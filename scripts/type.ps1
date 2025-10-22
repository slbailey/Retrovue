# Type checking script
# Usage: pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/type.ps1

Write-Host "Running MyPy type checker..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv") {
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Virtual environment not found. Please create one first." -ForegroundColor Red
    exit 1
}

# Run mypy
mypy src/

if ($LASTEXITCODE -eq 0) {
    Write-Host "Type checking passed!" -ForegroundColor Green
} else {
    Write-Host "Type checking failed!" -ForegroundColor Red
    exit 1
}
