# Retrovue Contracts

This directory defines operator-facing contracts. These are **binding**.

## Contract Structure

**One contract per noun/verb combination** with **two test files per contract**:

### Contract Document

- `docs/contracts/{Noun}{Verb}Contract.md` (e.g., `CollectionWipeContract.md`, `AssetsDeleteContract.md`)
- Defines the complete behavioral contract for that command
- Source of truth for CLI shape, flags, output, safety expectations, and data effects

### Test Files

Each contract has exactly two test files:

1. **CLI Contract Test**: `tests/contracts/test_{noun}_{verb}_contract.py`

   - Validates CLI syntax, flags, prompts, help text, output format
   - Tests operator-facing behavior and user experience
   - Ensures stable command interface

2. **Data Contract Test**: `tests/contracts/test_{noun}_{verb}_data_contract.py`
   - Validates database persistence and data integrity
   - Tests actual data changes, side effects, and cleanup
   - Ensures correct database state transitions

## Contract Types

### 1. Global CLI Contract

- `cli_contract.md`
- Defines the Retrovue command surface:
  - `retrovue <noun> <verb> [options]`
  - Required flags and safety behaviors (`--dry-run`, `--force`, `--json`, etc.)
  - Help text expectations
  - Exit code semantics
- Tests that assert CLI shape, help output, argument rules, etc. MUST reference this file.

### 2. Command-Specific Behavioral Contracts

These are deeper guarantees for high-risk flows.

**Examples:**

- `CollectionWipeContract.md`

  - Destructive wipe semantics
  - What is and is not deleted
  - Confirmation model
  - Dry-run / JSON structure
  - **Tests**: `test_collection_wipe_contract.py` + `test_collection_wipe_data_contract.py`

- `AssetsDeleteContract.md`

  - Asset deletion/restoration semantics
  - Soft vs hard delete behavior
  - Reference checking and safety
  - **Tests**: `test_assets_delete_contract.py` + `test_assets_delete_data_contract.py`

- `AssetsSelectContract.md`
  - Asset selection criteria and validation
  - Output format and filtering
  - **Tests**: `test_assets_select_contract.py` + `test_assets_select_data_contract.py`

## Contract Pattern

### Contract Document Structure

Each contract document MUST include:

1. **Command Shape**: Exact CLI syntax and required flags
2. **Safety Expectations**: Confirmation prompts, dry-run behavior, force flags
3. **Output Format**: Human-readable and JSON output structure
4. **Exit Codes**: Success and failure exit codes
5. **Data Effects**: What changes in the database
6. **Contract Test Coverage**: Names of the two test files that enforce this contract

### Test File Responsibilities

**CLI Contract Test** (`test_{noun}_{verb}_contract.py`):

- CLI syntax validation
- Flag behavior (`--dry-run`, `--force`, `--json`)
- Help text and error messages
- Output format validation
- Exit code verification
- Interactive prompts and confirmations

**Data Contract Test** (`test_{noun}_{verb}_data_contract.py`):

- Database state changes
- Data integrity and cleanup
- Side effects and dependencies
- Persistence guarantees
- Transaction boundaries

## Rules

- **One contract per noun/verb**: Each command has exactly one contract document
- **Two tests per contract**: Each contract has exactly two test files (CLI + data)
- **Contract first**: Behavior MUST be written in a contract before tests assert it
- **Test references**: Tests MUST reference the contract they enforce
- **Implementation follows tests**: Implementation MUST change to satisfy the tests, not the other way around
- **Breaking changes**: Changing CLI flags, prompts, confirmation flows, output formats, exit codes, or data side effects without updating the relevant contract FIRST is considered a breaking change
