@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if not exist "package.json" (
    echo ERROR: package.json was not found beside run.bat.
    goto :failure
)

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or is not available in PATH.
    goto :failure
)

set "NODE_VERSION_CODE="
for /f %%V in ('node -p "Number(process.versions.node.split('.')[0])*1000+Number(process.versions.node.split('.')[1])"') do set "NODE_VERSION_CODE=%%V"

if not defined NODE_VERSION_CODE (
    echo ERROR: The installed Node.js version could not be read.
    goto :failure
)

if %NODE_VERSION_CODE% LSS 20019 (
    echo ERROR: Node.js 20.19 or later is required.
    node --version
    goto :failure
)

call npm ci
if errorlevel 1 (
    echo ERROR: Frontend dependencies could not be installed.
    goto :failure
)

if not exist ".env.local" (
    copy /Y ".env.example" ".env.local" >nul
    if errorlevel 1 (
        echo ERROR: .env.local could not be created.
        goto :failure
    )
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$path='.env.local'; $placeholder='NEXTAUTH_SECRET=replace-with-a-long-random-secret'; $text=[IO.File]::ReadAllText($path); if ($text.Contains($placeholder)) { $bytes=New-Object byte[] 32; $rng=[Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($bytes); $rng.Dispose(); $secret=[Convert]::ToBase64String($bytes); $text=$text.Replace($placeholder,'NEXTAUTH_SECRET='+$secret); [IO.File]::WriteAllText($path,$text) }"
if errorlevel 1 (
    echo ERROR: NEXTAUTH_SECRET could not be configured.
    goto :failure
)

if exist ".next" rmdir /S /Q ".next"

echo.
echo Starting AUSA frontend at http://localhost:3000
echo Press Ctrl+C to stop it.
echo.

call npm run dev

endlocal
exit /b 0

:failure
echo.
pause
endlocal
exit /b 1
