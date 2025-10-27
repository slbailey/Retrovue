# Channel manager

## Purpose

ChannelManager is responsible for the live runtime of a Channel.

It decides when to launch ffmpeg, what to feed ffmpeg, and when to tear it down.

**Critical Rule**: ChannelManager may only operate on assets where `state == 'ready'` and `approved_for_broadcast == true`.

## Core model / scope

- One ChannelManager per Channel.
- It tracks active viewer count for that Channel.
- It holds (or can fetch) the Channel configuration: Producer instance, playout enrichers, branding rules.
- It is aware of scheduling state via the Playlog horizon / EPG context.

## Contract / interface

ChannelManager must be able to:

- `tune_in()`: increment viewer count. If this was the first viewer, prepare stream.
- `tune_out()`: decrement viewer count. If this was the last viewer, stop stream.
- Ask the Producer for "what is airing right now + offset" and generate a playout plan.
- Run playout-scope enrichers in configured priority order.
- Start an ffmpeg Producer (or equivalent) using the enriched playout plan.
- Stream output to all current viewers.
- Report health/status of the active ffmpeg process.

**Asset Eligibility**: ChannelManager queries only assets with `state='ready'` and `approved_for_broadcast=true`. Assets in `new`, `enriching`, or `retired` states are never considered for playout.

## Execution model

1. First viewer triggers:
   - Query schedule: what should be on this Channel at this exact wall-clock time?
   - ChannelManager asks ScheduleService/Playlog for the PlaylogEvent that's active right now. Each PlaylogEvent references asset_uuid. ChannelManager will refuse to build a playout plan if that asset is not in state='ready' AND approved_for_broadcast=true.
   - Call Producer to build the base playout plan from ready assets only.
   - Apply playout enrichers.
   - Launch ffmpeg with that plan.
2. Subsequent viewers attach to the same stream fanout.
3. Last viewer leaving triggers:
   - Graceful teardown of ffmpeg.
   - ChannelManager remains idle, but the Channel timeline itself keeps logically advancing in the database.

**Asset State Enforcement**: The Producer only considers assets with `state='ready'` and `approved_for_broadcast=true` when building playout plans. Assets in other states are invisible to the runtime layer.

## Failure / fallback behavior

- If a playout enricher fails, ChannelManager uses the last valid version of the playout plan without that enricher.
- If ffmpeg crashes mid-stream, ChannelManager can attempt to rebuild the current playout plan and relaunch.
- Failure to launch should be logged and surfaced to operators.

## Naming rules

- "Channel" is the persistent logical feed.
- "ChannelManager" is the runtime controller for that Channel.
- "viewer count" means connected consumers for that Channel right now, not general audience metrics.

See also:

- [Playout pipeline](../domain/PlayoutPipeline.md)
- [Producer lifecycle](ProducerLifecycle.md)
- [As-run logging](AsRunLogging.md)
  \_For CLI commands, refer to the [CLI contract](../contracts/README.md).
