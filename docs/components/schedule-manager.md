# Schedule Manager

## Overview

The **Schedule Manager** is RetroVue's programming and scheduling system. It's responsible for creating broadcast schedules, maintaining programming horizons, enforcing content rules, and ensuring time alignment across all channels.

Think of it as the "network programming department" of RetroVue—it knows what's supposed to air when, ensures content follows the right rules, and keeps the programming guide accurate and up-to-date.

## What This Document Is

This document describes the **architecture and behavior** of the Schedule Manager layer. It explains:

- What the Schedule Manager does and doesn't do
- How its components work together
- How it fits into RetroVue's overall architecture
- How other parts of the system should interact with it

This is **not** a code-level API reference—it's about understanding the system's design and responsibilities.

## Core Responsibilities

The Schedule Manager has four main jobs:

### 1. **Maintain EPG Horizon**

- **Build programming guide** that shows what's scheduled to air
- **Keep EPG current** with at least 2 days of future programming
- **Snap programming to :00/:30 boundaries** for clean schedule blocks
- **Provide human-readable schedule** for viewers and operators

### 2. **Maintain Playlog Horizon**

- **Track actual playback events** at segment level
- **Record absolute start/end times** for precise timing
- **Keep playlog current** with at least 2 hours of future events
- **Fill boundaries with ads/bumpers** to maintain schedule integrity

### 3. **Enforce Block Rules / Tone / Rotation**

- **Apply content policies** based on time of day, day of week, etc.
- **Ensure proper content rotation** to avoid repetition
- **Enforce tone restrictions** (family-friendly vs. adult content)
- **Manage commercial breaks** and promotional content placement

### 4. **Guarantee Time Alignment**

- **Synchronize all channels** to common time boundaries
- **Ensure seamless transitions** between content segments
- **Maintain precise timing** for live events and scheduled programming
- **Handle time zone consistency** across the system

### 5. **Broadcast Day Management**

- **06:00 → 06:00 broadcast day model** - Standard broadcast television scheduling
- **Rollover handling** - Manage programs that span the 06:00 boundary
- **Broadcast day classification** - Determine which broadcast day a timestamp belongs to
- **Carryover detection** - Identify content that continues across rollover
- **Schedule conflict prevention** - Ensure new broadcast day doesn't double-schedule carryover time

### Content Source Constraint

Schedule Manager may only schedule assets that are already marked canonical=True in Content Manager.

It is not allowed to fetch content directly from Plex, the filesystem, or any other external provider.

If Schedule Manager cannot find appropriate content for a slot, that is considered a scheduling failure, not permission to bypass Content Manager.

## Design Principles Alignment

The Schedule Manager follows RetroVue's architectural patterns:

- **Services** provide focused capabilities for scheduling operations
- **Orchestrators** coordinate complex multi-step scheduling processes
- **Authorities** maintain single sources of truth for schedule state
- **Unit of Work** ensures atomic operations for schedule updates

**Operational rule:** there is no such thing as a "partial schedule." If a schedule generation half-worked and half-failed, the correct interpretation is "it failed."

## System Boundaries

**What Schedule Manager DOES:**

- ✅ Creates and maintains broadcast schedules
- ✅ Manages EPG and playlog horizons
- ✅ Enforces content rules and policies
- ✅ Ensures time alignment across channels
- ✅ Provides schedule data to playback systems

**What Schedule Manager DOES NOT:**

- ❌ Perform actual media playback
- ❌ Spin up or manage Producer processes
- ❌ Handle real-time streaming or encoding
- ❌ Manage viewer sessions or connections

> **Key Principle:** Schedule Manager is the **upstream authority** for what should air when. Playback systems ask Schedule Manager for the current schedule—they don't generate schedules themselves.

## Core Data Model

All scheduling information is stored in SQLAlchemy models in `src/retrovue/domain/entities.py`. These represent the "source of truth" for what's scheduled to air.

### Channel

Represents a broadcast channel with its own schedule and programming.

**Key Properties:**

- `id` - Database primary key
- `uuid` - Stable external identifier
- `name` - Human-readable channel name
- `number` - Channel number for display
- `enabled` - Whether channel is active
- `timezone` - Channel's time zone for scheduling
- `epg_horizon_days` - How far ahead to maintain EPG
- `playlog_horizon_hours` - How far ahead to maintain playlog

**Relationships:**

- Has many EPGEntry records (scheduled programming)
- Has many PlaylogEvent records (actual playback)
- Has BlockRule/BlockPolicy records (content rules)

### BlockRule / BlockPolicy

Defines content rules and restrictions for scheduling.

