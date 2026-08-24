@echo off
setlocal EnableExtensions

set "AUSA_DB_HOST=127.0.0.1"
set "AUSA_DB_PORT=5432"
set "AUSA_DB_NAME=ausa_db"
set "AUSA_DB_USER=ausa_user"
set "AUSA_DB_PASSWORD=ausa_password"
set "AUSA_ADMIN_USER=postgres"

set "AUSA_SCRIPT_DIR=%~dp0"

if exist "%AUSA_SCRIPT_DIR%backend\requirements.txt" (
    set "AUSA_BACKEND_DIR=%AUSA_SCRIPT_DIR%backend"
) else if exist "%AUSA_SCRIPT_DIR%requirements.txt" (
    set "AUSA_BACKEND_DIR=%AUSA_SCRIPT_DIR%"
) else (
    echo ERROR: The backend folder could not be found.
    echo Place run_backend.bat beside the backend folder or inside it.
    goto :failure
)

cd /d "%AUSA_BACKEND_DIR%"

set "AUSA_PSQL="

for /f "delims=" %%P in ('where psql.exe 2^>nul') do if not defined AUSA_PSQL set "AUSA_PSQL=%%P"

if not defined AUSA_PSQL (
    for /d %%D in ("C:\Program Files\PostgreSQL\*") do if exist "%%~fD\bin\psql.exe" set "AUSA_PSQL=%%~fD\bin\psql.exe"
)

if not defined AUSA_PSQL (
    echo ERROR: PostgreSQL command-line tools were not found.
    echo Ensure PostgreSQL is installed with Command Line Tools.
    goto :failure
)

for %%P in ("%AUSA_PSQL%") do set "AUSA_PGBIN=%%~dpP"

if not exist "%AUSA_PGBIN%pg_isready.exe" (
    echo ERROR: pg_isready.exe was not found in %AUSA_PGBIN%
    goto :failure
)

echo Checking PostgreSQL at %AUSA_DB_HOST%:%AUSA_DB_PORT%...
"%AUSA_PGBIN%pg_isready.exe" -h "%AUSA_DB_HOST%" -p "%AUSA_DB_PORT%" >nul 2>&1

if errorlevel 1 (
    echo ERROR: PostgreSQL is installed but is not accepting connections.
    echo Open Windows Services, start the PostgreSQL service, and run this file again.
    goto :failure
)

call :check_database

if defined AUSA_DATABASE_READY goto :database_ready

call :initialize_database
if errorlevel 1 goto :failure

call :check_database

if not defined AUSA_DATABASE_READY (
    echo ERROR: The AUSA database was created but could not be verified.
    goto :failure
)

:database_ready
echo PostgreSQL database and pgvector are ready.

call :select_python

if errorlevel 1 (
    echo ERROR: No working CPython 3.10 through 3.13 installation was found.
    echo The Windows Python Launcher may contain a stale or incomplete Python registration.
    echo Run "py -0p" to inspect registered interpreters.
    echo Recommended download: https://www.python.org/downloads/windows/
    goto :failure
)

if defined AUSA_VENV_PYTHON goto :python_environment_ready

if not exist ".venv" goto :create_python_environment

set "AUSA_OLD_VENV=.venv_incompatible_%RANDOM%_%RANDOM%"
move ".venv" "%AUSA_OLD_VENV%" >nul

if errorlevel 1 (
    echo ERROR: The existing .venv is broken or incompatible and could not be moved.
    echo Close programs using it, rename the .venv folder, and run this file again.
    goto :failure
)

echo Moved the incompatible environment to %AUSA_OLD_VENV%.

:create_python_environment
echo Creating the Python virtual environment with %AUSA_SYSTEM_PYTHON%...
%AUSA_SYSTEM_PYTHON% -m venv ".venv"

if errorlevel 1 (
    echo ERROR: The Python virtual environment could not be created.
    goto :failure
)

set "AUSA_VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

:python_environment_ready
echo Using Python:
"%AUSA_VENV_PYTHON%" --version

if errorlevel 1 (
    echo ERROR: The selected virtual-environment interpreter cannot run.
    goto :failure
)

echo Installing backend dependencies...
"%AUSA_VENV_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt

if errorlevel 1 (
    echo ERROR: Backend dependencies could not be installed.
    goto :failure
)

if exist ".env" goto :environment_ready

set "AUSA_SECRET_FILE=%TEMP%\ausa_secret_%RANDOM%_%RANDOM%.txt"
"%AUSA_VENV_PYTHON%" -c "import secrets; print(secrets.token_hex(32))" > "%AUSA_SECRET_FILE%"

if errorlevel 1 (
    echo ERROR: A backend secret could not be generated.
    if exist "%AUSA_SECRET_FILE%" del /Q "%AUSA_SECRET_FILE%"
    goto :failure
)

set /p "AUSA_SECRET="<"%AUSA_SECRET_FILE%"
del /Q "%AUSA_SECRET_FILE%"

> ".env" echo ENVIRONMENT=development
>> ".env" echo DEBUG=true
>> ".env" echo SECRET_KEY=%AUSA_SECRET%
>> ".env" echo POSTGRES_USER=%AUSA_DB_USER%
>> ".env" echo POSTGRES_PASSWORD=%AUSA_DB_PASSWORD%
>> ".env" echo POSTGRES_HOST=%AUSA_DB_HOST%
>> ".env" echo POSTGRES_PORT=%AUSA_DB_PORT%
>> ".env" echo POSTGRES_DB=%AUSA_DB_NAME%
>> ".env" echo DATABASE_URL=postgresql+asyncpg://%AUSA_DB_USER%:%AUSA_DB_PASSWORD%@%AUSA_DB_HOST%:%AUSA_DB_PORT%/%AUSA_DB_NAME%

