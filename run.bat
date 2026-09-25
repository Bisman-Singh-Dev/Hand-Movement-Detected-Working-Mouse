@echo off
title Hand Movement Detected - Virtual Working Mouse Pro
color 0B

echo ====================================================================
echo   🖐️  HAND MOVEMENT DETECTED - VIRTUAL WORKING MOUSE PRO
echo ====================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    py -3.11 --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python is not installed or not in PATH.
        echo Please install Python 3.10 or 3.11 from python.org
        pause
        exit /b 1
    )
    set PY_CMD=py -3.11
) else (
    set PY_CMD=python
)

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [SETUP] First-time setup detected. Initializing environment...
    %PY_CMD% -m venv venv
    echo [SETUP] Installing required dependencies...
    .\venv\Scripts\python.exe -m pip install --upgrade pip
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [INFO] Launching Virtual Hand Mouse...
echo [INFO] Press 'Q' or ESC in the camera window to exit.
echo [INFO] Press 'P' to pause/resume tracking.
echo.

.\venv\Scripts\python.exe main.py %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] Application closed with exit code %ERRORLEVEL%.
    pause
)