**BlockRule Properties:**

- `id` - Database primary key
- `channel_id` - Which channel this applies to
- `day_of_week` - Day restriction (0=Monday, 6=Sunday)
- `start_time` - Time of day restriction (HH:MM format)
- `end_time` - End time restriction
- `content_type` - What type of content is allowed/restricted
- `tone_rating` - Content rating restrictions
- `rotation_rule` - How often content can repeat

**BlockPolicy Properties:**

- `id` - Database primary key
- `name` - Policy name for reference
- `description` - Human-readable policy description
- `rules` - JSON array of BlockRule IDs
- `priority` - Policy priority when multiple apply
- `enabled` - Whether policy is active

**Purpose:**
Block rules and policies do not schedule specific episodes.
They describe what is allowed to air in a given slot (tone, rating, category, rotation rules, etc.) so the ScheduleOrchestrator can pick compliant assets from Content Manager.

### EPGEntry (30-min aligned, human-facing)

Represents scheduled programming in the Electronic Program Guide.

**Key Properties:**

- `id` - Database primary key
- `channel_id` - Which channel this is for
- `title` - Program title
- `description` - Program description
- `start_time` - Scheduled start (snapped to :00/:30)
- `end_time` - Scheduled end (snapped to :00/:30)
- `duration_minutes` - Program length
- `content_type` - Type of content (episode, movie, commercial, etc.)
- `tone_rating` - Content rating
- `asset_id` - Link to content asset (if applicable)
- `series_id` - Link to series (if applicable)
- `episode_number` - Episode number within series

**Relationships:**

- Belongs to Channel
- Links to Asset (the actual media file)
- Links to Episode/Series (logical content grouping)

EPGEntry is for humans and guide surfaces.
It answers 'what's on at 9PM Thursday?'
It is aligned to clean half-hour boundaries and may be coarse at the sub-segment level.

### PlaylogEvent (segment-level, absolute_start / absolute_end)

Represents actual playback events with precise timing.

**Key Properties:**

- `id` - Database primary key
- `channel_id` - Which channel this is for
- `asset_id` - The media file being played
- `absolute_start` - Precise start timestamp
- `absolute_end` - Precise end timestamp
- `segment_type` - Type of segment (content, commercial, bumper, etc.)
- `duration_ms` - Actual duration in milliseconds
- `epg_entry_id` - Link to scheduled EPG entry
- `playback_status` - Current status (scheduled, playing, completed, failed)

**Relationships:**

- Belongs to Channel
- Links to Asset (the media being played)
- Links to EPGEntry (the scheduled programming)

PlaylogEvent is for machines and playout.
It answers 'what, to the millisecond, should be on-air right now?'
It must include absolute_start and absolute_end timestamps so ChannelManager can drop a viewer into the middle of the current segment at the correct offset.

## Major Services

### ScheduleService

**File:** `src/retrovue/schedule_manager/schedule_service.py`

**Role:** The single source of truth for schedule state and horizons.

**Design Pattern:** Authority + Service/Capability Provider

**Key Responsibilities:**

- Generate and maintain EPG entries
- Create and track playlog events
- Enforce block rules and content policies
- Provide current schedule queries
- Manage schedule horizons (EPG ≥ 2 days, Playlog ≥ 2 hours)
- Handle schedule updates and corrections

**Important Behaviors:**

- **Horizon maintenance** - Always keeps EPG 2+ days ahead, playlog 2+ hours ahead
- **Time alignment** - All schedules snapped to :00/:30 boundaries
- **Rule enforcement** - Applies all active block rules and policies
- **Atomic updates** - All schedule changes are atomic (commit/rollback)
- **Authority over schedule** - Nothing else should directly modify schedule state
- **Time authority compliance** - All time calculations, including absolute_start / absolute_end timestamps, must use MasterClock. ScheduleService is not allowed to call system time directly.

**Authority Rule:**
ScheduleService is the single authority over EPGEntry, PlaylogEvent, and schedule state.
No other part of the system (CLI, API, playback systems, runtime) may write or mutate these records directly.
All schedule generation, updates, corrections, and horizon management must go through ScheduleService.
The rest of the system must not write schedule data directly or silently patch horizons. All modifications go through ScheduleService inside a Unit of Work.

**Broadcast Day Authority:**
ScheduleService is the single authority over broadcast day logic and rollover handling.
No other component may compute broadcast day labels or handle rollover scenarios.
All broadcast day operations must go through ScheduleService methods.

### ScheduleOrchestrator

**File:** `src/retrovue/schedule_manager/schedule_orchestrator.py`

