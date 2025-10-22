# Development server script
# Usage: pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/dev.ps1

Write-Host "Starting Retrovue development server..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv") {
  Write-Host "Activating virtual environment..." -ForegroundColor Yellow
  & "venv\Scripts\Activate.ps1"
}
else {
  Write-Host "Virtual environment not found. Please create one first." -ForegroundColor Red
  exit 1
}

# Install dependencies if needed
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e .

# Start the development server
Write-Host "Starting FastAPI server with uvicorn..." -ForegroundColor Green
uvicorn src.retrovue.api:app --reload --host 0.0.0.0 --port 8000
