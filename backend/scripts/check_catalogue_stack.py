"""Exercise the production frontend against real HTTP APIs and a disposable catalogue.

First run npm ci and npm run build in frontend (default API URL localhost:8000/api/v1).
Then, from backend: python -m scripts.check_catalogue_stack
Uses ports 8000 and 3100, a temporary SQLite database, and an installed Playwright
Chromium (or PLAYWRIGHT_EXECUTABLE_PATH). Never connects to the application database.
PostgreSQL migrations are checked separately by test_catalogue_postgres.py.
"""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"


async def seed():
    if os.environ.get("AUSA_STACK_TEST_FIXTURE") != "1" or not os.environ.get("DATABASE_URL", "").startswith("sqlite+aiosqlite:///"):
        raise RuntimeError("Seeding is allowed only inside the disposable stack test.")
    from app.core.database import Base, engine
    from app.models.qualifications import ProgramRequirement
    from app.models.dp_catalogue import DPCatalogueEntry
    from scripts.bootstrap_catalogue import load_catalogue
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=[ProgramRequirement.__table__, DPCatalogueEntry.__table__])
    await load_catalogue()


def ready(url, process):
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server exited before becoming ready: {url}")
        try:
            with opener.open(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            pass
        time.sleep(0.2)
    raise TimeoutError(f"Server did not become ready: {url}")


def main():
    if not (FRONTEND / ".next" / "BUILD_ID").exists():
        raise RuntimeError("Run npm run build in frontend before this production stack check.")
    processes = []
    with tempfile.TemporaryDirectory(prefix="ausa-stack-check-") as directory:
        fixture = Path(directory)
        env = {**os.environ, "DATABASE_URL": "sqlite+aiosqlite:///" + (fixture / "catalogue.sqlite").as_posix(),
               "AUSA_STACK_TEST_FIXTURE": "1", "DEBUG": "false", "ENVIRONMENT": "test", "PYTHONUTF8": "1",
               "BACKEND_CORS_ORIGINS": json.dumps(["http://127.0.0.1:3100"]),
               "NEXTAUTH_URL": "http://127.0.0.1:3100", "NEXTAUTH_SECRET": "disposable-stack-check-secret"}
        with (fixture / "servers.log").open("w+") as log:
            try:
                subprocess.run([sys.executable, "-m", "scripts.check_catalogue_stack", "--seed"], cwd=BACKEND, env=env, check=True, timeout=60, stdout=log, stderr=log)
                backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=BACKEND, env=env, stdout=log, stderr=log)
                processes.append(backend)
                ready("http://127.0.0.1:8000/api/v1/health", backend)
                frontend = subprocess.Popen(["node", str(FRONTEND / "node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", "3100"], cwd=FRONTEND, env=env, stdout=log, stderr=log)
                processes.append(frontend)
                ready("http://127.0.0.1:3100", frontend)
                subprocess.run(["node", "scripts/check_catalogue_stack.mjs"], cwd=FRONTEND, env=env, check=True, timeout=60)
            except Exception:
                log.flush()
                log.seek(0)
                print(log.read()[-12000:])
                raise
            finally:
                for process in reversed(processes):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    if sys.argv[1:] == ["--seed"]:
        asyncio.run(seed())
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit(__doc__)
