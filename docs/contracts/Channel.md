# Channel

## Purpose

Define the behavioral contract for channel management operations in RetroVue. This contract ensures safe channel configuration, enricher attachment, and channel listing operations.

---

## Command Shape

```
retrovue channel list [--json] [--test-db]
retrovue channel attach-enricher <channel_id> <enricher_id> --priority <n> [--test-db] [--json]
retrovue channel detach-enricher <channel_id> <enricher_id> [--test-db] [--json]
```

### Required Parameters

- `channel_id`: Channel identifier (UUID, name, or external ID)
- `enricher_id`: Enricher identifier to attach/detach
- `--priority`: Execution priority for enricher (lower numbers run first)

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment

---

## Safety Expectations

### Channel Operations

- **Non-destructive operations**: Channel listing and enricher management
- **Idempotent**: Safe to run multiple times
- **Test isolation**: `--test-db` prevents production data modification

### Enricher Management

- Enricher attachment requires priority specification
- Detaching non-existent enrichers should be handled gracefully
- Priority conflicts should be resolved automatically

---

## Output Format

### Human-Readable Output

**Channel List:**

```
Channels:
  • Channel 1 (ID: abc-123) - Active producer: LinearProducer
  • Channel 2 (ID: def-456) - Active producer: PrevueProducer
```

**Enricher Operations:**

```
Successfully attached enricher 'metadata' to channel 'Channel 1' with priority 1
Successfully detached enricher 'metadata' from channel 'Channel 1'
```

### JSON Output

```json
{
  "channels": [
    {
      "channel_id": "abc-123",
      "name": "Channel 1",
      "active_producer": "LinearProducer",
      "enrichers": [
        {
          "enricher_id": "metadata-001",
          "name": "metadata",
          "priority": 1
        }
      ]
    }
  ]
}
```

---

## Exit Codes

- `0`: Operation completed successfully
- `1`: Validation error, channel not found, or operation failure

---

## Data Effects

### Database Changes

1. **Enricher Attachment**:

   - ChannelEnricher record created
   - Priority assigned and conflicts resolved
   - Enricher becomes active for channel

2. **Enricher Detachment**:
   - ChannelEnricher record deleted
   - Channel continues operation without enricher

### Side Effects

- No external system changes
- Database transaction for enricher operations
- Logging of enricher attachment/detachment

---

## Behavior Contract Rules (B-#)

- **B-1:** The `channel list` command MUST show all channels with their active producers and attached enrichers.
- **B-2:** When `--json` is supplied, output MUST include fields `"channels"`, `"channel_id"`, `"name"`, `"active_producer"`, and `"enrichers"`.
- **B-3:** The `attach-enricher` command MUST require `--priority` parameter.
- **B-4:** On validation failure (channel not found), the command MUST exit with code `1` and print "Error: Channel 'X' not found".
- **B-5:** The `detach-enricher` command MUST handle non-existent enrichers gracefully.
- **B-6:** All commands MUST support `--test-db` for isolated testing.

---

## Data Contract Rules (D-#)

- **D-1:** Enricher attachment MUST occur within a single transaction boundary.
- **D-2:** Priority conflicts MUST be resolved automatically (reassign existing priorities).
- **D-3:** Enricher detachment MUST NOT affect other channels using the same enricher.
- **D-4:** On transaction failure, ALL changes MUST be rolled back with no partial operations.
- **D-5:** Channel listing MUST include all active enrichers with their priorities.
- **D-6:** All operations run with `--test-db` MUST be isolated from production database.

---

## Test Coverage Mapping

- `B-1..B-6` → `test_channel_contract.py`
- `D-1..D-6` → `test_channel_data_contract.py`

Each rule above MUST have explicit test coverage in its respective test file, following the contract test responsibilities in [README.md](./README.md).  
Each test file MUST reference these rule IDs in docstrings or comments to provide bidirectional traceability.

Future related tests (integration or scenario-level) MAY reference these same rule IDs for coverage mapping but must not redefine behavior.

---

## Error Conditions

### Validation Errors

- Channel not found: "Error: Channel 'invalid-channel' not found"
- Enricher not found: "Error: Enricher 'invalid-enricher' not found"
- Missing priority: "Error: --priority is required for enricher attachment"

### Database Errors

- Transaction rollback on any persistence failure
- Foreign key constraint violations handled gracefully
- Priority conflict resolution

---

## Examples

### Channel Listing

```bash
# List all channels
retrovue channel list

# List with JSON output
retrovue channel list --json

# Test channel listing
retrovue channel list --test-db
```

### Enricher Management

```bash
# Attach enricher with priority
retrovue channel attach-enricher "Channel 1" "metadata-001" --priority 1

# Detach enricher
retrovue channel detach-enricher "Channel 1" "metadata-001"

# Test enricher operations
retrovue channel attach-enricher "Test Channel" "test-enricher" --priority 1 --test-db
```

---

## Safety Guidelines

- Always use `--test-db` for testing channel operations
- Verify channel and enricher existence before operations
- Check enricher priorities after attachment
- Confirm channel configuration after changes


