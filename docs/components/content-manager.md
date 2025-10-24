# Content Manager

## Overview

The **Content Manager** is RetroVue's content discovery and library management system. It's responsible for finding media files, understanding what they contain, deciding which ones are suitable for broadcast, and maintaining the authoritative library that the rest of the system depends on.

Think of it as the "librarian" of RetroVue—it knows what content exists, where it came from, and whether it's ready to be scheduled for broadcast.

## What This Document Is

This document describes the **architecture and behavior** of the Content Manager layer. It explains:

- What the Content Manager does and doesn't do
- How its components work together
- How it fits into RetroVue's overall architecture
- How other parts of the system should interact with it

This is **not** a code-level API reference—it's about understanding the system's design and responsibilities.

## Core Responsibilities

The Content Manager has four main jobs:

### 1. **Discovery & Ingest**

- **Find media** in external systems (Plex servers, filesystems, etc.)
- **Extract metadata** like file size, duration, codecs, and content hashes
- **Classify content deterministically** (episode, bumper, promo, ad, etc.)
- **Annotate operational metadata** needed for scheduling, such as runtime, break markers / ad insertion points, and safety/restriction flags

### 2. **Library Management**

- **Create internal records** for discovered media files
- **Link files to logical content** (episodes, shows, movies)
- **Mark content as "canonical"** when it's good enough for broadcast
- **Handle content lifecycle** (soft-delete, restore, etc.)

### 3. **Source Configuration**

- **Track content sources** (which Plex servers, which folders)
- **Map file paths** so we can find files regardless of where they're stored
- **Control what gets scanned** by enabling/disabling specific collections

### 4. **Quality Control**

- **Score content confidence** to determine if it's broadcast-ready
- **Auto-approve good content** for immediate use
- **Queue questionable content** for human review
- **Provide tools** for humans to resolve ambiguous cases

## Design Principles Alignment

The Content Manager follows RetroVue's architectural patterns:

- **Adapters** handle communication with external systems (Plex, filesystem)
- **Enrichers** add meaning and metadata to raw content
- **Importers (Adapters)** discover and normalize content from external sources
- **LibraryService (using a Unit of Work)** commits that content into the authoritative library
- **Services** provide focused capabilities to other components
- **Authorities** maintain single sources of truth
- **Unit of Work** ensures atomic operations

**Operational rule:** there is no such thing as a "partial ingest." If an ingest run half-worked and half-failed, the correct interpretation is "it failed."

## System Boundaries

**What Content Manager DOES:**

- ✅ Discovers and catalogs content
- ✅ Manages the authoritative content library
- ✅ Provides content metadata to scheduling systems
- ✅ Handles content quality and review processes

**What Content Manager DOES NOT:**

- ❌ Schedule content for broadcast
- ❌ Handle real-time playback
- ❌ Manage viewer sessions
- ❌ Generate programming guides

> **Key Principle:** Content Manager is the **upstream supplier** for scheduling and playback systems. They ask Content Manager for eligible content—they don't go hunting through filesystems or calling Plex directly.

## Core Data Model

All content information is stored in SQLAlchemy models in `src/retrovue/domain/entities.py`. These represent the "source of truth" for what content exists and how it's organized.

### Asset

Represents a single media file we know about.

**Key Properties:**

- `id` - Database primary key
- `uuid` - Stable external identifier
- `uri` - File path or URI
- `size` - File size in bytes
- `duration_ms` - Runtime (populated by enrichment)
- `video_codec`, `audio_codec`, `container` - Technical details
- `hash_sha256` - Content fingerprint
- `canonical` - Whether this asset is approved for scheduling and playout.
  - `canonical=True` means "this asset is broadcast-ready and safe for downstream systems to use without human intervention."
  - `canonical=False` means "this asset exists but is not yet approved; it may still be in review or be unsuitable for air."
- `is_deleted` / `deleted_at` - Soft deletion support

**Relationships:**

- Links to Episodes (many-to-many)
- Has Markers (chapter points, ad breaks)
- Has ReviewQueue items (if needs human attention)
- Has ProviderRefs (links to external systems like Plex)

### Episode / Title / Season

Logical content structure:

- **Title** = Show or movie (e.g., "Batman: The Animated Series")
- **Season** = Grouping under a title
- **Episode** = Individual piece of content with episode number, name, and external IDs

This connects logical programming ("Season 1 Episode 3 of Batman TAS") to actual playable files.

### ProviderRef

Maps back to external systems (like Plex).

**Properties:**

