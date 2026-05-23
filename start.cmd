@echo off
chcp 65001 >nul
title Ebook2Audiobook
echo ================================================
echo   Ebook2Audiobook - Starting...
echo   Browser will open at http://127.0.0.1:7860
echo   Keep this window open while converting
echo ================================================
echo.
"%~dp0venv\Scripts\python.exe" "%~dp0app.py"
pause