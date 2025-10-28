# Contract Migration Status

This document tracks the migration from legacy tests to contract-based testing and the enforcement status of each contract.

## Migration Status Legend

- **ENFORCED**: Contract is fully implemented and enforced by tests. Changes require contract update first.
- **IN_PROGRESS**: Contract tests exist but implementation is incomplete.
- **PLANNED**: Contract defined but tests not yet created.
- **LEGACY**: Old implementation preserved in `_legacy/` for reference.

---

## EnricherAdd

**Status:** ENFORCED  
**Contracts:** docs/contracts/EnricherAdd.md  
**Tests:**

- tests/contracts/test_enricher_add_contract.py
- tests/contracts/test_enricher_add_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

---

## Migration Progress

### Completed Contracts

- ✅ EnricherAdd (ENFORCED)

### Planned Contracts

- ⏳ EnricherListTypes
- ⏳ EnricherList
- ⏳ EnricherUpdate
- ⏳ EnricherRemove
- ⏳ ImporterList
- ⏳ ImporterShow
- ⏳ ImporterValidate
- ⏳ SourceListTypes

### Legacy Tests Preserved

All previous test implementations have been moved to `tests/_legacy/` for reference and potential pattern reuse during migration.

---

## CI Policy

**Enforced Contracts Only:** CI runs only contract tests for ENFORCED contracts plus minimal unit tests that don't contradict contracts.

**Command:** `pytest tests/contracts --maxfail=1 --disable-warnings -q`

**Excluded:** `tests/_legacy/` is reference material and not included in CI.

---

## Change Policy

**Governed Interfaces:** Commands marked as ENFORCED are governed interfaces.

**No Direct Changes:** No one may change flags, JSON output keys, error codes, transaction semantics, etc. without:

1. First editing the contract document in `docs/contracts/`
2. Then updating both contract test files
3. Ensuring all tests pass

**This prevents drift and maintains API stability.**
