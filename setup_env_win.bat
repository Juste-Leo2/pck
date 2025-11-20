@echo off
setlocal

:: =============================================================================
::      DEVELOPMENT ENVIRONMENT INITIALIZATION
:: =============================================================================
echo.

REM --- Step 1: Checking prerequisites ---
echo [1/5] Checking prerequisites...
if not exist "requirements.txt" (
    echo FAILURE: The 'requirements.txt' file could not be found.
    goto:error
)
echo    [OK] requirements.txt file found.

REM --- Step 2: Checking for and installing 'uv' ---
echo [2/5] Checking for and installing 'uv'...

REM Check if the 'uv' command already exists
where uv > nul 2>&1
if %errorlevel% == 0 (
    echo    [OK] uv is already installed.
) else (
    echo    uv not found, starting installation...
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo FAILURE: Could not install uv. Check your internet connection or PowerShell permissions.
        goto:error
    )
    
    REM Check if the installation successfully added uv to the PATH
    where uv > nul 2>&1
    if %errorlevel% neq 0 (
        echo FAILURE: uv was installed but is not accessible. You might need to restart your terminal.
        goto:error
    )
    echo    [OK] uv installed successfully.
)


REM --- Step 3: Creating the Python environment ---
echo [3/5] Creating the Python environment (python 3.11)...
uv venv -p 3.11
if %errorlevel% neq 0 (
    echo FAILURE: Could not create the Python environment. Make sure Python 3.11 is accessible.
    goto:error
)
echo    [OK] Python environment created in the .venv folder.

REM --- Step 4: Activating and installing dependencies ---
echo [4/5] Installing Python dependencies...

REM Check that the activation script exists
if not exist ".\.venv\Scripts\activate.bat" (
    echo FAILURE: The environment activation script was not found.
    goto:error
)

call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo FAILURE: Could not activate the virtual environment.
    goto:error
)

uv pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo FAILURE: Could not install dependencies from requirements.txt.
    call .\.venv\Scripts\deactivate.bat
    goto:error
)

echo    [OK] Python dependencies installed.

REM --- Step 5: Cleanup and finalization ---
echo [5/5] Finalizing the installation...
call .\.venv\Scripts\deactivate.bat
echo    [OK] Environment deactivated.
goto:success


:success
echo.
echo ==========================================================
echo      ENVIRONMENT CONFIGURED SUCCESSFULLY!
echo ==========================================================
echo.
echo To activate the environment, run the command:
echo   call .\.venv\Scripts\activate.bat
echo.
goto:end


:error
echo.
echo ==========================================================
echo      ERROR: THE INSTALLATION FAILED.
echo ==========================================================
echo Please check the error messages above.
echo.
set "EXIT_CODE=1"
goto:end


:end
endlocal
echo Press any key to exit...
pause > nul
exit /b %EXIT_CODE%