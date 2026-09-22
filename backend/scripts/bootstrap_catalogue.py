"""Migrate and load the shipped catalogue without making an LLM request.

Run from backend: python -m scripts.bootstrap_catalogue
Optional research CSVs and RAG embeddings are loaded explicitly by their own scripts.
"""
import asyncio
from pathlib import Path
try:
    from alembic import command
    from alembic.config import Config
except ImportError:
    import sys, importlib
    _cwd = sys.path.pop(0) if sys.path and sys.path[0] in ("", ".") else None
    try:
        command = importlib.import_module("alembic.command")
        Config = importlib.import_module("alembic.config").Config
    finally:
        if _cwd is not None:
            sys.path.insert(0, _cwd)
from app.core.database import AsyncSessionLocal, engine
from scripts.load_program_requirements import CATALOGUE_FILES, DEFAULT_FILE, KEY_FIELDS, read_rows, load_program_requirements
from scripts.collect_dp_catalogue import DEFAULT_DESTINATION, RESOURCES
from scripts.load_dp_catalogue import load_csv, rows_from_csv
from scripts.adopt_legacy_schema import adopt_legacy_schema


def validate_catalogue(paths=CATALOGUE_FILES):
    keys = set()
    for path in paths:
        for row in read_rows(path):
            key = tuple(row[f] for f in KEY_FIELDS)
            if key in keys:
                raise ValueError(f"Duplicate catalogue identity across files: {key}")
            keys.add(key)
    return len(keys)


async def load_catalogue(paths=CATALOGUE_FILES, dp_files=None):
    validate_catalogue(paths)
    dp_files = dp_files if dp_files is not None else [(DEFAULT_DESTINATION / name, url) for name, url in RESOURCES.items()]
    for path, url in dp_files:
        rows_from_csv(path, url)
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                results = [await load_program_requirements(session, path, commit=False) for path in paths]
                for path, url in dp_files:
                    results.append({"dp_file": path.name, "inserted": await load_csv(session, path, url, commit=False)})
        return results
    finally:
        await engine.dispose()


def main():
    count = validate_catalogue()
    for name, url in RESOURCES.items():
        rows_from_csv(DEFAULT_DESTINATION / name, url)
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    async def prepare():
        try:
            async with engine.begin() as connection:
                adopted = await connection.run_sync(adopt_legacy_schema, config)
                if adopted:
                    print("Recognised the original create_all schema; adopted its existing migration baseline.")
        finally:
            await engine.dispose()
    asyncio.run(prepare())
    command.upgrade(config, "head")
    summaries = asyncio.run(load_catalogue())
    print(f"Catalogue ready: {count} rows. Imports: {summaries}")
    print("Human review is retained only for unchanged facts. RAG seeding is a separate optional command.")


if __name__ == "__main__":
    main()
