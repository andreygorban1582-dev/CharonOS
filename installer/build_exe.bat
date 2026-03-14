@echo off
REM Build a standalone .exe for Windows using PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed --name "RickAssistant" --add-data "doom;doom" --add-data "gui/assets;gui/assets" main.py
echo Executable created in dist/RickAssistant.exe
pause
