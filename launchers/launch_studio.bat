@echo off
setlocal
cd /d "%~dp0.."

where pythonw >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start "" pythonw scripts/lib/cli.py studio --open %*
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start "" python scripts/lib/cli.py studio --open %*
    exit /b 0
)

echo [ERROR] Python >=3.10 was not found in your PATH.
echo Please install Python from https://www.python.org or the Microsoft Store.
pause
exit /b 1
