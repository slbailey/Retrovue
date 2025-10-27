# Retrovue Contracts

This directory defines operator-facing contracts. These are **binding**.

There are two kinds of contracts:

## 1. Global CLI Contract

- `cli_contract.md`
- Defines the Retrovue command surface:
  - `retrovue <noun> <verb> [options]`
  - required flags and safety behaviors (`--dry-run`, `--force`, `--json`, etc.)
  - help text expectations
  - exit code semantics
- Tests that assert CLI shape, help output, argument rules, etc. MUST reference this file.

Example tests (after migration):

- `tests/contracts/test_channel_contract.py`
- `tests/contracts/test_source_contract.py`
- `tests/contracts/test_ingest_contract.py`

## 2. Command-Specific Behavioral Contracts

These are deeper guarantees for high-risk flows.

- `collectionwipecontract.md`

  - Destructive wipe semantics
  - What is and is not deleted
  - Confirmation model
  - Dry-run / JSON structure

- `syncidempotencycontract.md`
  - Sync behavior
  - Idempotency guarantees
  - No-duplicate rules
  - Metadata update rules
  - "Don't destroy content" rules

Tests that assert data correctness, idempotency, cleanup, or irreversible changes MUST reference the appropriate command-specific contract.

Example tests:

- `tests/contracts/test_collection_wipe_contract.py`
- `tests/contracts/test_collection_wipe_data_contract.py`
- `tests/contracts/test_sync_idempotency_contract.py`

## Rules

- Behavior MUST be written in a contract (`docs/contracts/*.md`) before tests assert it.
- Tests MUST reference the contract they enforce.
- Implementation MUST change to satisfy the tests, not the other way around.
- Changing CLI flags, prompts, confirmation flows, output formats, exit codes, or data side effects without updating the relevant contract FIRST is considered a breaking change.
