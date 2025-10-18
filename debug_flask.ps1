# KitchenRadio Flask Debug Setup (PowerShell)

Write-Host "🎵 KitchenRadio Flask Debug Setup" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray

# Set environment variables for debugging
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:DEBUG = "true"
$env:LOG_LEVEL = "DEBUG"

# Add project paths to Python path
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$projectRoot;$projectRoot\src;$projectRoot\web;$env:PYTHONPATH"

Write-Host "🔧 Environment configured for debugging:" -ForegroundColor Green
Write-Host "   FLASK_ENV = development" -ForegroundColor Gray
Write-Host "   FLASK_DEBUG = 1" -ForegroundColor Gray  
Write-Host "   DEBUG = true" -ForegroundColor Gray
Write-Host "   LOG_LEVEL = DEBUG" -ForegroundColor Gray
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "🐍 Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "⚠️  No virtual environment found. Consider creating one:" -ForegroundColor Yellow
    Write-Host "   python -m venv venv" -ForegroundColor Gray
    Write-Host "   venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 Starting Flask in debug mode..." -ForegroundColor Cyan
Write-Host "📍 Web interface: http://localhost:5000" -ForegroundColor Green
Write-Host "🔍 Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Run the debug script
python debug_flask.py
