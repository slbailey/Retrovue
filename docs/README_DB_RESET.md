# Retrovue Database Reset Guide

This guide explains how to reset and recreate the Retrovue database using the v1.2 schema.

## Overview

The database reset system provides a clean way to:
- Remove all existing database files and migration artifacts
- Create a fresh SQLite database from the authoritative v1.2 schema
- Ensure deterministic database creation for development and testing

## Quick Start

### Using Make (Recommended)

```bash
# Reset database (deletes existing and creates fresh)
make db-reset

# Create database only if it doesn't exist
make db-create

# Check database status
make db-status
```

### Using Scripts Directly

```bash
# Linux/macOS
./scripts/db_reset.sh

# Cross-platform Python
python3 scripts/db_reset.py
```

## Configuration

### Environment Variables

- `DB_PATH`: Database file path (default: `data/retrovue.db`)
- `SCHEMA`: Schema file path (default: `sql/retrovue_schema_v1.2.sql`)

### Custom Configuration

```bash
# Custom database path
DB_PATH=/custom/path/retrovue.db make db-reset

# Custom schema file
SCHEMA=sql/custom_schema.sql make db-reset
```

## Safety Features

### Production Path Detection

The scripts automatically detect production-like paths and require confirmation:
- `/var/`, `/opt/`, `/usr/` directories
- Paths containing `production`
- Home directory production folders

### Backup Recommendation

Before resetting a production database:

```bash
# Create backup first
make db-backup

# Then reset
make db-reset
```

## File Structure

```
retrovue/
├── sql/
│   └── retrovue_schema_v1.2.sql    # Authoritative schema
├── scripts/
│   ├── db_reset.sh                 # Linux/macOS reset script
│   └── db_reset.py                 # Cross-platform reset script
├── Makefile                        # Make targets
└── docs/
    └── README_DB_RESET.md          # This file
```

## Schema v1.2 Features

The v1.2 schema implements a **Plex-centric media-first architecture**:

### Core Tables
- `plex_servers`: Plex server configurations and connections
- `libraries`: Plex library definitions and metadata
- `path_mappings`: Critical mappings from Plex paths to accessible local paths
- `media_files`: Physical media file references with technical metadata
- `content_items`: Logical content wrappers with editorial metadata

### TV Structure
- `shows`: TV series metadata with Plex integration
- `seasons`: Season information and organization
- `content_items`: Episode-level content with show/season relationships

### Advanced Features
- `content_tags`: Namespaced tagging system for flexible content organization
- `content_editorial`: Source metadata preservation and editorial overrides
- `media_markers`: Ad breaks, chapters, and cue points
- `schedule_blocks`: Programming templates with strategy support
- `schedule_instances`: Specific scheduled content with approval workflow
- `play_log`: Comprehensive logging of what actually aired

### External Integration
- `plex_servers`: Multiple Plex server support
- `libraries`: Plex library organization
- `path_mappings`: Critical for streaming functionality

## Make Targets

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets |
| `make db-create` | Create database if it doesn't exist |
| `make db-reset` | Force delete and recreate database |
| `make db-status` | Show database information |
| `make db-backup` | Create timestamped backup |
| `make check-deps` | Check required dependencies |
| `make validate-schema` | Validate schema syntax |
| `make clean` | Clean temporary files |
| `make install` | Install Python dependencies |
| `make run` | Run main application |
| `make run-ui` | Run UI application |

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Database
  run: make ci-setup

- name: Run Tests
  run: make ci-test
```

### Local Development

```bash
# Fresh start for development
make clean
make install
make db-reset
make run-ui
```

## Troubleshooting

### Common Issues

#### "sqlite3 command not found"
```bash
# Install SQLite3
# Ubuntu/Debian
sudo apt install sqlite3

# macOS
brew install sqlite3

# Windows
# Download from https://sqlite.org/download.html
```

#### "Schema file not found"
```bash
# Ensure you're in the project root
cd /path/to/retrovue

# Check if schema exists
ls -la sql/retrovue_schema_v1.2.sql
```

#### "Permission denied" (Linux/macOS)
```bash
# Make script executable
chmod +x scripts/db_reset.sh
```

#### "Database is locked"
```bash
# Stop any running applications
# Then retry
make db-reset
```

### Validation

```bash
# Check dependencies
make check-deps

# Validate schema syntax
make validate-schema

# Check database status
make db-status
```

## Schema Management Methodology

### Schema-First Approach

Retrovue uses a **schema-first approach** with no migration framework:

#### **Single Source of Truth**
- **`sql/retrovue_schema_v1.2.sql`** is the authoritative schema file
- All schema changes are made directly to this SQL file
- No migration scripts, no version tracking, no incremental changes

#### **Clean Recreate Workflow**
1. **Delete existing database**: Remove the `.db` file
2. **Update schema**: Modify `sql/retrovue_schema_v1.2.sql` as needed
3. **Recreate database**: Run `scripts/db_reset.py` to create fresh database
4. **Re-import data**: Use the UI to re-sync from Plex/TMM sources

#### **Benefits of This Approach**
- **Deterministic**: Every database creation produces identical results
- **Simple**: No complex migration logic or version management
- **Reliable**: No risk of migration failures or data corruption
- **Fast**: Schema changes are immediate, no migration downtime
- **Clean**: No legacy migration artifacts or version tracking

#### **Development Workflow**
```bash
# Make schema changes
# Edit sql/retrovue_schema_v1.2.sql

# Reset database with new schema
python scripts/db_reset.py

# Re-import content
# Use UI to sync from Plex/TMM
```

#### **Production Considerations**
- **Backup First**: Always backup existing data before schema changes
- **Data Export**: Export any custom data before reset
- **Re-import**: Plan for re-importing content after schema changes
- **Testing**: Test schema changes in development first

## Best Practices

### Development
- Use `make db-reset` before starting new features
- Always test with fresh database
- Use `make db-backup` before major changes

### Production
- **Never** run `make db-reset` on production without backup
- Use `make db-backup` before any database operations
- Test reset procedures in staging environment first

### CI/CD
- Always use `make ci-setup` in CI pipelines
- Never cache database files between CI runs
- Use `make db-reset` for deterministic test environments

## Support

For issues with the database reset system:

1. Check this documentation
2. Run `make check-deps` to verify dependencies
3. Run `make validate-schema` to check schema
4. Check the project's main documentation

## Security Notes

- Database files contain no sensitive data by default
- Plex tokens are stored separately in configuration
- Path mappings may contain local file system paths
- Always backup before resetting production databases
