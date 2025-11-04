## Channel Update Contract

## Purpose

Define the behavioral contract for updating an existing broadcast channel.

---

## Command Shape

```
retrovue channel update --id <int> \
  [--version <int>] \
  [--name <string>] \
  [--timezone <IANA>] \
  [--grid-size-minutes <15|30|60>] \
  [--grid-offset-minutes <int>] \
  [--rollover-minutes <int>] \
  [--effective-date <YYYY-MM-DD>] \
  [--active | --inactive] \
  [--json] [--test-db]
```

### Parameters

- `--id` (required): Channel integer identifier.
- `--version` (recommended): Optimistic-lock precondition. Required when API enforces conflict detection.
- Other flags optional; only provided fields are changed.
- `--effective-date` (optional): Required when changing `--timezone` or `--rollover-minutes`; defines the date from which rebuilds apply.
- `--json` (optional): Machine-readable output.
- `--test-db` (optional): Use isolated test database session.

---

## Safety Expectations

- Updates a single row; no cross-entity side effects.
- Validation mirrors creation rules for modified fields.
- `--test-db` MUST isolate from production.

---

## Output Format

### Human-Readable

```
Channel updated:
  ID: 7
  Name: RetroToons
  Timezone: America/Chicago
  Grid Size (min): 30
  Grid Offset (min): 0
  Rollover (min): 360
  Active: true
  Updated: 2025-01-02 10:00:00
```

### JSON

```json
{
  "status": "ok",
  "channel": {
    "id": 7,
    "name": "RetroToons",
    "timezone": "America/Chicago",
    "grid_size_minutes": 30,
    "grid_offset_minutes": 0,
    "rollover_minutes": 360,
    "is_active": true,
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-02T10:00:00Z"
  },
  "impacted_entities": {
    "schedule_templates": { "count": 0, "ids": [] },
    "schedule_days": { "count": 2, "ids": [3456, 3457] }
  }
}
```

---

## Exit Codes

- `0`: Channel updated successfully.
- `1`: Channel not found, validation failed, conflict (stale `--version`), DB failure, or `--test-db` session unavailable.

---

## Behavior Contract Rules (B-#)

- **B-1:** The channel identified by `--id` MUST exist; else exit 1 with error.
- **B-2:** Timezone MUST be valid IANA if provided.
- **B-3:** `grid-size-minutes` MUST be one of 15, 30, 60 if provided.
- **B-4:** Offsets and rollover MUST be integers and policy-compliant if provided.
- **B-5:** `--inactive` sets `is_active=false`; `--active` sets `true`.
- **B-6:** Partial updates MUST only affect specified fields.
- **B-7:** `--json` returns valid JSON with updated record.
- **B-8:** Output MUST be deterministic.
- **B-9:** When `--timezone` or `--rollover-minutes` are provided, `--effective-date` MUST also be provided; system triggers rebuilds from that date forward.
- **B-10:** If `--version` is provided and does not match current, update MUST fail with a conflict message.
- **B-11:** When `--effective-date`, `--timezone`, or `--rollover-minutes` are used, the JSON response MUST include `impacted_entities` with counts and IDs for affected `ScheduleTemplate`/`ScheduleDay`.

---

## Data Contract Rules (D-#)

- **D-1:** Only modified fields change; others remain intact.
- **D-2:** Timestamps reflect update time.
- **D-3:** Name uniqueness enforced if name changes.
- **D-4:** Test DB isolation preserved.
- **D-5:** Version increments by 1 on successful update; no reset.
- **D-6:** Effective-dated changes produce rebuild markers from the specified date.

---

## Tests

Planned tests:

- tests/contracts/test_channel_update_contract.py::test_channel_update__help_flag
- tests/contracts/test_channel_update_contract.py::test_channel_update__success_human_output
- tests/contracts/test_channel_update_contract.py::test_channel_update__success_json_output
- tests/contracts/test_channel_update_contract.py::test_channel_update__not_found
- tests/contracts/test_channel_update_contract.py::test_channel_update__validation_errors
- tests/contracts/test_channel_update_contract.py::test_channel_update__test_db_isolation

---

## Error Conditions

- Not found: exit 1, "Error: Channel '7' not found."
- Invalid timezone/grid values: exit 1 with validation messages.
- Conflict (optimistic lock): exit 1; JSON error includes `{ "status": "error", "error": "conflict", "expected_version": N, "actual_version": M }`.

---

## See also

- [Channel Add](ChannelAddContract.md)
- [Channel List](ChannelListContract.md)
- [Channel Show](ChannelShowContract.md)
- [Channel Delete](ChannelDeleteContract.md)
 - [Channel](../../domain/Channel.md)

