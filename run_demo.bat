@echo off
setlocal EnableExtensions

rem One command to run AUSA for a demo: the real product, the real curated
rem catalogue, no PostgreSQL and no pgvector to install first.
rem
rem What this does NOT cover: accounts, sign-in, saved applications and document
rem search all need PostgreSQL. Run backend\run_backend.bat for those.
rem
rem The chatbot additionally needs OPENAI_API_KEY in backend\.env. Without it the
rem chat endpoint reports that search is unavailable; the rest of the product works.

set "DATABASE_URL=sqlite+aiosqlite:///./demo.db"

echo Starting the AUSA backend on SQLite (demo mode).
echo Start the frontend separately with frontend\run.bat, then open http://localhost:3000
echo.

call "%~dp0backend\run_backend.bat"

endlocal
