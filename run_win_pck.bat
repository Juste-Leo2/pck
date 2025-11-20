@echo off
setlocal

REM Check if the virtual environment folder exists.
REM If it doesn't exist, the setup was probably not run.
set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
if not exist ".venv" (
    echo Error: The Python environment was not found.
    echo Please run 'setup.bat' first to complete the installation.
    pause
    exit /b 1
)

echo Activating the Python environment...
call .\.venv\Scripts\activate.bat

echo Launching...
"%UV_EXE%" run main.py

echo Closing...
call .\.venv\Scripts\deactivate.bat
pause