_Related: [Architecture: Data flow](../architecture/DataFlow.md) • [Runtime: Channel manager](ChannelManager.md) • [Runtime: As-run logging](AsRunLogging.md)_

# Master clock

## Purpose

Provide a single source of truth for "now" inside RetroVue.

## Core model / scope

- The MasterClock is the authority for current wall-clock time in the system.
- All scheduling, playout, logging, and ChannelManager decisions must query MasterClock instead of calling system time directly.

## Contract / interface

MasterClock exposes:

- `now()` → timestamp used for:
  - figuring out what should currently be airing
  - choosing join offsets into a segment
  - labeling as-run log entries
- (optional) monotonic / health info for debugging drift

## Execution model

- Scheduler uses MasterClock to advance EPG / Playlog horizons.
- Producer uses MasterClock to figure out "what should be airing right now".
- ChannelManager uses MasterClock to timestamp transitions.
- As-run log uses MasterClock to record what actually aired.

## Failure / fallback behavior

- If MasterClock is unavailable or returns nonsense, downstream services cannot safely infer "what is on right now." This is considered critical.
- This condition must be surfaced to operators.

## Naming rules

- "MasterClock" is not ffmpeg's framerate clock. It is the broadcast facility wall clock for RetroVue logic.

See also:

- [Data flow](../architecture/DataFlow.md)
- [Channel manager](ChannelManager.md)
- [As-run logging](AsRunLogging.md)
