# Retrovue Database Schema

This document describes the database schema for Retrovue, including tables, relationships, and key constraints.

## Overview

Retrovue uses PostgreSQL as its primary database with SQLAlchemy ORM. The schema is designed to support:

- **Content management** (titles, episodes, assets)
- **Multi-source ingestion** (Plex, filesystem, etc.)
- **Quality assurance** (review queue)
- **External provider integration** (provider references)

## Core Tables

### Content Hierarchy

```
Titles (Movies/Shows)
├── Seasons (for TV shows)
│   └── Episodes
└── Episodes (for movies)
    └── Assets (media files)
```

### 1. Titles Table

**Purpose**: Represents movies and TV shows in the content library.

```sql
CREATE TABLE titles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind VARCHAR(50) NOT NULL,  -- 'movie' or 'show'
    name VARCHAR(255) NOT NULL,
    year INTEGER,
    external_ids JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Fields**:

- `id`: Primary key (UUID)
- `kind`: Content type (movie/show)
- `name`: Title name
- `year`: Release year
- `external_ids`: Provider-specific identifiers (TMDB, TVDB, etc.)

### 2. Seasons Table

**Purpose**: Represents seasons of TV shows.

```sql
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_id UUID NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Relationships**:

- `title_id` → `titles.id` (many-to-one)

### 3. Episodes Table

**Purpose**: Represents individual episodes or movies.

```sql
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_id UUID NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    number INTEGER,  -- Episode number (NULL for movies)
    name VARCHAR(255),  -- Episode title
    external_ids JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Relationships**:

- `title_id` → `titles.id` (many-to-one)
- `season_id` → `seasons.id` (many-to-one, optional)

### 4. Assets Table

**Purpose**: Represents media files (video, audio, etc.).

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uri TEXT NOT NULL UNIQUE,  -- File path or URL
    size BIGINT NOT NULL,  -- File size in bytes
    duration_ms INTEGER,  -- Duration in milliseconds
    video_codec VARCHAR(50),
    audio_codec VARCHAR(50),
    container VARCHAR(50),
    hash_sha256 VARCHAR(64),  -- SHA256 hash
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    canonical BOOLEAN DEFAULT FALSE NOT NULL
);
```

**Key Fields**:

- `uri`: Unique file identifier
- `size`: File size for storage management
- `duration_ms`: Runtime for scheduling
- `canonical`: Primary version flag
- `hash_sha256`: Content integrity verification

**Indexes**:

- `ix_assets_canonical` on `canonical`
- `ix_assets_discovered_at` on `discovered_at`

### 5. EpisodeAssets Junction Table

**Purpose**: Many-to-many relationship between episodes and assets.

```sql
CREATE TABLE episode_assets (
    episode_id UUID NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    PRIMARY KEY (episode_id, asset_id)
);
```

**Relationships**:

- `episode_id` → `episodes.id`
- `asset_id` → `assets.id`

## Provider Integration Tables

### 6. ProviderRefs Table

**Purpose**: References to entities in external providers (Plex, Jellyfin, etc.).

```sql
CREATE TABLE provider_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- 'title', 'episode', 'asset'
    entity_id UUID NOT NULL,  -- Reference to title/episode/asset
    provider VARCHAR(50) NOT NULL,  -- 'plex', 'jellyfin', etc.
    provider_key TEXT NOT NULL,  -- External provider identifier
    raw JSONB,  -- Raw provider data

    -- Polymorphic foreign keys
    title_id UUID REFERENCES titles(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE
);
```

**Key Fields**:

- `entity_type`: Type of referenced entity
- `provider`: External provider name
- `provider_key`: External identifier
- `raw`: Cached provider metadata

## Content Management Tables

### 7. Markers Table

**Purpose**: Markers placed on assets (chapters, availability windows, etc.).

```sql
CREATE TABLE markers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL,  -- 'chapter', 'avail', 'bumper', etc.
    start_ms INTEGER NOT NULL,  -- Start time in milliseconds
    end_ms INTEGER NOT NULL,    -- End time in milliseconds
    payload JSONB  -- Additional marker data
);
```

**Key Fields**:

- `kind`: Marker type (chapter, commercial break, etc.)
- `start_ms`/`end_ms`: Timeline positions
- `payload`: Marker-specific data

