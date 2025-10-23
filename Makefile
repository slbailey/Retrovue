# Retrovue Development Makefile
# Web-first development with FastAPI

.PHONY: help dev dev-all install test lint clean

# Default target
help:
	@echo "Retrovue Development Commands:"
	@echo "  dev        - Start FastAPI development server"
	@echo "  dev-all    - Start API + any frontend dev servers"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  clean      - Clean build artifacts"

# Development server
dev:
	@echo "Starting Retrovue FastAPI development server..."
	uvicorn retrovue.api.main:app --reload --port 8000 --host 127.0.0.1

# Development with all services (if frontend exists)
dev-all: dev
	@echo "Starting all development services..."
	@echo "API: http://localhost:8000"
	@echo "Note: No separate frontend dev server configured"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-admin.txt

# Run tests
test:
	pytest -v

# Run linting
lint:
	ruff check src/ tests/
	mypy src/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
