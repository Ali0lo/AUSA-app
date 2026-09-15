"""Recognise the uploaded project's create_all schema before introducing Alembic.

Only the exact original schema can be adopted automatically. Unknown tables may
coexist; differing application columns/keys stop the import without changing data.
"""
import json
from pathlib import Path
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

LEGACY_REVISION = "d4e5f6a7b8c9"


def adopt_legacy_schema(connection, config):
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if "alembic_version" in tables:
        if connection.execute(text("SELECT version_num FROM alembic_version")).first():
            return False
    expected = json.loads(Path(__file__).with_name("legacy_schema.json").read_text())
    if not tables.intersection(expected):
        return False  # fresh database: apply the complete migration history
    problems = []
    for name, shape in expected.items():
        if name not in tables:
            problems.append(f"missing table {name}")
            continue
        # PostgreSQL stores an unqualified SQLAlchemy FLOAT as DOUBLE PRECISION.
        # Reflection uses the latter spelling; REAL and numeric precisions stay distinct.
        columns = {c["name"]: {"type": str(c["type"].compile(dialect=connection.dialect)).replace("DOUBLE PRECISION", "FLOAT"),
                                "nullable": c["nullable"]} for c in inspector.get_columns(name)}
        if columns != shape["columns"]:
            problems.append(f"column definition differs in {name}")
        if inspector.get_pk_constraint(name)["constrained_columns"] != shape["pk"]:
            problems.append(f"primary key differs in {name}")
        unique = {tuple(c["column_names"]) for c in inspector.get_unique_constraints(name)}
        unique |= {tuple(i["column_names"]) for i in inspector.get_indexes(name) if i["unique"]}
        if any(tuple(key) not in unique for key in shape["unique"]):
            problems.append(f"missing unique key in {name}")
    if problems:
        raise RuntimeError("Unversioned database differs from the uploaded AUSA schema: " +
                           "; ".join(problems) + ". No automatic stamp was made. "
                           "Review this database's migration history before importing.")
    MigrationContext.configure(connection).stamp(ScriptDirectory.from_config(config), LEGACY_REVISION)
    return True
