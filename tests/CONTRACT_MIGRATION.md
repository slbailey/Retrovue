# Contract Migration Status

> **This document is part of the RetroVue Contract System.**  
> For process rules, see `CLI_CHANGE_POLICY.md`.  
> For enforcement status, see this document.

This document tracks the migration from legacy tests to contract-based testing and the enforcement status of each contract.

## Current Enforcement Status

| Status        | Count | Notes                                                                                            |
| ------------- | ----- | ------------------------------------------------------------------------------------------------ |
| ENFORCED      | 10    | All Enricher commands + SourceListTypes + SourceAdd + SourceList + SourceDiscover + SourceDelete |
| TESTS CREATED | 0     | All tests moved to ENFORCED                                                                      |
| PLANNED       | 9     | Source, Collection, Assets, Channel, System                                                      |
| CROSS-DOMAIN  | 4     | Source-Enricher (tests), Source-Importer (tests), Source-Collection (tests), CLI-Data (tests)    |

**10 Contracts ENFORCED:** All Enricher operations (Add, ListTypes, List, Update, Remove) + SourceListTypes + SourceAdd + SourceList + SourceDiscover + SourceDelete  
**0 Contracts with Tests:** All tests moved to ENFORCED  
**9 Contracts Planned:** Source, Collection, Assets, Channel, and System operations  
**4 Cross-Domain Guarantees:** Source-Enricher (tests), Source-Importer (tests), Source-Collection (tests), CLI-Data (tests)

## Migration Status Legend

- **ENFORCED**: Contract is fully implemented and enforced by tests. Changes require contract update first.
- **IN_PROGRESS**: Contract tests exist but implementation is incomplete.
- **PLANNED**: Contract defined but tests not yet created.
- **CROSS-DOMAIN**: Cross-domain guarantees defined but tests not yet created.
- **LEGACY**: Old implementation preserved in `_legacy/` for reference.

---

## Enforced Contracts

### SourceAdd

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/SourceAddContract.md  
**Tests:**

- tests/contracts/test_source_add_contract.py
- tests/contracts/test_source_add_data_contract.py  
  **CI:** YES  
  **Notes:** All 32 contract tests passing. Complete implementation with --discover, --dry-run, and --test-db flags.

### EnricherAdd

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/EnricherAddContract.md  
**Tests:**

- tests/contracts/test_enricher_add_contract.py
- tests/contracts/test_enricher_add_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherListTypes

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/EnricherListTypesContract.md  
**Tests:**

- tests/contracts/test_enricher_list_types_contract.py
- tests/contracts/test_enricher_list_types_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherList

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/EnricherListContract.md  
**Tests:**

- tests/contracts/test_enricher_list_contract.py
- tests/contracts/test_enricher_list_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherUpdate

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/EnricherUpdateContract.md  
**Tests:**

- tests/contracts/test_enricher_update_contract.py
- tests/contracts/test_enricher_update_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### EnricherRemove

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/EnricherRemoveContract.md  
**Tests:**

- tests/contracts/test_enricher_remove_contract.py
- tests/contracts/test_enricher_remove_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first.

### SourceListTypes

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/SourceListTypesContract.md  
**Tests:**

- tests/contracts/test_source_list_types_contract.py
- tests/contracts/test_source_list_types_data_contract.py  
  **CI:** YES  
  **Notes:** This command is considered stable. Any change to behavior must update the contract first. Architecture clarified: Registry returns importer names only; CLI is responsible for validation, compliance checking, and output shaping. All 28 contract tests passing (15 CLI + 13 data contract tests).

### SourceList

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/SourceListContract.md  
**Tests:**

- tests/contracts/test_source_list_contract.py
- tests/contracts/test_source_list_data_contract.py  
  **CI:** YES  
  **Notes:** All 28 contract tests passing (16 behavioral + 12 data contract tests). Complete implementation with consistent read snapshot guarantee (G-7), proper type validation using SourceListTypesContract registry, and accurate collection counting from persisted data.

### SourceDiscover

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/SourceDiscoverContract.md  
**Tests:**

- tests/contracts/test_source_discover_contract.py
- tests/contracts/test_source_discover_data_contract.py  
  **CI:** YES  
  **Notes:** All 24 contract tests passing (13 behavioral + 11 data contract tests). Complete implementation with --dry-run and --test-db support, proper transaction handling with rollback, duplicate collection prevention, and comprehensive error handling.

