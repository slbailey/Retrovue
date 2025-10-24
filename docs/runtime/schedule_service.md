# Schedule Service

The ScheduleService is the single source of truth for all schedule state in RetroVue. It owns the EPG Horizon and Playlog Horizon data, and is the only interface allowed to create or modify schedule entries.

## Key Responsibilities

- Maintain EPG Horizon (≥ 2 days ahead)
- Maintain Playlog Horizon (≥ 2 hours ahead)
- Enforce block rules and content policies
- Provide read methods for current and future programming
- Ensure time alignment across all channels
- **Manage broadcast day logic and rollover handling**

## Authority Rule

ScheduleService is the single authority over EPGEntry, PlaylogEvent, and schedule state. No other part of the system may write or mutate these records directly. All schedule generation, updates, corrections, and horizon management must go through ScheduleService. The rest of the system must not write schedule data directly or silently patch horizons. All modifications go through ScheduleService inside a Unit of Work.

## Design Principles

- All operations are atomic (Unit of Work)
- EPG entries are snapped to :00/:30 boundaries
- Playlog events have precise absolute_start/absolute_end timestamps
- Schedule state is always consistent and valid
- **Broadcast day boundaries are accounting/reporting boundaries, NOT playback boundaries**

## Broadcast Day Model (06:00 → 06:00)

RetroVue uses a broadcast day model that runs from 06:00 → 06:00 local channel time instead of midnight → midnight. This is the standard model used by broadcast television and ensures proper handling of programs that span the 06:00 rollover.

### Key Concepts

- **Broadcast day starts at 06:00:00 local channel time**
- **Broadcast day ends just before 06:00:00 the next local day**
- Example: 2025-10-24 23:59 local and 2025-10-25 02:00 local are the SAME broadcast day
- Example: 2025-10-25 05:30 local still belongs to 2025-10-24 broadcast day

### ScheduleService Methods

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

## Critical Rules

**ChannelManager never snaps playback at 06:00.**

**AsRunLogger may split one continuous asset across two broadcast days in reporting. That's expected, not an error.**

## Implementation Notes

- All APIs ALWAYS accept or return tz-aware datetimes
- If something naive is passed in, raise ValueError
- These APIs MUST use MasterClock for timezone conversion
- No direct datetime.now() or manual tz math is allowed
- Use the already-implemented MasterClock.to_channel_time()

## Testing

Use the `retrovue test broadcast-day-alignment` command to validate broadcast day logic and rollover handling. This test validates the HBO-style 05:00–07:00 scenario and ensures proper broadcast day classification.
