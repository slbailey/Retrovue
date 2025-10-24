# Retrovue Virtual Environment Activation Script
# Run this script to activate the virtual environment

Write-Host "Activating Retrovue virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"
Write-Host "Virtual environment activated! You can now run:" -ForegroundColor Yellow
Write-Host "  retrovue --help" -ForegroundColor Cyan
Write-Host "  python run_server.py" -ForegroundColor Cyan

