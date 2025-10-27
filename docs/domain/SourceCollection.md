_Related: [Architecture](../overview/architecture.md) • [Asset](Asset.md) • [Ingest Pipeline](IngestPipeline.md)_

# Domain — Source Collection Hierarchy

## Purpose

This document establishes the official mapping of the content hierarchy in RetroVue. It defines the relationship between Sources, Collections, and Assets, and serves as the high-level ingestion model reference.

## Hierarchy Definition

### Source

A **source** is an origin of media content. Sources represent external systems or locations where content can be discovered.

**Examples:**

- Plex library (e.g., "Movies", "TV Shows")
- Filesystem path (e.g., `/media/shows`, `/media/commercials`)
- Capture pipeline (e.g., live TV recording)
- Ad library API (e.g., commercial content provider)

### Collection

A **collection** groups related content inside a source. Collections organize content into broadcast-relevant categories within their parent source.

**Examples:**

- "Transformers Season 1" (within a TV Shows source)
- "Commercials_90s" (within a Commercials source)
- "Station IDs" (within a Promos source)
- "Classic Movies" (within a Movies source)

**TV Show Collections:**

Collections of TV shows typically have a hierarchical structure before reaching individual assets:

```
Collection (TV Show) → Title → Season → Episode → Asset
```

For example:

- **Collection**: "The Simpsons" (TV Show collection)
- **Title**: "The Simpsons" (show title)
- **Season**: "Season 1", "Season 2", etc.
- **Episode**: "Bart the Genius", "Homer's Odyssey", etc.
- **Asset**: Individual episode file

This hierarchy allows for:

- **Season-level operations**: Select all episodes from Season 1
- **Episode-level operations**: Select specific episodes
- **Show-level operations**: Select episodes across all seasons
- **Asset-level operations**: Select specific playable files

### Asset

An **asset** is a playable unit within a collection. Assets represent individual pieces of content that can eventually be broadcast.

**Examples:**

- Individual episode files
- Individual movie files
- Individual commercial spots
- Individual bumper/promo files

## Relationship Cardinality

### Basic Hierarchy

```
Source (1) → (N) Collections
Collection (1) → (N) Assets
```

- **One source** can contain **many collections**
- **One collection** can contain **many assets**
- **Each asset** belongs to exactly **one collection**
- **Each collection** belongs to exactly **one source**

### TV Show Hierarchy

For TV show collections, the hierarchy is more complex:

```
Source (1) → (N) Collections
Collection (1) → (N) Titles
Title (1) → (N) Seasons
Season (1) → (N) Episodes
Episode (1) → (N) Assets
```

- **One source** can contain **many collections**
- **One collection** can contain **many titles** (TV shows)
- **One title** can contain **many seasons**
- **One season** can contain **many episodes**
- **One episode** can contain **many assets** (different formats, qualities, etc.)

**Note:** Movies and other content types typically follow the simpler Collection → Asset hierarchy.

## Ingestion Model

> **We ingest sources, which yield collections, which yield assets.**

### Ingestion Flow

1. **Source Discovery**: RetroVue connects to and discovers available sources
2. **Collection Enumeration**: For each source, RetroVue enumerates available collections
3. **Content Structure Discovery**: For TV show collections, RetroVue discovers the Title → Season → Episode hierarchy
4. **Asset Registration**: For each collection (or episode for TV shows), RetroVue registers individual assets
5. **Asset Enrichment**: Registered assets progress through the lifecycle state machine

### State Progression

Assets progress through states as they are processed:

```
new → enriching → ready → retired
```

- **`new`**: Recently discovered, minimal metadata
- **`enriching`**: Being processed by enrichers
- **`ready`**: Fully processed, approved for broadcast
- **`retired`**: No longer available or approved

## Implementation Model

### Database Relationships

```sql
-- Simplified schema representation
Source {
  id: Integer (PK)
  uuid: UUID
  name: String
  type: String
  -- source-specific configuration
}

Collection {
  uuid: UUID (PK)
  source_id: Integer (FK → Source.id)
  name: String
  -- collection-specific metadata
}

Asset {
  uuid: UUID (PK)
  collection_uuid: UUID (FK → Collection.uuid)
  state: String
  -- asset-specific metadata
}
```

### API Surface

The hierarchy is exposed through the CLI and API:

- **Source operations**: `retrovue sources list`, `retrovue sources scan`
- **Collection operations**: `retrovue collections list`, `retrovue collections scan`
- **TV Show operations**: `retrovue shows list`, `retrovue shows seasons`, `retrovue shows episodes`
- **Asset operations**: `retrovue assets list`, `retrovue assets select`

## Operator Mental Model

Operators should understand that:

1. **Sources are discovered** - RetroVue connects to external systems
2. **Collections are enumerated** - Sources reveal their content groupings
3. **TV Show structure is discovered** - For TV collections, the Title → Season → Episode hierarchy is mapped
4. **Assets are registered** - Individual playable units are cataloged
5. **Assets are enriched** - Content progresses through processing states
6. **Ready assets are schedulable** - Only `ready` assets can be broadcast

## See also

- [Asset](Asset.md) - Individual content units
- [Ingest Pipeline](IngestPipeline.md) - Content discovery workflow
- [Architecture](../overview/architecture.md) - System overview
