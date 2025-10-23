# Streaming Pipeline Concepts (Deferred Work)

## Overview

This document captures key architectural concepts for Retrovue's streaming pipeline. These ideas represent the intended design direction but are **not to be implemented yet**. They are documented here for future reference once the foundation (Content Library, domain model, and FastAPI integration) is solidified.

## Continuous Playback (Perpetual Live Channel)

### Goal: True 24x7 Live Channel

The ultimate objective is to create a true 24x7 live channel with **no defined start or end**. This differs fundamentally from traditional video streaming approaches:

- **Traditional approach:** `concat.txt`-style playlists with beginning and end points
- **Retrovue approach:** Continuously assembled stream that runs indefinitely
- **Challenge:** The system must continuously assemble a stream on the fly, alternating between program segments and ad breaks, without ever "running out" of content

### Key Requirements

- **Perpetual operation:** Channel runs continuously without manual intervention
- **Dynamic content selection:** System chooses what to play next based on rules and scheduling
- **Seamless transitions:** No gaps, stutters, or interruptions in the stream
- **Content variety:** Mix of programs, ads, bumpers, and promos according to schedule

## Segmented Playback Logic

### Timeline-Aware Sources

Each program file (e.g., `episode1.mp4`) should be represented as a **timeline-aware source** rather than a simple file path:

**Example Playback Sequence:**

1. Play `episode1.mp4` from `00:00–03:00`
2. Insert `ad30.mp4` (commercial break)
3. Resume `episode1.mp4` from `03:01–06:00`
4. Insert `bumper15.mp4` (station bumper)
5. Continue with next program segment

### Technical Requirements

- **Resume capability:** System must support resuming playback of partially played files
- **Seamless transitions:** Handle file-to-file transitions without gaps or audio/video sync issues
- **Timeline tracking:** Maintain precise timing for program segments and commercial breaks
- **State persistence:** Remember playback position across system restarts

## Dynamic Playlist Assembly

### Memory-Based Playlist Generation

The "playlist" should be generated **dynamically in memory**, not from hardcoded file paths:

- **Content library integration:** Pull selections from the content database
- **Rule-based selection:** Apply scheduling rules, content ratings, and timing constraints
- **Real-time assembly:** Generate playlist segments as needed, not pre-computed
- **Flexible injection:** Support for ads, bumpers, and promos based on various criteria

### Content Selection Logic

- **Program selection:** Choose episodes/movies based on schedule, genre, or rotation rules
- **Commercial insertion:** Inject ads based on timing, content rating, or business rules
- **Bumper integration:** Add station identification, promos, and transitions
- **Emergency handling:** Support for breaking news, special events, or technical overrides

## Development Priority

### Current Focus (Phase 1)

These streaming concepts are **parked for now**. Current development priorities are:

1. **Content Library Foundation**

   - Robust database schema for media metadata
   - Efficient content discovery and retrieval
   - Metadata enrichment and validation

2. **Domain Model & Architecture**

   - Clean separation of concerns (Domain, Application, Infrastructure)
   - Unit of Work pattern implementation
   - Repository pattern for data access

3. **FastAPI Integration**
   - RESTful API for content management
   - Web interface for library browsing
   - Authentication and authorization

### Future Focus (Phase 2)

Streaming engine development will resume once the library can provide program and commercial selections programmatically:

- **Content API:** Library exposes methods for content selection
- **Scheduling Engine:** Rules-based content scheduling
- **Streaming Pipeline:** Continuous playback implementation
- **Monitoring & Analytics:** Stream health and performance tracking

## Why This Was Deferred

This architectural intent is captured early to ensure the foundation is built with streaming requirements in mind. However, we prioritize **foundation stability** before dealing with the complexities of continuous stream orchestration.

The streaming pipeline represents one of the most technically challenging aspects of the system, involving real-time media processing, precise timing, and complex state management. By first establishing a solid content library and domain model, we ensure that when streaming development begins, we have:

- **Reliable data sources** for content selection
- **Clean architecture** that can support streaming requirements
- **Proven patterns** for handling complex business logic
- **Stable foundation** that won't require major refactoring

This approach reduces risk and ensures that streaming features are built on a solid, well-tested foundation rather than attempting to solve all problems simultaneously.
