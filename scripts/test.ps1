# Test script
# Usage: pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1

Write-Host "Running tests..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv") {
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Virtual environment not found. Please create one first." -ForegroundColor Red
    exit 1
}

# Run pytest
pytest tests/ -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
    exit 1
}
