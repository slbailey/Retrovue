# Contract Migration Status

> **This document is part of the RetroVue Contract System.**  
> For process rules, see `CLI_CHANGE_POLICY.md`.  
> For enforcement status, see this document.

This document tracks the migration from legacy tests to contract-based testing and the enforcement status of each contract.

## Current Enforcement Status

| Status        | Count | Notes                                       |
| ------------- | ----- | ------------------------------------------- |
| ENFORCED      | 6     | All Enricher commands + SourceListTypes     |
| TESTS CREATED | 0     | None                                        |
| PLANNED       | 12    | Source, Collection, Assets, Channel, System |

**6 Contracts ENFORCED:** All Enricher operations (Add, ListTypes, List, Update, Remove) + SourceListTypes  
**0 Contracts with Tests:** None  
**12 Contracts Planned:** Source, Collection, Assets, Channel, and System operations

## Migration Status Legend

- **ENFORCED**: Contract is fully implemented and enforced by tests. Changes require contract update first.
- **IN_PROGRESS**: Contract tests exist but implementation is incomplete.
- **PLANNED**: Contract defined but tests not yet created.
- **LEGACY**: Old implementation preserved in `_legacy/` for reference.

---

## Enforced Contracts

### EnricherAdd

**Status:** ENFORCED  
**Contracts:** docs/contracts/EnricherAddContract.md  
**Tests:**

- tests/contracts/test_enricher_add_contract.py
- tests/contracts/test_enricher_add_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherListTypes

**Status:** ENFORCED  
**Contracts:** docs/contracts/EnricherListTypesContract.md  
**Tests:**

- tests/contracts/test_enricher_list_types_contract.py
- tests/contracts/test_enricher_list_types_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherList

**Status:** ENFORCED  
**Contracts:** docs/contracts/EnricherListContract.md  
**Tests:**

- tests/contracts/test_enricher_list_contract.py
- tests/contracts/test_enricher_list_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherUpdate

**Status:** ENFORCED  
**Contracts:** docs/contracts/EnricherUpdateContract.md  
**Tests:**

- tests/contracts/test_enricher_update_contract.py
- tests/contracts/test_enricher_update_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherRemove

**Status:** ENFORCED  
**Contracts:** docs/contracts/EnricherRemoveContract.md  
**Tests:**

- tests/contracts/test_enricher_remove_contract.py
- tests/contracts/test_enricher_remove_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### SourceListTypes

**Status:** ENFORCED  
**Contracts:** docs/contracts/SourceListTypesContract.md  
**Tests:**

- tests/contracts/test_source_list_types_contract.py
- tests/contracts/test_source_list_types_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first. Architecture clarified: Registry returns importer names only; CLI is responsible for validation, compliance checking, and output shaping. All 28 contract tests passing (15 CLI + 13 data contract tests).

---

## Migration Progress

### Contracts with Tests Created

- None (all contracts with tests have been moved to ENFORCED)

### Planned Contracts

- ⏳ SourceAdd
- ⏳ SourceDiscover
- ⏳ SourceIngest
- ⏳ CollectionIngest
- ⏳ CollectionWipe
- ⏳ AssetsSelect
- ⏳ AssetsDelete
- ⏳ Channel
- ⏳ Collection
- ⏳ SourceDelete
- ⏳ SyncIdempotency
- ⏳ UnitOfWork

### Legacy Tests Preserved

All previous test implementations have been moved to `tests/_legacy/` for reference and potential pattern reuse during migration.

---

## CI Policy

**Enforced Contracts:** CI runs contract tests for all ENFORCED contracts plus minimal unit tests that don't contradict contracts.

**Current Enforced Contracts:** All Enricher contracts (Add, ListTypes, List, Update, Remove) + SourceListTypes

**Command:** `pytest tests/contracts --maxfail=1 --disable-warnings -q`

**Special Enforcement:** SourceListTypes contract tests run with explicit enforcement in CI workflow with detailed output.

**Excluded:** `tests/_legacy/` is reference material and not included in CI.

---

## Linked Governance Policy

**Change Control:** Refer to `CLI_CHANGE_POLICY.md` for change control procedures and governance rules governing ENFORCED interfaces.
