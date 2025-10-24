# MasterClock

_Provides a unified, timezone-aware time authority for all runtime components._

## Overview

The **MasterClock** is RetroVue's internal runtime authority for "now." It ensures every component uses a consistent source of time instead of calling `datetime.now()` directly.

MasterClock handles timezone conversions per channel and provides stable UTC as the system's master reference. It does not manage events, scheduling, or external synchronization.

Think of it as the "time authority" of RetroVue—it knows what time it is everywhere and ensures all components use the same time reference.

## What This Document Is

This document describes the **architecture and behavior** of MasterClock. It explains:

- What MasterClock does and doesn't do
- How it provides consistent time across the system
- How it fits into RetroVue's overall architecture

This is **not** a code-level API reference—it's about runtime responsibilities and boundaries.

## Core Responsibilities

### 1. **Authoritative Time Source**

- Provides the single source of truth for "now" across the entire system
- Ensures all components use the same time reference with stable UTC as master
- Handles timezone conversions for different channels

### 2. **Timezone Management**

- Converts times between different timezones for multi-channel operations
- Handles timezone changes (DST transitions, etc.) using built-in zoneinfo module
- Provides channel-specific time information

### 3. **Time Consistency**

- Ensures all components use MasterClock instead of system time
- Maintains consistent time across all system components

## Design Principles Alignment

MasterClock follows RetroVue's architectural patterns as an **Authority** component. It is the single source of truth for time, and all other components must defer to it for time-based operations.

**Invariant:** All time-based operations in RetroVue must use MasterClock. No component may call system time directly.

## Implementation Interface

MasterClock provides a simple, practical interface for time operations:

```python
class MasterClock:
    def now_utc(self) -> datetime:
        """Get current UTC time as the system's master reference"""
        ...

    def now_local(self, channel_tz: str | None = None) -> datetime:
        """Get current local time for a channel's timezone"""
        ...

    def seconds_since(self, dt: datetime) -> float:
        """Calculate seconds elapsed since a given datetime"""
        ...
```

### Time Information Structure

MasterClock provides simple time information:

- UTC time (authoritative reference)
- Local time (timezone-adjusted)
- Timezone conversions using built-in zoneinfo module
- System UTC is authoritative; conversions are derived from that

## Usage Example

Here's how another component (like ScheduleService) would call MasterClock:

```python
from retrovue.runtime.master_clock import MasterClock

class ScheduleService:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def get_playout_plan_now(self, channel_id: str, at_station_time: datetime) -> List[Dict[str, Any]]:
        # Get current UTC time from MasterClock
        now_utc = self.clock.now_utc()

        # Get channel-specific local time
        channel_time = self.clock.now_local(channel_tz="America/New_York")

        # Calculate time offset for mid-program joins
        if at_station_time:
            offset_seconds = self.clock.seconds_since(at_station_time)

        # Build playout plan using MasterClock time
        return self._build_playout_plan(channel_id, now_utc, offset_seconds)
```

## Key Integration Points

### ScheduleService

- Builds schedule horizons and timestamps using MasterClock
- EPG entries and Playlog events use MasterClock time as authoritative reference
- Must not compute time independently

### ChannelManager

- Calculates playback offsets when a viewer joins mid-program
- Asks MasterClock for "now" when determining playout offsets
- Never calls system time directly

### ProgramDirector

- Keeps multiple channels in sync and timestamps global overrides
- Uses MasterClock for system-wide coordination and emergency overrides

### AsRunLogger

- Timestamps all logged playout events using MasterClock
- Provides audit trail with synchronized timestamps

## Time Consistency Model

MasterClock uses system time as the authoritative source:

- System UTC is the master reference
- All timezone conversions are derived from system UTC
- No external synchronization in v0.1
- Ensures all components use the same time reference

## Timezone Handling

RetroVue supports channels in different timezones:

- Each channel can operate in its local timezone
- MasterClock handles conversions between timezones using built-in zoneinfo module
- Handles timezone changes (DST transitions, timezone updates, channel migration)
- Simple timezone conversion without external dependencies

## Runtime Data Model

MasterClock maintains these runtime fields:

- **Current Time**: Authoritative "now" timestamp
- **Timezone Cache**: Cached timezone information using zoneinfo module
- **System UTC**: Master reference time
- **Channel Timezones**: Per-channel timezone settings

## Hard Boundaries

**MasterClock IS allowed to:** Provide authoritative time for the entire system, handle timezone conversions and timezone changes, and cache timezone information for performance using zoneinfo module.

**MasterClock IS NOT allowed to:** Make content decisions or scheduling decisions, manage viewer sessions or channel operations, access external content sources, schedule or trigger time-based events (belongs to scheduler daemon), or synchronize with external time sources (not in v0.1).

## Failure and Recovery Model

If timezone conversions fail, MasterClock can fall back to UTC operations, refresh the timezone cache using zoneinfo module, and handle errors simply without complex recovery.

If system time becomes unreliable, MasterClock continues operating with available time and provides simple time validation without external dependencies.

## Performance Considerations

MasterClock optimizes timezone operations by caching timezone objects for fast conversions using zoneinfo module, lazy loading timezone information, and providing simple memory management for timezone cache.

## Future Expansion

Later versions of RetroVue may add optional NTP/PTP sync for external time synchronization and broadcast-grade precision, frame-level precision for ultra-high precision timing, event coordination hooks for integration with scheduler daemon, and advanced timecode support for professional broadcast timecode integration.

These features will be added as optional enhancements while maintaining the simple v0.1 interface.

## Summary

MasterClock is RetroVue's internal time authority for v0.1. It provides the single source of truth for "now" across the entire system, handles timezone conversions for multi-channel operations, and ensures all components use consistent time.

**Remember:** MasterClock is about **time authority and consistency**—not content, scheduling, or broadcast decisions. It provides the temporal foundation that enables all other RetroVue components to operate with consistent time.

**Broadcast Day Boundary:** MasterClock does NOT know about broadcast days or 06:00 rollover logic. It only provides time conversion and calculation services. ScheduleService is responsible for broadcast day classification and rollover handling.

In practical terms: MasterClock is the reliable time reference. It doesn't decide what's on the log or when it should air — it ensures that when something is supposed to happen, it happens at the right time, with all components using the same time reference.

---

**Note:** This class will live in `src/retrovue/runtime/clock.py`.
