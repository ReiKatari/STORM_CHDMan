@echo off
set EXE_NAME=STORM CHDMan
set ICON=stormchdman.ico

echo [1/3] Cleaning old build files...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist "%EXE_NAME%.spec" del /q "%EXE_NAME%.spec"

echo [2/3] Building EXE with PyInstaller...
echo This may take a few minutes...
pyinstaller --onefile --windowed --name "%EXE_NAME%" --icon "%ICON%" --add-data "chdman.exe;." --add-data "notification.wav;." --add-data "stormchdman.ico;." --add-data "requirements.txt;." --collect-all requests --collect-all PyQt6 stormchdman.py

echo.
echo [3/3] Build complete! 
echo Check the 'dist' folder for "%EXE_NAME%.exe"
pause
