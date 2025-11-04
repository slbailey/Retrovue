# Unused Tables Analysis

**Date:** 2025-01-27  
**Analysis Script:** `scripts/analyze_unused_tables.py`

## Summary

The analysis found **6 tables** in the PostgreSQL database that are **NOT** defined in the SQLAlchemy models (`src/retrovue/domain/entities.py`):

### 1. `alembic_version` ✅ (System Table)

- **Status:** Expected - This is Alembic's system table for tracking migrations
- **References:** Found in Alembic migrations
- **Action:** No action needed - this is a required system table

### 2. `broadcast_channels` ⚠️ (Broadcast Domain)

- **Status:** Missing from SQLAlchemy models
- **References:** Found in:
  - Alembic migrations (`alembic/versions/9541bbc23bcd_fresh_baseline_schema.py`)
  - Test fixtures (`src/retrovue/tests/conftest.py`)
- **Action:** Should be added to `entities.py` if broadcast functionality is being used

### 3. `broadcast_playlog_event` ⚠️ (Broadcast Domain)

- **Status:** Missing from SQLAlchemy models
- **References:** Found in:
  - Alembic migrations
  - Test fixtures (`src/retrovue/tests/conftest.py`)
  - Legacy tests (`tests/_legacy/test_compliance_reporting.py`)
- **Action:** Should be added to `entities.py` if broadcast functionality is being used

### 4. `broadcast_schedule_day` ⚠️ (Broadcast Domain)

- **Status:** Missing from SQLAlchemy models
- **References:** Found in Alembic migrations and test fixtures
- **Action:** Should be added to `entities.py` if broadcast functionality is being used

### 5. `broadcast_template` ⚠️ (Broadcast Domain)

- **Status:** Missing from SQLAlchemy models
- **References:** Found in Alembic migrations and test fixtures
- **Action:** Should be added to `entities.py` if broadcast functionality is being used

### 6. `broadcast_template_block` ⚠️ (Broadcast Domain)

- **Status:** Missing from SQLAlchemy models
- **References:** Found in Alembic migrations and test fixtures
- **Action:** Should be added to `entities.py` if broadcast functionality is being used

## Context

According to the documentation:

- These broadcast tables are part of the **Broadcast Domain** (separate from Library Domain)
- They are documented in `docs/data-model/broadcast-schema.md`
- The documentation states they should exist, but they're not currently modeled in SQLAlchemy
- The tables are referenced in test fixtures for cleanup, but not in active application code

## Recommendation

### Option 1: Add Broadcast Domain Models (Recommended if using broadcast features)

If the broadcast/scheduling functionality is being used or planned:

1. Create SQLAlchemy models for all broadcast tables in `entities.py` or a separate `broadcast_entities.py`
2. This would provide type safety and ORM access to these tables

### Option 2: Remove Broadcast Tables (If not needed)

If broadcast functionality is not being used:

1. Create an Alembic migration to drop these tables
2. Remove references from test fixtures
3. Update documentation to reflect that broadcast features are deferred

### Option 3: Keep as-is (Temporary)

If broadcast functionality is planned but not yet implemented:

- Keep the tables in the database (they're already created)
- Document that models are deferred
- Add models when broadcast functionality is implemented

## Tables Currently Defined in Models

The following 18 tables **are** properly defined in `entities.py`:

- `asset_editorial`
- `asset_probed`
- `asset_relationships`
- `asset_sidecar`
- `asset_station_ops`
- `assets`
- `channels`
- `collections`
- `enrichers`
- `episode_assets`
- `episodes`
- `markers`
- `path_mappings`
- `provider_refs`
- `review_queue`
- `seasons`
- `sources`
- `titles`

## Note on Analysis Method

The analysis searches for string patterns in the codebase. Some tables may be:

- Referenced dynamically via SQLAlchemy relationships
- Used in raw SQL queries that weren't caught by pattern matching
- Referenced through indirect means

For a more thorough analysis, consider:

- Checking Alembic migrations for table creation/dropping
- Reviewing documentation for intended usage
- Checking if tables have foreign key relationships from other tables
