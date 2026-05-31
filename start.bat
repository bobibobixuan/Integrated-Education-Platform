@echo off
setlocal

echo ========================================
echo   Integrated-Education-Platform Server v2.2.12
echo ========================================

cd /d "%~dp0"
set "ROOT_DIR=%CD%"
set "PORT=80"
set "PYTHONPATH=%ROOT_DIR%"

echo Starting server...

call :try_python "%ROOT_DIR%\backend\.venv\Scripts\python.exe"
if %ERRORLEVEL% EQU 0 goto :end

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

"%PYEXE%" -c "import backend.app.main" >nul 2>&1
if errorlevel 1 exit /b 1

echo Using Python: %PYEXE%
"%PYEXE%" -m backend.app.main --port %PORT%
exit /b %ERRORLEVEL%

:end
pause