- `entity_type` - What kind of entity (Asset, Episode, etc.)
- `entity_id` - UUID of that entity
- `provider` - External system name (e.g., "Plex")
- `provider_key` - External system's identifier
- `raw_metadata` - Original metadata from external system

### ReviewQueue

Tracks content that needs human attention.

**Properties:**

- `asset_id` - Which asset needs review
- `reason` - Why it needs review ("File size too small", "No hash available")
- `confidence` - Confidence score (0.0–1.0)
- `status` - Current state (PENDING, etc.)

### Source / SourceCollection / PathMapping

Describes where content comes from and how to access it.

- **Source** - External provider (Plex server, filesystem root)
- **SourceCollection** - Subdivision (Plex library, directory)
  - Each collection has an `enabled` flag that controls whether it is eligible for ingest
  - Disabling a collection means "do not ingest from here", even if the files are technically accessible
- **PathMapping** - Maps external paths to local filesystem paths
  - Path mapping only translates paths; it does not control ingest eligibility or access policy

## Major Services

### LibraryService

**File:** `src/retrovue/content_manager/library_service.py`

**Role:** The single source of truth for the content library.

**Design Pattern:** Authority + Service/Capability Provider

**Key Responsibilities:**

- Register new assets from discovery
- Enrich assets with metadata
- Link assets to episodes
- Mark assets as canonical
- Manage review queue
- List and fetch assets
- Handle asset lifecycle (delete, restore)

**Important Behaviors:**

- **Soft delete by default** - Sets `is_deleted=True` instead of removing records
- **Hard delete only when safe** - Checks if assets are referenced by episodes
- **Unit of Work boundaries** - All operations are atomic (commit/rollback)
- **Authority over content** - Nothing else should directly modify the library

**Authority Rule:**
LibraryService is the single authority over Assets, Episodes, and ReviewQueue state.
No other part of the system (CLI, API, ingest orchestrator, schedulers, runtime) may write or mutate these records directly.
All creation, enrichment, canonicalization, deletion, restore, and review resolution must go through LibraryService.

### SourceService

**File:** `src/retrovue/content_manager/source_service.py`

**Role:** Manages external content sources and path mappings.

**Design Pattern:** Authority + Service/Capability Provider

**Key Responsibilities:**

- Create and register Plex sources
- Discover libraries/collections from sources
- Enable/disable collections for ingestion
- Manage path mappings
- List enabled collections with metadata

**Why This Matters:**
Ingest systems need to know which sources to scan and how to translate external paths to local filesystem paths. SourceService provides this information so ingest can be deterministic and source-agnostic.

**Authority Rule:**
SourceService is the single authority for external source configuration (Plex servers, filesystem roots), enabled/disabled collections, and path mappings.
No other component is allowed to "just talk to Plex," "scan a random directory," or invent a mapping for a path on its own.

### Ingest Orchestrator

**File:** `src/retrovue/content_manager/ingest_orchestrator.py`

**Role:** Coordinates ingest from configured sources into the library.

**Design Pattern:** Orchestrator

**High-Level Flow:**

1. **Identify sources** to scan
2. **Use Importers** to discover content
3. **For each discovered item:**
   - Register asset via LibraryService
   - Attempt enrichment (metadata extraction)
   - Calculate confidence score
   - Either mark canonical or queue for review
4. **Return summary counts**

**Key Behaviors:**

- **Confidence scoring** - Determines if content is broadcast-ready
- **Automatic canonicalization** - Good content is immediately usable
- **Review queueing** - Questionable content gets human attention
- **Comprehensive logging** - Tracks discovery, registration, enrichment, etc.
- **Batch/Offline Only** - Runtime playback and schedulers must not call it during tune-in/playout. They consume only what's in the library.

### PathResolverService

**File:** `src/retrovue/content_manager/path_service.py`

**Role:** Centralized path mapping and resolution for external sources.

**Design Pattern:** Service / Capability Provider

**Key Features:**

- Translates external source paths to local filesystem paths
- Uses configured PathMapping records for resolution
- Provides consistent path translation across the system
- Validates resolved paths exist on local filesystem

**Authority Rule:**
PathResolverService is the only approved way to translate provider paths (e.g. Plex-provided paths) into local playable filesystem paths.
No other component — CLI commands, ingest logic, runtime playback, schedulers — is allowed to guess or rewrite paths manually.

## Adapter Layer

The ingest system is designed to be pluggable through adapters.

### Importers

**Location:** `src/retrovue/adapters/importers/`

**Design Pattern:** Adapter

**Purpose:** Discover content from external systems without modifying system state.

**Key Importers:**

- **FilesystemImporter** - Walks local directories, extracts file stats, computes hashes
- **PlexImporter** - Talks to Plex Media Server, discovers libraries and episodes

