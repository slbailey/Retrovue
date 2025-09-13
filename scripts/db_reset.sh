#!/bin/bash
# Retrovue Database Reset Script
# Nukes old DB and applies fresh v1.1 schema

set -e  # Exit on any error

# Configuration
DB_PATH="${DB_PATH:-data/retrovue.db}"
SCHEMA="${SCHEMA:-sql/retrovue_schema_v1.2.sql}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if path looks like production
check_production_path() {
    local path="$1"
    if [[ "$path" == *"/var/"* ]] || [[ "$path" == *"/opt/"* ]] || [[ "$path" == *"/usr/"* ]] || [[ "$path" == *"/home/"*"/production"* ]]; then
        return 0  # Looks like production
    fi
    return 1  # Doesn't look like production
}

# Main function
main() {
    print_status "Retrovue Database Reset Script"
    print_status "=============================="
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check if schema file exists
    if [[ ! -f "$SCHEMA" ]]; then
        print_error "Schema file not found: $SCHEMA"
        print_error "Please ensure the schema file exists in the project root"
        exit 1
    fi
    
    # Check if path looks like production
    if check_production_path "$DB_PATH"; then
        print_warning "WARNING: Database path '$DB_PATH' looks like a production path!"
        print_warning "This script will DELETE the existing database and recreate it."
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            print_status "Operation cancelled by user"
            exit 0
        fi
    fi
    
    # Ensure parent directory exists
    DB_DIR="$(dirname "$DB_PATH")"
    if [[ ! -d "$DB_DIR" ]]; then
        print_status "Creating database directory: $DB_DIR"
        mkdir -p "$DB_DIR"
    fi
    
    # Remove existing database if it exists
    if [[ -f "$DB_PATH" ]]; then
        print_status "Removing existing database: $DB_PATH"
        rm -f "$DB_PATH"
    fi
    
    # Check if sqlite3 is available
    if ! command -v sqlite3 &> /dev/null; then
        print_error "sqlite3 command not found. Please install SQLite3."
        exit 1
    fi
    
    # Apply schema
    print_status "Applying schema from: $SCHEMA"
    print_status "Creating database at: $DB_PATH"
    
    if sqlite3 "$DB_PATH" < "$SCHEMA"; then
        print_status "Database created successfully!"
        
        # Verify database was created
        if [[ -f "$DB_PATH" ]]; then
            DB_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null || echo "unknown")
            print_status "Database file size: $DB_SIZE bytes"
            
            # Show table count
            TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "unknown")
            print_status "Tables created: $TABLE_COUNT"
        else
            print_error "Database file was not created!"
            exit 1
        fi
    else
        print_error "Failed to create database!"
        exit 1
    fi
    
    print_status "Database reset completed successfully!"
}

# Run main function
main "$@"