### SourceDelete

**Status:** ENFORCED  
**Contracts:** docs/contracts/resources/SourceDeleteContract.md  
**Tests:**

- tests/contracts/test_source_delete_contract.py
- tests/contracts/test_source_delete_data_contract.py  
  **CI:** YES  
  **Notes:** All 27 contract tests passing (13 behavioral + 14 data contract tests). Complete implementation with wildcard support, production safety checks, confirmation prompts, cascade deletion, and transactional guarantees. Includes compliance with DestructiveOperationConfirmation (C-1 through C-14) and ProductionSafety (PS-1 through PS-4) contracts.

---

## Cross-Domain Guarantees

> **Cross-Domain Guarantees are governed by the House Standard defined in `docs/contracts/resources/cross-domain/README.md`.**  
> All domain interactions that cross boundaries must have explicit guarantee documents and test suites.

### Source ↔ Enricher Guarantees

**Status:** CROSS-DOMAIN  
**Document:** docs/contracts/resources/cross-domain/Source_Enricher_Guarantees.md  
**Tests:** tests/contracts/cross-domain/test_source_enricher_guarantees.py  
**CI:** YES  
**Notes:** Defines guarantees for source-enricher interactions, validation, and transactional integrity. G-1 through G-4 enforced, G-5 planned (requires SourceRemoveContract and SourceUpdateContract).

### Source ↔ Importer Guarantees

**Status:** CROSS-DOMAIN  
**Document:** docs/contracts/resources/cross-domain/Source_Importer_Guarantees.md  
**Tests:** tests/contracts/cross-domain/test_source_importer_guarantees.py  
**CI:** YES  
**Notes:** Defines guarantees for source-importer interactions, interface compliance, and capability validation. All 9 tests passing (G-1 through G-6 + error standards + transaction boundaries + ID correlation).

### Source ↔ Collection Guarantees

**Status:** CROSS-DOMAIN  
**Document:** docs/contracts/resources/cross-domain/Source_Collection_Guarantees.md  
**Tests:** tests/contracts/cross-domain/test_source_collection_guarantees.py  
**CI:** YES  
**Notes:** Defines guarantees for source-collection interactions, discovery coordination, and lifecycle synchronization. All 9 tests passing (G-1 through G-6 + exit code semantics + error standards + transaction boundaries).

### CLI ↔ Data Guarantees

**Status:** CROSS-DOMAIN  
**Document:** docs/contracts/resources/cross-domain/CLI_Data_Guarantees.md  
**Tests:** tests/contracts/cross-domain/test_cli_data_guarantees.py  
**CI:** YES  
**Notes:** Defines guarantees for CLI-data interactions, transaction management, and error handling consistency. All 8 tests passing (G-1 through G-6 + error standards + transaction boundaries).

---

### Contracts with Tests Created

_None - all tests moved to ENFORCED_

### Planned Contracts

- ⏳ SourceIngest
- ⏳ CollectionIngest
- ⏳ CollectionWipe
- ⏳ AssetsSelect
- ⏳ AssetsDelete
- ⏳ Channel
- ⏳ Collection
- ⏳ SyncIdempotency
- ⏳ UnitOfWork

### Legacy Tests Preserved

All previous test implementations have been moved to `tests/_legacy/` for reference and potential pattern reuse during migration.

---

## CI Policy

**Enforced Contracts:** CI runs contract tests for all ENFORCED contracts plus minimal unit tests that don't contradict contracts.

**Current Enforced Contracts:** All Enricher contracts (Add, ListTypes, List, Update, Remove) + SourceListTypes + SourceAdd + SourceList + SourceDiscover + SourceDelete

**Command:** `pytest tests/contracts --maxfail=1 --disable-warnings -q`

**Special Enforcement:** SourceListTypes and SourceList contract tests run with explicit enforcement in CI workflow with detailed output.

**Excluded:** `tests/_legacy/` is reference material and not included in CI.

---

## Linked Governance Policy

**Change Control:** Refer to `CLI_CHANGE_POLICY.md` for change control procedures and governance rules governing ENFORCED interfaces.
