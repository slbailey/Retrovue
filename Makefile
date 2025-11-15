# Retrovue Development Makefile
# Web-first development with FastAPI

.PHONY: help dev dev-all install test test-contracts test-enricher-contracts lint clean

# Default target
help:
	@echo "Retrovue Development Commands:"
	@echo "  dev        - Start FastAPI development server"
	@echo "  dev-all    - Start API + any frontend dev servers"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run tests"
	@echo "  test-contracts - Run contract tests only"
	@echo "  test-enricher-contracts - Run enricher contract tests only"
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
# PYTHON can be passed from parent Makefile to use venv
install:
	$(PYTHON) -m pip install -q -r requirements.txt
	@if [ -f requirements-admin.txt ]; then $(PYTHON) -m pip install -q -r requirements-admin.txt; fi

# Run tests
# PYTHON can be passed from parent Makefile to use venv
# Prefer Python 3.11 if available
PYTHON311 := $(shell command -v python3.11 2>/dev/null)
VENV_PYTHON := $(shell if [ -f ../.venv/bin/python ]; then echo ../.venv/bin/python; elif [ -f .venv/bin/python ]; then echo .venv/bin/python; fi)
PYTHON ?= $(shell if [ -n "$(PYTHON311)" ]; then echo $(PYTHON311); elif [ -n "$(VENV_PYTHON)" ]; then echo $(VENV_PYTHON); elif command -v python >/dev/null 2>&1; then echo python; else echo python3; fi)
test:
	$(PYTHON) -m pytest -v

# Run contract tests only
test-contracts:
	$(PYTHON) -m pytest tests/contracts -v

# Run enricher contract tests only
test-enricher-contracts:
	$(PYTHON) -m pytest tests/contracts/ -k "enricher" -v

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
