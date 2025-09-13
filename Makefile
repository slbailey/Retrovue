# Retrovue Makefile
# Database management and development tasks

# Configuration
DB_PATH ?= data/retrovue.db
SCHEMA ?= sql/retrovue_schema_v1.2.sql
SCRIPTS_DIR = scripts

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m # No Color

# Default target
.PHONY: help
help: ## Show this help message
	@echo "Retrovue Development Makefile"
	@echo "============================="
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Configuration:"
	@echo "  DB_PATH = $(DB_PATH)"
	@echo "  SCHEMA  = $(SCHEMA)"

# Database targets
.PHONY: db-create
db-create: ## Create database if it doesn't exist
	@echo "$(GREEN)[INFO]$(NC) Creating database if it doesn't exist..."
	@if [ ! -f "$(DB_PATH)" ]; then \
		mkdir -p "$$(dirname "$(DB_PATH)")"; \
		if command -v sqlite3 >/dev/null 2>&1; then \
			sqlite3 "$(DB_PATH)" < "$(SCHEMA)"; \
			echo "$(GREEN)[INFO]$(NC) Database created successfully at $(DB_PATH)"; \
		else \
			echo "$(RED)[ERROR]$(NC) sqlite3 command not found. Please install SQLite3."; \
			exit 1; \
		fi; \
	else \
		echo "$(YELLOW)[WARN]$(NC) Database already exists at $(DB_PATH)"; \
	fi

.PHONY: db-reset
db-reset: ## Force delete database and recreate from schema
	@echo "$(GREEN)[INFO]$(NC) Resetting database..."
	@if [ -f "$(DB_PATH)" ]; then \
		echo "$(YELLOW)[WARN]$(NC) Database path '$(DB_PATH)' will be deleted and recreated."; \
		if echo "$(DB_PATH)" | grep -qE "(/var/|/opt/|/usr/|/home/.*production)"; then \
			echo "$(RED)[WARNING]$(NC) Database path looks like a production path!"; \
			echo "$(RED)[WARNING]$(NC) This will DELETE the existing database!"; \
			read -p "Are you sure? (yes/no): " confirm; \
			if [ "$$confirm" != "yes" ]; then \
				echo "$(GREEN)[INFO]$(NC) Operation cancelled"; \
				exit 0; \
			fi; \
		fi; \
	fi
	@if command -v python3 >/dev/null 2>&1; then \
		python3 "$(SCRIPTS_DIR)/db_reset.py" --db-path "$(DB_PATH)" --schema "$(SCHEMA)"; \
	elif command -v bash >/dev/null 2>&1; then \
		bash "$(SCRIPTS_DIR)/db_reset.sh"; \
	else \
		echo "$(RED)[ERROR]$(NC) Neither python3 nor bash found. Please install one of them."; \
		exit 1; \
	fi

.PHONY: db-status
db-status: ## Show database status and information
	@echo "$(GREEN)[INFO]$(NC) Database Status"
	@echo "=================="
	@if [ -f "$(DB_PATH)" ]; then \
		echo "$(GREEN)[INFO]$(NC) Database exists at: $(DB_PATH)"; \
		if command -v sqlite3 >/dev/null 2>&1; then \
			echo "$(GREEN)[INFO]$(NC) File size: $$(stat -f%z "$(DB_PATH)" 2>/dev/null || stat -c%s "$(DB_PATH)" 2>/dev/null || echo "unknown") bytes"; \
			echo "$(GREEN)[INFO]$(NC) Tables: $$(sqlite3 "$(DB_PATH)" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "unknown")"; \
			echo "$(GREEN)[INFO]$(NC) Schema version: $$(sqlite3 "$(DB_PATH)" "SELECT value FROM system_config WHERE key='schema_version';" 2>/dev/null || echo "unknown")"; \
		else \
			echo "$(YELLOW)[WARN]$(NC) sqlite3 not available for detailed status"; \
		fi; \
	else \
		echo "$(YELLOW)[WARN]$(NC) Database does not exist at: $(DB_PATH)"; \
	fi

.PHONY: db-backup
db-backup: ## Create a backup of the database
	@echo "$(GREEN)[INFO]$(NC) Creating database backup..."
	@if [ -f "$(DB_PATH)" ]; then \
		BACKUP_PATH="$(DB_PATH).backup.$$(date +%Y%m%d_%H%M%S)"; \
		cp "$(DB_PATH)" "$$BACKUP_PATH"; \
		echo "$(GREEN)[INFO]$(NC) Backup created: $$BACKUP_PATH"; \
	else \
		echo "$(YELLOW)[WARN]$(NC) No database to backup at $(DB_PATH)"; \
	fi

# Development targets
.PHONY: install
install: ## Install Python dependencies
	@echo "$(GREEN)[INFO]$(NC) Installing Python dependencies..."
	pip install -r requirements.txt

.PHONY: clean
clean: ## Clean up temporary files and caches
	@echo "$(GREEN)[INFO]$(NC) Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

.PHONY: test
test: db-reset ## Run tests (resets database first)
	@echo "$(GREEN)[INFO]$(NC) Running tests..."
	@echo "$(YELLOW)[WARN]$(NC) Test target not implemented yet"

.PHONY: run
run: db-create ## Run the application (creates database if needed)
	@echo "$(GREEN)[INFO]$(NC) Starting Retrovue..."
	python3 main.py

.PHONY: run-ui
run-ui: db-create ## Run the UI application (creates database if needed)
	@echo "$(GREEN)[INFO]$(NC) Starting Retrovue UI..."
	python3 run_ui.py

# CI/CD targets
.PHONY: ci-setup
ci-setup: ## Setup for CI environment
	@echo "$(GREEN)[INFO]$(NC) Setting up CI environment..."
	@echo "$(GREEN)[INFO]$(NC) Installing dependencies..."
	pip install -r requirements.txt
	@echo "$(GREEN)[INFO]$(NC) Creating fresh database..."
	$(MAKE) db-reset

.PHONY: ci-test
ci-test: ci-setup ## Run CI tests
	@echo "$(GREEN)[INFO]$(NC) Running CI tests..."
	@echo "$(YELLOW)[WARN]$(NC) CI test target not implemented yet"

# Utility targets
.PHONY: check-deps
check-deps: ## Check if required dependencies are installed
	@echo "$(GREEN)[INFO]$(NC) Checking dependencies..."
	@command -v python3 >/dev/null 2>&1 && echo "$(GREEN)[OK]$(NC) python3" || echo "$(RED)[MISSING]$(NC) python3"
	@command -v sqlite3 >/dev/null 2>&1 && echo "$(GREEN)[OK]$(NC) sqlite3" || echo "$(RED)[MISSING]$(NC) sqlite3"
	@command -v pip >/dev/null 2>&1 && echo "$(GREEN)[OK]$(NC) pip" || echo "$(RED)[MISSING]$(NC) pip"

.PHONY: validate-schema
validate-schema: ## Validate the schema file syntax
	@echo "$(GREEN)[INFO]$(NC) Validating schema file..."
	@if [ -f "$(SCHEMA)" ]; then \
		if command -v sqlite3 >/dev/null 2>&1; then \
			sqlite3 ":memory:" < "$(SCHEMA)" >/dev/null 2>&1 && echo "$(GREEN)[OK]$(NC) Schema syntax is valid" || echo "$(RED)[ERROR]$(NC) Schema syntax is invalid"; \
		else \
			echo "$(YELLOW)[WARN]$(NC) sqlite3 not available for validation"; \
		fi; \
	else \
		echo "$(RED)[ERROR]$(NC) Schema file not found: $(SCHEMA)"; \
	fi