echo Created backend\.env with local development settings.

:environment_ready

echo Initializing and seeding the database...
"%AUSA_VENV_PYTHON%" -m scripts.seed_db

if errorlevel 1 (
    echo ERROR: Database initialization or seeding failed.
    echo Check the error above and the values in backend\.env.
    goto :failure
)

echo.
echo Starting the AUSA backend...
echo API: http://localhost:8000
echo Health: http://localhost:8000/api/v1/health
echo Documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop the backend.
echo.

"%AUSA_VENV_PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

set "AUSA_SERVER_EXIT=%ERRORLEVEL%"

if not "%AUSA_SERVER_EXIT%"=="0" (
    echo.
    echo ERROR: The backend server exited with code %AUSA_SERVER_EXIT%.
    goto :failure
)

endlocal
exit /b 0

:select_python
set "AUSA_SYSTEM_PYTHON="
set "AUSA_VENV_PYTHON="

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
        exit /b 0
    )
)

where py.exe >nul 2>&1
if not errorlevel 1 (
    py -3.12 -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_SYSTEM_PYTHON=py -3.12"
        exit /b 0
    )

    py -3.11 -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_SYSTEM_PYTHON=py -3.11"
        exit /b 0
    )

    py -3.13 -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_SYSTEM_PYTHON=py -3.13"
        exit /b 0
    )

    py -3.10 -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_SYSTEM_PYTHON=py -3.10"
        exit /b 0
    )
)

where python.exe >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_SYSTEM_PYTHON=python"
        exit /b 0
    )
)

where python3.exe >nul 2>&1
if not errorlevel 1 (
    python3 -c "import sys; raise SystemExit(not (sys.version_info[:2].__ge__((3, 10)) and sys.version_info[:2].__lt__((3, 14))))" >nul 2>&1
    if not errorlevel 1 (
        set "AUSA_SYSTEM_PYTHON=python3"
        exit /b 0
    )
)

exit /b 1

:initialize_database
echo.
echo First-time PostgreSQL setup is required.
echo Enter the password for the PostgreSQL administrator "%AUSA_ADMIN_USER%" when prompted.
echo.

set "AUSA_SQL_FILE=%TEMP%\ausa_setup_%RANDOM%_%RANDOM%.sql"

> "%AUSA_SQL_FILE%" echo SELECT 'CREATE ROLE %AUSA_DB_USER% WITH LOGIN PASSWORD ''%AUSA_DB_PASSWORD%''' WHERE NOT EXISTS ^(SELECT 1 FROM pg_roles WHERE rolname = '%AUSA_DB_USER%'^)
>> "%AUSA_SQL_FILE%" echo \gexec
>> "%AUSA_SQL_FILE%" echo ALTER ROLE %AUSA_DB_USER% WITH LOGIN PASSWORD '%AUSA_DB_PASSWORD%';
>> "%AUSA_SQL_FILE%" echo SELECT 'CREATE DATABASE %AUSA_DB_NAME% OWNER %AUSA_DB_USER%' WHERE NOT EXISTS ^(SELECT 1 FROM pg_database WHERE datname = '%AUSA_DB_NAME%'^)
>> "%AUSA_SQL_FILE%" echo \gexec
>> "%AUSA_SQL_FILE%" echo ALTER DATABASE %AUSA_DB_NAME% OWNER TO %AUSA_DB_USER%;
>> "%AUSA_SQL_FILE%" echo \connect %AUSA_DB_NAME%
>> "%AUSA_SQL_FILE%" echo CREATE EXTENSION IF NOT EXISTS vector;
>> "%AUSA_SQL_FILE%" echo GRANT ALL ON SCHEMA public TO %AUSA_DB_USER%;

"%AUSA_PSQL%" -h "%AUSA_DB_HOST%" -p "%AUSA_DB_PORT%" -U "%AUSA_ADMIN_USER%" -d postgres -W -v ON_ERROR_STOP=1 -f "%AUSA_SQL_FILE%"
set "AUSA_SETUP_EXIT=%ERRORLEVEL%"

if exist "%AUSA_SQL_FILE%" del /Q "%AUSA_SQL_FILE%"

if not "%AUSA_SETUP_EXIT%"=="0" (
    echo.
    echo ERROR: PostgreSQL initialization failed.
    echo If PostgreSQL reported that extension "vector" is unavailable, pgvector is not installed in PostgreSQL.
    echo Official instructions: https://github.com/pgvector/pgvector#installation
    exit /b 1
)

exit /b 0

:check_database
set "AUSA_DATABASE_READY="
set "AUSA_DB_CHECK_FILE=%TEMP%\ausa_db_check_%RANDOM%_%RANDOM%.txt"
set "PGPASSWORD=%AUSA_DB_PASSWORD%"

"%AUSA_PSQL%" -h "%AUSA_DB_HOST%" -p "%AUSA_DB_PORT%" -U "%AUSA_DB_USER%" -d "%AUSA_DB_NAME%" -tA -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" > "%AUSA_DB_CHECK_FILE%" 2>nul
set "AUSA_DB_CHECK_EXIT=%ERRORLEVEL%"
set "PGPASSWORD="

if "%AUSA_DB_CHECK_EXIT%"=="0" (
    findstr /x /c:"1" "%AUSA_DB_CHECK_FILE%" >nul 2>&1
    if not errorlevel 1 set "AUSA_DATABASE_READY=1"
)

if exist "%AUSA_DB_CHECK_FILE%" del /Q "%AUSA_DB_CHECK_FILE%"
exit /b 0

:failure
echo.
pause
endlocal
exit /b 1
