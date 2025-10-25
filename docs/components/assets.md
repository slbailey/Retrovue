# Assets Identity Model

## Overview

The assets table uses a dual identity model to provide both internal database efficiency and external API stability.

## Identity Structure

### Internal Identity: `id` (integer)
- **Type**: INTEGER AUTOINCREMENT (SQLite)
- **Purpose**: Primary key for database operations and foreign key references
- **Usage**: Internal database operations, foreign key relationships
- **Characteristics**: 
  - Auto-incrementing integer
  - Efficient for joins and indexing
  - Used by all foreign key tables (episode_assets, markers, review_queue, provider_refs)

### External Identity: `uuid` (UUID)
- **Type**: UUID (CHAR(36)/TEXT in SQLite)
- **Purpose**: Stable public identifier for API and external references
- **Usage**: API endpoints, playlists, playout manifests, external integrations
- **Characteristics**:
  - Globally unique identifier
  - Stable across database operations
  - Human-readable in logs and debugging
  - Used in playlists and playout manifests

## Usage Guidelines

### For Database Operations
- Use `id` (integer) for all foreign key relationships
- Use `id` for internal queries and joins
- Use `id` for performance-critical operations

### For API and External Operations
- Use `uuid` for API endpoints that accept asset identifiers
- Use `uuid` in playlists and playout manifests
- Use `uuid` for external integrations and logging
- Always include both `id` and `uuid` in API responses

## Database Schema

```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid CHAR(36) NOT NULL UNIQUE,
    -- other columns...
);

CREATE UNIQUE INDEX assets_uuid_idx ON assets(uuid);
```

## API Response Format

```json
{
  "id": 123,
  "uuid": "a17d9c8e-4b2f-4c3d-8e9f-1a2b3c4d5e6f",
  "uri": "/path/to/asset.mp4",
  "size": 1048576,
  "canonical": true
}
```

## Migration Notes

When migrating from UUID-only to this dual identity model:
1. Existing UUID primary keys are converted to integer auto-increment
2. A new `uuid` column is added for external references
3. All foreign key tables are updated to reference the new integer `id`
4. API endpoints are updated to accept both integer `id` and UUID `uuid` parameters