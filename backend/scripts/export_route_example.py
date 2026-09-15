"""Generate the explicitly labelled discovery example using the shipped catalogue."""
import argparse
import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from app.models.qualifications import ProgramRequirement
from app.models.dp_catalogue import DPCatalogueEntry
from app.api.v1.routes import AssessRoutesPayload, assess
from scripts.bootstrap_catalogue import CATALOGUE_FILES
from scripts.collect_dp_catalogue import DEFAULT_DESTINATION, RESOURCES
from scripts.load_dp_catalogue import load_csv
from scripts.load_program_requirements import load_program_requirements

async def export(path):
    engine = create_async_engine('sqlite+aiosqlite://')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, tables=[ProgramRequirement.__table__, DPCatalogueEntry.__table__])
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            for source in CATALOGUE_FILES:
                await load_program_requirements(session, source)
            for name, url in RESOURCES.items():
                await load_csv(session, DEFAULT_DESTINATION/name, url)
            result = await assess(AssessRoutesPayload(level_sought='bachelor', qualification_held='attestat'), session)
            path.write_text(json.dumps(result.model_dump(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    finally:
        await engine.dispose()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'frontend/src/lib/baseline-routes.json')
    asyncio.run(export(parser.parse_args().output))
