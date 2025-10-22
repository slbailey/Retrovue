# Linting script
# Usage: pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/lint.ps1

Write-Host "Running Ruff linter..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv") {
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Virtual environment not found. Please create one first." -ForegroundColor Red
    exit 1
}

# Run ruff check
ruff check src/ tests/

if ($LASTEXITCODE -eq 0) {
    Write-Host "Linting passed!" -ForegroundColor Green
} else {
    Write-Host "Linting failed!" -ForegroundColor Red
    exit 1
}