**Role:** Orchestrator that rolls horizons forward and maintains schedule continuity.

**Design Pattern:** Orchestrator

**Key Responsibilities:**

- **Roll EPG horizon forward** as time progresses
- **Generate new playlog events** based on EPG schedule
- **Fill time boundaries** with ads, bumpers, and promotional content
- **Handle schedule corrections** and last-minute changes
- **Maintain schedule continuity** across time boundaries
- **Coordinate with Content Manager** for eligible content
- **No runtime control** – ScheduleOrchestrator never starts or stops Producer instances. It only prepares future schedule horizons.

**High-Level Flow:**

1. **Check current horizons** - Are EPG and playlog still adequate?
2. **Generate new EPG entries** - Create programming for upcoming time slots
3. **Apply block rules** - Ensure content follows all policies
4. **Create playlog events** - Convert EPG schedule to precise playback events
5. **Fill boundaries** - Add commercials, bumpers, station IDs
6. **Update horizons** - Extend EPG and playlog as needed

**Key Behaviors:**

- **Continuous operation** - Runs periodically to maintain horizons
- **Content coordination** - Works with Content Manager for eligible assets
- **Rule compliance** - Ensures all content follows channel policies
- **Time precision** - Maintains exact timing for seamless playback
- **Error handling** - Gracefully handles content unavailability
- **No direct playout control** – It does not tell a channel to go live. It only plans.

## Invariants

The Schedule Manager maintains several critical invariants:

### EPG ≥ 2 days ahead, Playlog ≥ 2 hours ahead

- **EPG horizon** must always extend at least 2 days into the future
- **Playlog horizon** must always extend at least 2 hours into the future
- **Automatic extension** when horizons become insufficient
- **Graceful degradation** if content becomes unavailable

### EPG snapped to :00/:30 blocks

- **All EPG entries** start and end on :00 or :30 minute boundaries
- **30-minute minimum** programming blocks
- **Clean transitions** between different content types
- **Consistent scheduling** across all channels

### Playlog events have absolute_start/absolute_end and fill to boundary

- **Precise timing** with absolute timestamps for all events
- **No gaps** - every second is accounted for in the playlog
- **Boundary filling** - ads, bumpers, and promotional content fill any gaps
- **Seamless playback** with exact timing information

## Boundaries

### ChannelManager/Producer are consumers, not schedulers

**What ChannelManager/Producer DO:**

- ✅ Ask Schedule Manager "what is airing right now + offset?"
- ✅ Execute playback based on schedule data
- ✅ Report playback status back to Schedule Manager
- ✅ Handle real-time streaming and encoding

**What ChannelManager/Producer DO NOT:**

- ❌ Generate schedules or programming
- ❌ Make scheduling decisions
- ❌ Modify EPG or playlog data
- ❌ Enforce content rules or policies

### ScheduleManager does not do playback, does not spin Producers

**What Schedule Manager DOES:**

- ✅ Provide schedule data to playback systems
- ✅ Track what should be playing when
- ✅ Maintain programming horizons
- ✅ Enforce content rules and policies

**What Schedule Manager DOES NOT:**

- ❌ Start or stop Producer processes
- ❌ Handle real-time streaming
- ❌ Manage viewer connections
- ❌ Perform actual media playback

### MasterClock is the only time source

✅ ScheduleService uses MasterClock to assign absolute_start / absolute_end timestamps for PlaylogEvents

✅ ChannelManager uses MasterClock to determine 'where in the current PlaylogEvent should we start the viewer?'

❌ No component is allowed to compute timing from datetime.now() directly

❌ No component is allowed to drift its own local notion of current time

## Future Consumers

### ChannelManager asks "what is airing right now + offset?"

ChannelManager will query Schedule Manager for:

- **Current programming** - What should be playing right now
- **Upcoming content** - What's scheduled next (with offset)
- **Playlog events** - Precise timing for seamless transitions
- **Content metadata** - Asset information for playback

**Query Pattern:**

```python
# Get current programming
current = schedule_service.get_current_programming(channel_id)

# Get next 3 hours of programming
upcoming = schedule_service.get_upcoming_programming(
    channel_id,
    hours_ahead=3
)

# Get precise playlog events
events = schedule_service.get_playlog_events(
    channel_id,
    start_time=now,
    end_time=now + timedelta(hours=2)
)
```

### ProgramManager uses ScheduleManager for visibility, not for schedule control

ProgramManager will use Schedule Manager for:

- **Schedule reporting** - What's been scheduled and when
- **Content usage tracking** - How often assets are used
- **Performance metrics** - Schedule adherence and timing
- **Audit trails** - What content aired when

