@echo off
echo ========================================
echo   Python Adventure Game - Build
echo ========================================
echo.

echo [1/3] Installing dependencies...
pip install pyinstaller -q
pip install -r requirements.txt -q

echo.
echo [2/3] Building...
pyinstaller --clean pyinstaller.spec

echo.
echo [3/3] Build complete!
echo.
echo Output: dist\game\
echo Run:   dist\game\game.exe
echo.
echo Deployment: copy the entire dist\game\ folder to the target machine.
echo Database will be auto-created in data\app.db on first run.
pause