**Indexes**:

- `ix_markers_asset_id` on `asset_id`
- `ix_markers_kind` on `kind`

### 8. ReviewQueue Table

**Purpose**: Items requiring human review for quality assurance.

```sql
CREATE TABLE review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,  -- Why review is needed
    confidence FLOAT NOT NULL,  -- Confidence score (0.0-1.0)
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,  -- 'pending', 'resolved', 'rejected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);
```

**Key Fields**:

- `reason`: Review justification
- `confidence`: Automated confidence score
- `status`: Review workflow state

**Indexes**:

- `ix_review_queue_asset_id` on `asset_id`
- `ix_review_queue_status` on `status`
- `ix_review_queue_created_at` on `created_at`

## Source Management Tables

### 9. Sources Table

**Purpose**: Content sources (Plex servers, filesystem paths, etc.).

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) NOT NULL UNIQUE,  -- External identifier
    name VARCHAR(255) NOT NULL,  -- Human-readable name
    kind VARCHAR(50) NOT NULL,  -- 'plex', 'filesystem', etc.
    config JSONB,  -- Source-specific configuration
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Fields**:

- `external_id`: Unique source identifier
- `kind`: Source type
- `config`: Source-specific settings

### 10. SourceCollections Table

**Purpose**: Collections within sources (Plex libraries, directories, etc.).

```sql
CREATE TABLE source_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    external_id VARCHAR(255) NOT NULL,  -- Plex library ID, etc.
    name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE NOT NULL,
    config JSONB,  -- Collection-specific settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(source_id, external_id)
);
```

**Key Fields**:

- `source_id`: Parent source reference
- `external_id`: Collection identifier within source
- `enabled`: Whether collection is active
- `config`: Collection-specific configuration

**Indexes**:

- `ix_source_collections_source_id` on `source_id`
- `ix_source_collections_enabled` on `enabled`

### 11. PathMappings Table

**Purpose**: Path mappings for collections (Plex path → local path).

```sql
CREATE TABLE path_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES source_collections(id) ON DELETE CASCADE,
    plex_path VARCHAR(500) NOT NULL,  -- Plex server path
    local_path VARCHAR(500) NOT NULL,  -- Local filesystem path
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Fields**:

- `plex_path`: Path as seen by Plex
- `local_path`: Actual local filesystem path

**Indexes**:

- `ix_path_mappings_collection_id` on `collection_id`

## Relationships Summary

### Content Relationships

```
Title (1) ←→ (N) Season (1) ←→ (N) Episode (N) ←→ (N) Asset
```

### Provider Relationships

```
Title/Episode/Asset (1) ←→ (N) ProviderRef
```

### Source Relationships

```
Source (1) ←→ (N) SourceCollection (1) ←→ (N) PathMapping
```

### Quality Assurance

```
Asset (1) ←→ (N) Marker
Asset (1) ←→ (N) ReviewQueue
```

## Key Constraints

### 1. Referential Integrity

- **Cascade deletes** for dependent entities
- **Foreign key constraints** for data consistency
- **Unique constraints** for business rules

### 2. Data Validation

- **NOT NULL constraints** for required fields
- **CHECK constraints** for value ranges
- **ENUM constraints** for status fields

### 3. Performance Indexes

- **Primary key indexes** on all tables
- **Foreign key indexes** for join performance
- **Business logic indexes** for common queries

## Migration Strategy

### 1. Schema Evolution

- **Alembic migrations** for schema changes
- **Backward compatibility** for API changes
- **Data migration scripts** for complex changes

### 2. Data Integrity

- **Validation rules** in application layer
- **Database constraints** for data consistency
- **Audit trails** for change tracking

## Performance Considerations

### 1. Indexing Strategy

- **Composite indexes** for common query patterns
- **Partial indexes** for filtered queries
- **Covering indexes** for read-heavy workloads

### 2. Query Optimization

- **Eager loading** for related entities
- **Lazy loading** for large datasets
- **Query batching** for bulk operations

### 3. Storage Management

- **Partitioning** for large tables
- **Archiving** for historical data
- **Compression** for JSONB fields

---

_This schema provides a robust foundation for Retrovue's content management capabilities while maintaining flexibility for future enhancements._
