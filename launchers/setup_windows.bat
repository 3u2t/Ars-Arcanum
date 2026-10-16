@echo off
setlocal
cd /d "%~dp0.."
echo ============================================================
echo   Ars Arcanum -- Automated Setup for Windows Writing System
echo ============================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\setup_arcanum.ps1" %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Installation failed or was cancelled.
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo [OK] Setup completed successfully.
pause
exit /b 0