**What ProgramManager DOES NOT do:**

- ❌ Modify or generate schedules
- ❌ Override block rules or tone policies
- ❌ Patch horizons directly
- ❌ Force airings into the Playlog

## Key Architectural Principles

### Single Responsibility

Each component has one clear purpose:

- **ScheduleService** - Schedule state authority
- **ScheduleOrchestrator** - Schedule generation orchestration
- **BlockRule/BlockPolicy** - Content rule enforcement
- **EPGEntry** - Human-readable programming guide
- **PlaylogEvent** - Precise playback tracking

### Time Alignment

All scheduling follows consistent time boundaries:

- **30-minute blocks** for EPG entries
- **Precise timestamps** for playlog events
- **Synchronized channels** across the system
- **Consistent time zones** for all operations

### Authority Boundaries

- **ScheduleService** is the authority over schedule state
- **ScheduleOrchestrator** coordinates schedule generation
- **Nothing else** should directly modify schedule data

### Horizon Management

- **EPG horizon** - Always 2+ days ahead
- **Playlog horizon** - Always 2+ hours ahead
- **Automatic extension** when horizons become insufficient
- **Graceful degradation** if content unavailable

## Broadcast Day Model

RetroVue uses a broadcast day model that runs from 06:00 → 06:00 local channel time instead of midnight → midnight. This is the standard model used by broadcast television and ensures proper handling of programs that span the 06:00 rollover.

### Key Concepts

- **Broadcast day starts at 06:00:00 local channel time**
- **Broadcast day ends just before 06:00:00 the next local day**
- **Example:** 2025-10-24 23:59 local and 2025-10-25 02:00 local are the SAME broadcast day
- **Example:** 2025-10-25 05:30 local still belongs to 2025-10-24 broadcast day

### ScheduleService Broadcast Day Methods

#### `broadcast_day_for(channel_id, when_utc) -> date`

Given a UTC timestamp, return the broadcast day label (a date) for that channel.

**Steps:**

1. Convert when_utc (aware datetime in UTC) to channel-local using MasterClock.to_channel_time()
2. If local_time.time() >= 06:00, broadcast day label is local_time.date()
3. Else, broadcast day label is (local_time.date() - 1 day)
4. Return that label as a date object

#### `broadcast_day_window(channel_id, when_utc) -> tuple[datetime, datetime]`

Return (start_local, end_local) for the broadcast day that contains when_utc, in channel-local tz, tz-aware datetimes.

- start_local = YYYY-MM-DD 06:00:00
- end_local = (YYYY-MM-DD+1) 05:59:59.999999

#### `active_segment_spanning_rollover(channel_id, rollover_start_utc)`

Given the UTC timestamp for rollover boundary (which is local 06:00:00), return info about any scheduled content that STARTED BEFORE rollover and CONTINUES AFTER rollover.

**Returns:**

- None if nothing is carrying over
- Otherwise return a dict with:
  - program_id: identifier/title/asset ref
  - absolute_start_utc: aware UTC datetime
  - absolute_end_utc: aware UTC datetime
  - carryover_start_local: tz-aware local datetime at rollover start
  - carryover_end_local: tz-aware local datetime when the asset actually ends

### Rollover Handling

A broadcast day schedule may legally include an item whose end is AFTER the 06:00 turnover, if it began before 06:00. The next broadcast day must treat that carried segment as already in progress; it cannot schedule new content under it until it finishes.

**Example: HBO Movie 05:00–07:00**

- Movie starts at 05:00 local (Day A)
- Movie continues past 06:00 rollover
- Movie ends at 07:00 local (Day B)
- Day B's schedule must account for 06:00–07:00 being occupied by carryover

### Critical Rules

**ChannelManager never snaps playback at 06:00.**

**AsRunLogger may split one continuous asset across two broadcast days in reporting. That's expected, not an error.**

## Summary

The Schedule Manager is RetroVue's programming and scheduling system. It:

- **Creates** broadcast schedules with proper time alignment
- **Maintains** EPG and playlog horizons for continuous operation
- **Enforces** content rules and policies for appropriate programming
- **Provides** schedule data to playback systems
- **Ensures** seamless transitions and precise timing
- **Manages** broadcast day logic and rollover handling

It follows RetroVue's architectural patterns and provides the scheduling foundation that playback systems depend on. The system maintains strict time boundaries and content rules while providing flexible interfaces for different types of programming.

**Remember:** Schedule Manager is about **programming and scheduling**—not playback, streaming, or runtime operations. It tells other systems what should air when, but doesn't handle the actual media playback.
