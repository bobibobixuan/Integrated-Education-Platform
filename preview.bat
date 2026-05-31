@echo off
setlocal

echo ========================================
echo   Preview Mode
echo ========================================

cd /d "%~dp0"
set "ROOT_DIR=%CD%"
set "PORT=80"
set "PYTHONPATH=%ROOT_DIR%"

echo.
echo [1/3] Switching to preview/dev...
git checkout preview/dev 2>nul
if errorlevel 1 (
    echo Failed to switch branch
    pause
    exit /b 1
)

echo [2/3] Building frontend...
call npm --prefix frontend run build
if errorlevel 1 (
    echo Build failed
    pause
    exit /b 1
)

echo [3/3] Starting server...

call :try_python "%ROOT_DIR%\backend\.venv\Scripts\python.exe"
if errorlevel 0 goto :end

echo.
echo [ERROR] Virtual environment not found at backend\.venv
echo         Run: uv sync --directory backend
echo.
pause
exit /b 1

:try_python
set "PYEXE=%~1"
if not exist "%PYEXE%" exit /b 1

"%PYEXE%" --version >nul 2>&1
if errorlevel 1 exit /b 1

echo ========================================
echo   Preview: http://localhost
echo   Normal:  start.bat
echo ========================================
"%PYEXE%" -m backend.app.main --port %PORT%
exit /b %ERRORLEVEL%

:end
pause
