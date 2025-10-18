@echo off
REM KitchenRadio Flask Debug Setup (Batch)

echo 🎵 KitchenRadio Flask Debug Setup
echo ========================================

REM Set environment variables for debugging
set FLASK_ENV=development
set FLASK_DEBUG=1
set DEBUG=true
set LOG_LEVEL=DEBUG

REM Add project paths to Python path
set PROJECT_ROOT=%~dp0
set PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%src;%PROJECT_ROOT%web;%PYTHONPATH%

echo 🔧 Environment configured for debugging:
echo    FLASK_ENV = development
echo    FLASK_DEBUG = 1  
echo    DEBUG = true
echo    LOG_LEVEL = DEBUG
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🐍 Activating virtual environment...
    call "venv\Scripts\activate.bat"
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  No virtual environment found. Consider creating one:
    echo    python -m venv venv
    echo    venv\Scripts\activate.bat
    echo    pip install -r requirements.txt
)

echo.
echo 🚀 Starting Flask in debug mode...
echo 📍 Web interface: http://localhost:5000
echo 🔍 Press Ctrl+C to stop
echo.

REM Run the debug script
python debug_flask.py

pause