**Rules:**

- **Discovery only** - Don't write to database
- **Normalize external quirks** - Convert to internal format
- **Raise proper exceptions** - Don't leak external system errors

### Enrichers

**Location:** `src/retrovue/adapters/enrichers/`

**Design Pattern:** Enricher

**Purpose:** Add structured metadata to discovered content.

**Key Enrichers:**

- **FFprobeEnricher** - Runs ffprobe to extract duration, codecs, container format

**Rules:**

- **Deterministic** - Same input produces same output
- **Structured metadata** - Add flags, tags, classifications
- **No persistence** - Just return enriched data
- **No policy decisions** - Add meaning, not business rules

### Registry

**Location:** `src/retrovue/adapters/registry.py`

**Purpose:** Plugin system for Importers and Enrichers.

**Features:**

- Global registries for all available components
- Registration and lookup functions
- Plugin model for extensibility

## CLI and API Surfaces

### CLI (Command Line Interface)

**Location:** `src/retrovue/cli/`

**Purpose:** Manual operation of the Content Manager.

**Key Command Groups:**

#### `retrovue ingest`

- Runs content discovery and registration
- Outputs counts (discovered, registered, enriched, canonicalized, queued)
- Supports JSON output format

#### `retrovue assets`

- **list** - Browse assets with filtering options
- **get** - Fetch detailed information about a specific asset
- **select** - Pick assets from a series
- **delete** - Soft-delete assets (with hard-delete option)
- **restore** - Undo soft-deletes

#### `retrovue review`

- **list** - Show items in review queue
- **resolve** - Mark review items as resolved

#### `retrovue plex`

- **verify** - Test Plex connection
- **get-episode** - Pull episode metadata (dry run)
- **ingest-episode** - Actually import episode data

**Unit of Work:** All CLI operations use `infra/uow.py` for proper database session management.

### API (FastAPI)

**Location:** `src/retrovue/api/`

**Purpose:** Programmatic access for future admin GUI.

**Features:**

- Same capabilities as CLI
- RESTful endpoints for assets, review queue, ingest
- Proper schemas and DTOs
- Unit of Work via `infra.uow.get_db()`

**Key Routers:**

- `assets.py` - Asset management endpoints
- `ingest.py` - Ingest operations
- `review.py` - Review queue management

## How Other Systems Use Content Manager

### ScheduleManager (Future)

When we build the scheduling system, it will:

- **Ask Content Manager** for pools of canonical assets
- **Get stable UUIDs** and metadata for scheduling
- **Trust that canonical assets** are broadcast-ready

**Content Manager provides:**

- Reliable series/episode grouping
- Runtime and duration data
- Ad break markers and restrictions
- Content ratings and classifications

### ChannelManager / Producer (Future)

At runtime, playback systems will:

- **Only use canonical assets** that aren't soft-deleted
- **Trust enrichment data** for codecs, duration, container type
- **Not guess content properties** - enrichment already handled this

**Downstream Rule (Scheduler, ChannelManager, Producer):**

- Must not scan the filesystem directly
- Must not call Plex or any other external provider directly
- Must not probe media files directly for codecs/duration/etc.
- Must not invent metadata about safety, daypart, or suitability on the fly

If downstream code needs information it can't get from Content Manager, that is a feature request for Content Manager — not permission to bypass it.

## Key Architectural Principles

### Single Responsibility

Each component has one clear purpose:

- **LibraryService** - Content library authority
- **SourceService** - External source management
- **Ingest Orchestrator** - Discovery orchestration
- **Importers** - External system communication
- **Enrichers** - Metadata enhancement

### Replaceability

All components can be swapped without system-wide changes:

- Importers are pluggable through the registry
- Enrichers can be added or replaced
- Services have clear interfaces

### Authority Boundaries

- **LibraryService** is the authority over content assets
- **SourceService** is the authority over external sources
- **Nothing else** should directly modify these authorities

### Unit of Work

All write operations are atomic:

- Success = commit all changes
- Failure = rollback everything
- No partial states allowed

## Summary

The Content Manager is RetroVue's content discovery and library management system. It:

- **Discovers** content from external sources
- **Enriches** it with metadata and meaning
- **Manages** the authoritative content library
- **Provides** clean interfaces for other systems
- **Ensures** content quality through review processes

It follows RetroVue's architectural patterns and provides the foundation that scheduling and playback systems depend on. The CLI is the primary control interface, with the API enabling future GUI development.

**Remember:** Content Manager is about **content discovery and library management**—not scheduling, playback, or runtime operations.
