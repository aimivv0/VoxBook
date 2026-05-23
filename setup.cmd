@echo off
chcp 65001 >nul
title Ebook2Audiobook - Setup
echo ================================================
echo   Ebook2Audiobook - One-click Setup
echo ================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ first:
    echo   https://www.python.org/downloads/
    echo   ^(Make sure to check "Add Python to PATH"^)
    echo.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 ( echo Setup failed & pause & exit /b 1 )

echo [2/3] Installing dependencies...
venv\Scripts\python -m pip install --upgrade pip --quiet
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 ( echo Setup failed & pause & exit /b 1 )

echo [3/3] Checking ffmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [WARNING] ffmpeg not found in PATH.
    echo   Please install ffmpeg from: https://ffmpeg.org/download.html
    echo   Or place ffmpeg.exe in: %~dp0ffmpeg\
    echo.
)

echo.
echo ================================================
echo   Setup complete! Run start.cmd to launch.
echo ================================================
pause