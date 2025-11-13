@echo off
title Realtime Voice Cloning - Tkinter GUI
echo ========================================
echo   Realtime Voice Cloning - Tkinter GUI
echo ========================================
echo.
echo Starting application...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Run the tkinter application
python realtime_tkinter.py

REM Check if the application exited with an error
if errorlevel 1 (
    echo.
    echo ========================================
    echo Application exited with an error
    echo ========================================
    echo.
    pause
)