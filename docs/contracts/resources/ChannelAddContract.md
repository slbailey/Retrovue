## Channel Add Contract

## Purpose

Define the behavioral contract for creating a new broadcast channel in RetroVue.

---

## Command Shape

```
retrovue channel create \
  --name <string> \
  --grid-size-minutes <15|30|60> \
  [--grid-offset-minutes <int>] \
  [--broadcast-day-start <HH:MM>] \
  [--active | --inactive] \
  [--json] [--test-db]
```

### Parameters

- `--name` (required): Human-facing name, unique.
- `--grid-size-minutes` (required): One of 15, 30, 60.
- `--grid-offset-minutes` (optional, default 0): Alignment offset for grid snapping.
- `--broadcast-day-start` (optional, default `06:00`): Programming day anchor (HH:MM).
- `--active` / `--inactive` (optional): Initial active state. Default `--active`.
- `--json` (optional): Machine-readable output.
- `--test-db` (optional): Use isolated test database session.

---

## Safety Expectations

- Creates exactly one `Channel` row.
- Idempotent only with identical parameters and unique name constraint handling.
- No side effects outside the database.
- `--test-db` MUST isolate from production data.

---

## Output Format

### Human-Readable

```
Channel created:
  ID: 7
  Name: RetroToons
  Grid Size (min): 30
  Grid Offset (min): 0
  Broadcast day start: 06:00
  Active: true
  Created: 2025-01-01 12:00:00
```

### JSON

```json
{
  "status": "ok",
  "channel": {
    "id": 7,
    "name": "RetroToons",
    "grid_size_minutes": 30,
    "grid_offset_minutes": 0,
    "broadcast_day_start": "06:00",
    "is_active": true,
    "version": 1,
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": null
  }
}
```

---

## Exit Codes

- `0`: Channel created successfully.
- `1`: Validation failed (name not unique, invalid timezone or parameters), DB failure, or `--test-db` session unavailable.

---

## Behavior Contract Rules (B-#)

- **B-1:** Name MUST be unique (case-insensitive) across channels.
- **B-2:** Timezone MUST be a valid IANA timezone.
- **B-3:** `grid-size-minutes` MUST be one of 15, 30, 60.
- **B-4:** Grid size and offset MUST be integers; offset may be negative or positive as allowed by scheduling policy.
- **B-5:** `rollover-minutes` MUST be an integer in the 0–1439 range.
- **B-6:** `--inactive` sets `is_active=false`; otherwise default `true`.
- **B-7:** `--json` MUST return valid JSON with the created channel.
- **B-8:** The command MUST be deterministic; on duplicate name, MUST exit 1 with a helpful error.
- **B-9:** `--test-db` MUST behave identically in output shape and exit codes.
- **B-10:** Creation runs full Channel validation; violations fail the operation.

Effective-dated policy and optimistic locking begin after creation; record initializes with `version=1`.

---

## Data Contract Rules (D-#)

- **D-1:** Record MUST be persisted in `broadcast_channels` with the provided fields.
- **D-2:** Timestamps MUST be set correctly (UTC with timezone awareness).
- **D-3:** Name uniqueness MUST be enforced at the DB or application layer.
- **D-4:** No auxiliary rows are created.
- **D-5:** Test DB MUST NOT read/write production tables.
- **D-6:** New records initialize `version` to 1.

---

## Tests

Planned tests:

- tests/contracts/test_channel_add_contract.py::test_channel_create\_\_help_flag
- tests/contracts/test_channel_add_contract.py::test_channel_create\_\_success_human_output
- tests/contracts/test_channel_add_contract.py::test_channel_create\_\_success_json_output
- tests/contracts/test_channel_create_contract.py::test_channel_create\_\_duplicate_name_fails
- tests/contracts/test_channel_create_contract.py::test_channel_create\_\_invalid_timezone_fails
- tests/contracts/test_channel_create_contract.py::test_channel_create\_\_grid_size_validation
- tests/contracts/test_channel_create_contract.py::test_channel_create\_\_test_db_isolation

---

## Error Conditions

- Duplicate name: exit 1, "Error: Channel name already exists."
- Invalid timezone: exit 1, "Error: Invalid IANA timezone."
- Grid size invalid: exit 1, "Error: grid-size-minutes must be one of 15, 30, 60."

---

## See also

- [Channel](../../domain/Channel.md)
- [Channel Update](ChannelUpdateContract.md)
- [Channel List](ChannelListContract.md)
- [Channel Show](ChannelShowContract.md)
- [Channel Delete](ChannelDeleteContract.md)
- [CLI Data Guarantees](cross-domain/CLI_Data_Guarantees.md)
