@echo off
REM ============================================
REM AI Newsletter Bot - Scheduled Scout Script
REM ============================================
REM Run this script automatically to fetch articles overnight.
REM Set up Windows Task Scheduler to run at 11 PM daily.

cd /d "%~dp0"

echo.
echo ============================================
echo AI Newsletter Bot - Overnight Scout
echo %date% %time%
echo ============================================
echo.

REM Activate virtual environment and run scout
call venv\Scripts\activate.bat
python src/cli.py scout

echo.
echo Scout complete! Articles ready for review.
echo ============================================
