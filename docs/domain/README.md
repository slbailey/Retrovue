# Domain Documentation

This directory contains **domain model documentation** for RetroVue's core business entities and their relationships. These documents define the conceptual models, data structures, and business rules that form the foundation of the RetroVue system.

## Purpose

The `domain/` directory serves as the **authoritative source of truth** for understanding:

- **What** each business entity represents
- **How** entities relate to each other
- **What** business rules and constraints apply
- **Why** certain design decisions were made

This is **not** implementation documentation (that lives in `src/`), but rather the **conceptual foundation** that guides all implementation decisions.

## Domain-Driven Design

RetroVue follows Domain-Driven Design (DDD) principles, where the domain model reflects the real-world concepts of broadcast television operations:

- **Sources** → **Collections** → **Assets** (content hierarchy)
- **Assets** → **PlaylogEvents** → **Streams** (broadcast pipeline)
- **Channels** → **Schedules** → **Playout** (operational flow)

## Core Domain Entities

### Content Management Domain

- **[Asset](Asset.md)** - The leaf unit of broadcastable content with lifecycle states
- **[Source](Source.md)** - External content providers (Plex, filesystem, etc.)
- **[Collection](Collection.md)** - Logical groupings of content within sources
- **[Importer](Importer.md)** - Content discovery and ingestion from external systems
- **[Registry](Registry.md)** - Modular importer discovery, registration, and lifecycle management
- **[IngestPipeline](IngestPipeline.md)** - How external media becomes managed content

### Broadcast Operations Domain

- **[BroadcastChannel](BroadcastChannel.md)** - Channel identity and configuration
- **[Scheduling](Scheduling.md)** - Planning-time logic for future air
- **[PlaylogEvent](PlaylogEvent.md)** - Scheduled, timestamped playout units
- **[PlayoutPipeline](PlayoutPipeline.md)** - How scheduled content becomes streams

### Enhancement Domain

- **[Enricher](Enricher.md)** - Pluggable modules that enhance content or playout

### Scheduling Infrastructure Domain

- **[ScheduleDay](ScheduleDay.md)** - Template assignments for specific dates
- **[ScheduleTemplate](ScheduleTemplate.md)** - Reusable programming templates
- **[ScheduleTemplateBlock](ScheduleTemplateBlock.md)** - Time blocks within templates
- **[EPGGeneration](EPGGeneration.md)** - Electronic Program Guide generation

## Key Architectural Principles

### Single Asset Entity Model

RetroVue uses a **single Asset entity** with lifecycle states rather than separate "ingest assets" and "broadcast assets":

- **`new`** → **`enriching`** → **`ready`** → **`retired`**
- Only assets in `ready` state with `approved_for_broadcast=true` are eligible for scheduling
- UUID serves as the primary key and spine connecting all asset-related tables

### State-Based Eligibility

The system enforces clear boundaries based on asset state:

- **Ingest Layer**: Manages assets through `new` → `enriching` → `ready` progression
- **Scheduling Layer**: Only considers `ready` assets
- **Runtime Layer**: Only plays `ready` assets

### Asset vs Segment Distinction

- **Asset** = Conceptual content ("Transformers S01E03")
- **Segment** = Executable playout instructions (file path + offset + overlays for ffmpeg)

## How to Use This Documentation

### For Developers

1. **Start with [Asset](Asset.md)** - This is the central entity
2. **Understand the hierarchy** - Source → Collection → Asset
3. **Follow the flow** - Asset → PlaylogEvent → Playout
4. **Read related domains** - Each document links to related concepts

### For Operators

1. **Focus on operational domains** - BroadcastChannel, Scheduling, PlayoutPipeline
2. **Understand state transitions** - How assets become ready for broadcast
3. **Learn the constraints** - What can and cannot be scheduled

### For System Architects

1. **Study the relationships** - How domains interact
2. **Understand the boundaries** - Clear separation of concerns
3. **Follow the invariants** - Critical rules that must be maintained

## Document Structure

Each domain document follows a consistent structure:

- **Purpose** - What this entity represents
- **Core model / scope** - Data structure and fields
- **Contract / interface** - Business rules and constraints
- **Execution model** - How it operates in the system
- **Related documents** - Cross-references to other domains

## Critical Rules

Several critical rules span multiple domains:

1. **Asset State Rule**: Only `ready` assets with `approved_for_broadcast=true` are eligible for scheduling and playout
2. **UUID Spine Rule**: Asset UUID is the primary key and connects all asset-related tables
3. **Single Entity Rule**: There is only one Asset entity, not separate ingest/broadcast entities
4. **State Transition Rule**: Assets progress through lifecycle states, not through table copying

## Related Documentation

- **[Architecture Overview](../overview/architecture.md)** - High-level system design
- **[Runtime Documentation](../runtime/)** - How the system operates
- **[Operator Documentation](../operator/)** - How humans interact with the system
- **[Contract Documentation](../contracts/)** - Binding behavioral specifications

---

**Note**: This domain documentation is **conceptual** and **authoritative**. Implementation code in `src/` should align with these domain models. When implementation diverges from domain documentation, the domain documentation takes precedence and implementation should be updated to match.
