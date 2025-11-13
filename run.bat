@echo off
title Advanced RVC Inference
echo Starting Advanced RVC Inference...
echo.

set "ENV_DIR=%cd%\env"
set "MINICONDA_DIR=%UserProfile%\Miniconda3"

REM Check if environment exists
if not exist "%ENV_DIR%\python.exe" (
    echo Error: Environment not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Activate conda environment and run the application
call "%MINICONDA_DIR%\condabin\conda.bat" activate "%ENV_DIR%"
if errorlevel 1 (
    echo Error: Failed to activate conda environment.
    pause
    exit /b 1
)

REM Run the application
python app.py

REM Deactivate environment
call "%MINICONDA_DIR%\condabin\conda.bat" deactivate

pause