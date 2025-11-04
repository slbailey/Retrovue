## MasterClock Contract

## Purpose

Define the runtime contract for MasterClock — the single source of truth for time within RetroVue. Aligns with local-time methodology: inputs/outputs presented in local system time; storage and inter-component exchange in UTC.

---

## Scope

Applies to runtime components (ScheduleService, ChannelManager, ProgramDirector, AsRunLogger) and CLI test commands that validate MasterClock behavior.

---

## Interface (authoritative)

- `now_utc() -> datetime` (tz-aware UTC)
- `now_local() -> datetime` (tz-aware, system local timezone)
- `to_local(dt_utc: datetime) -> datetime` (UTC aware → local aware)
- `to_utc(dt_local: datetime) -> datetime` (local aware → UTC aware)
- `seconds_since(dt: datetime) -> float` (non-negative offset; clamps future to 0.0)

Notes:
- No per-channel timezone. “Local” means system local timezone.
- All datetimes are tz-aware; naive datetimes are rejected.

---

## Behavior Rules (MC-#)

- MC-001: All returned datetimes are tz-aware. UTC is authoritative for storage and exchange.
- MC-002: Time monotonicity — `now_utc()` never appears to go backward within a process.
- MC-003: `seconds_since(dt)` never returns negative values; future timestamps clamp to 0.0.
- MC-004: Naive datetimes passed to conversion methods raise ValueError.
- MC-005: Local time is the system timezone; no per-channel timezone parameters.
- MC-006: Passive design — no timers, listeners, or event scheduling APIs.
- MC-007: Single source of “now” — runtime components must not call `datetime.now()` directly.

---

## Integration Guarantees

- ScheduleService: uses `now_utc()` and converts to local once; applies channel policy (grid, offsets, broadcast_day_start) without per-channel tz.
- ChannelManager/ProgramDirector: use `now_utc()` for offsets/timestamps; local only for operator display.
- AsRunLogger: logs UTC; may include local display time via `now_local()` or `to_local()`.

---

## CLI Test Contracts

### `retrovue test masterclock`

- Purpose: sanity-check core MasterClock behaviors.
- Exit codes:
  - `0`: All checks pass
  - `1`: Infra or contract violation
- JSON (authoritative):
```json
{
  "status": "ok",
  "uses_masterclock_only": true,
  "tzinfo_ok": true,
  "monotonic_ok": true,
  "naive_timestamp_rejected": true,
  "max_skew_seconds": 0.005
}
```

### `retrovue test masterclock-scheduler-alignment`

- Purpose: validates that ScheduleService obtains time only via MasterClock and preserves broadcast-day boundary logic.
- Exit codes: `0` on success, `1` on violation.
- JSON includes: `{ "status":"ok", "scheduler_uses_masterclock": true }`.

---

## Tests (planned)

- docs/tests/masterclock.md (runtime test plan)
- tests to assert:
  - tz-aware outputs (MC-001)
  - non-negative `seconds_since` (MC-003)
  - naive datetime rejection (MC-004)
  - no direct `datetime.now()` usage in runtime code (MC-007)

---

## See also

- [ScheduleService](../../runtime/schedule_service.md)
- [MasterClock (runtime doc)](../../runtime/clock.md)
- [Channel Contract](ChannelContract.md)


