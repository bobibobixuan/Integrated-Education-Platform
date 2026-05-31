@echo off
setlocal

echo ========================================
echo   Dev Mode - Hot Reload  (http://localhost)
echo ========================================

cd /d "%~dp0"
set "ROOT_DIR=%CD%"
set "PYTHONPATH=%ROOT_DIR%"

echo.
echo Starting backend on port 8000...
start /B "" "%ROOT_DIR%\backend\.venv\Scripts\python.exe" -m backend.app.main --port 8000

echo Starting frontend dev server...
echo ========================================
call npm --prefix frontend run dev
