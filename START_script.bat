@echo off

rem Check if Python is installed
python --version 2>NUL
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again: https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    echo Check ADD TO PATH during installation!
    pause
    exit /b 1
)

rem Check if teachposgenerator.py exists
if not exist teachposgeneratorV3.py (
    echo The script teachposgenerator.py is missing. Please make sure it is in the same directory as this batch file.
    pause
    exit /b 1
)

rem Python is installed, pandas is installed, and the script exists, start teachposgenerator.py
python teachposgeneratorV3.py

rem Pause to keep the command window open (optional)
pause
