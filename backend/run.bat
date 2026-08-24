@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if not exist "backend\requirements.txt" (
    echo ERROR: backend\requirements.txt was not found.
    goto :failure
)

where docker >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or is not available in PATH.
    goto :failure
)

docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Desktop is not running.
    goto :failure
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is unavailable.
    goto :failure
)

echo Starting PostgreSQL...
docker compose up -d postgres
if errorlevel 1 (
    echo ERROR: PostgreSQL could not be started.
    goto :failure
)

echo Waiting for PostgreSQL to become healthy...
set /a DB_ATTEMPTS=0

:wait_for_database
set "DB_STATUS="
for /f "delims=" %%S in ('docker inspect --format "{{.State.Health.Status}}" ausa_postgres 2^>nul') do set "DB_STATUS=%%S"

if /i "%DB_STATUS%"=="healthy" goto :database_ready

set /a DB_ATTEMPTS+=1
if %DB_ATTEMPTS% GEQ 30 (
    echo ERROR: PostgreSQL did not become healthy within 60 seconds.
    docker compose logs --tail=50 postgres
    goto :failure
)

timeout /t 2 /nobreak >nul
goto :wait_for_database

:database_ready
echo PostgreSQL is ready.

cd /d "%~dp0backend"

set "SYSTEM_PYTHON="

where py >nul 2>&1
if not errorlevel 1 set "SYSTEM_PYTHON=py -3"

if not defined SYSTEM_PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set "SYSTEM_PYTHON=python"
)

if not defined SYSTEM_PYTHON (
    echo ERROR: Python 3 is not installed or is not available in PATH.
    goto :failure
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating the Python virtual environment...
    %SYSTEM_PYTHON% -m venv ".venv"
    if errorlevel 1 (
        echo ERROR: The Python virtual environment could not be created.
        goto :failure
    )
)

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

echo Installing backend dependencies...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo ERROR: Backend dependencies could not be installed.
    goto :failure
)

echo Initializing and seeding the database...
"%VENV_PYTHON%" scripts\seed_db.py
if errorlevel 1 (
    echo ERROR: Database initialization or seeding failed.
    echo Check the PostgreSQL logs and backend database configuration.
    goto :failure
)

echo.
echo Starting the AUSA backend...
echo API: http://localhost:8000
echo Health check: http://localhost:8000/api/v1/health
echo API documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop the backend.
echo.

"%VENV_PYTHON%" -m uvicorn app.main:app --reload --port 8000

echo.
echo Backend server stopped.
endlocal
exit /b 0

:failure
echo.
pause
endlocal
exit /b 1