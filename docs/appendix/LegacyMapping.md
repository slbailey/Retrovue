# Legacy Architecture Mapping

**Architecture Refactoring Date:** November 2025  
**Status:** Legacy concepts deprecated, replaced by unified SchedulableAsset architecture

This document provides a comprehensive mapping of legacy scheduling architecture concepts to their replacements in the unified SchedulableAsset model. Use this guide when migrating code, updating APIs, or understanding historical context.

---

## Before/After Concept Mapping

| Legacy Concept                            | New Concept                                                           | Mapping Notes                                                                                                                                            |
| ----------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pattern**                               | **Program**                                                           | Programs are now linked lists of SchedulableAssets with `play_mode` (random, sequential, manual). Programs define ordering and sequencing, not duration. |
| **PatternZone**                           | **Zone**                                                              | Zones now hold SchedulableAssets directly (Programs, Assets, VirtualAssets, SyntheticAssets). Duration is zone-controlled.                               |
| **Pattern reference in Zone**             | **SchedulableAsset placement in Zone**                                | Zones directly contain SchedulableAssets, eliminating the Pattern intermediate layer.                                                                    |
| **VirtualProducer**                       | **Producer** (runtime component)                                      | VirtualProducers don't exist. VirtualAssets expand to physical Assets which then feed standard Producers (runtime components).                           |
| **Duration in Program**                   | **Duration in Zone**                                                  | Duration is now zone-controlled, not program-controlled. Programs define ordering and sequencing only.                                                   |
| **Intro/outro fields in Program**         | **Linked list nodes in `asset_chain`**                                | Intro/outro bumpers are now nodes in the Program's `asset_chain` linked list, not separate fields.                                                       |
| **Pattern expansion at ScheduleDay**      | **Program expansion at Playlist generation**                          | Programs expand their asset chains at playlist generation, not at ScheduleDay resolution.                                                                |
| **VirtualAsset expansion at ScheduleDay** | **VirtualAsset expansion at Playlist generation**                     | VirtualAssets expand to physical Assets at playlist generation, not at ScheduleDay time.                                                                 |
| **ScheduleDay → PlaylogEvent**            | **ScheduleDay → Playlist → PlaylogEvent**                             | New Playlist layer between ScheduleDay and PlaylogEvent for asset expansion.                                                                             |
| **Pattern repetition to fill Zone**       | **Zone controls duration, SchedulableAssets play within Zone window** | Zones control timing and duration. SchedulableAssets play within the Zone's time window.                                                                 |
| **Pattern as container**                  | **Program as linked list**                                            | Programs are now linked lists of SchedulableAssets with `play_mode`, not containers.                                                                     |
| **PatternProducer**                       | **Producer** (runtime component)                                      | Producers are unified as output-oriented runtime components, not tied to Patterns or Programs.                                                           |

---

## Key Architectural Shifts

### 1. Elimination of Pattern Layer

**Before:** Patterns were separate entities that contained ordered Program references. Zones referenced Patterns.

**After:** Programs now serve the role of Patterns. Programs are linked lists of SchedulableAssets with `play_mode`. Zones directly contain SchedulableAssets (Programs, Assets, VirtualAssets, SyntheticAssets).

**Impact:**
- No more Pattern entity in the database
- Zone schema simplified (no `pattern_id` field)
- Programs can be nested (Programs can reference other Programs in their `asset_chain`)

### 2. Direct SchedulableAsset Placement

**Before:** Zones referenced Patterns, which contained Programs.

**After:** Zones directly contain SchedulableAssets. No intermediate Pattern layer.

**Impact:**
- Simpler data model
- More flexible content placement
- Clearer ownership of timing and duration

### 3. Duration Ownership

**Before:** Programs or Patterns could define duration.

**After:** Duration is explicitly zone-controlled. Programs define ordering and sequencing only.

**Impact:**
- Clear separation of concerns
- Zones control timing windows
- Programs are purely about content composition

### 4. Playlist Layer

**Before:** ScheduleDay → PlaylogEvent (direct)

**After:** ScheduleDay → Playlist → PlaylogEvent

**Impact:**
- New intermediate layer for asset expansion
- Programs and VirtualAssets expand at playlist generation
- Clear separation between planning (ScheduleDay) and execution (Playlist/PlaylogEvent)

### 5. Expansion Timing

**Before:** Programs and VirtualAssets expanded at ScheduleDay resolution.

**After:** Programs and VirtualAssets expand at playlist generation.

**Impact:**
- ScheduleDay contains SchedulableAssets (not fully resolved physical assets)
- EPG can show Programs/VirtualAssets without resolving to specific episodes
- Playlist generation happens closer to playout time

### 6. Producer Unification

**Before:** VirtualProducers existed as special producers for VirtualAssets.

**After:** Producers are unified as runtime components. VirtualAssets expand to physical Assets which then feed standard Producers.

**Impact:**
- Simpler producer architecture
- Producers are output-oriented, not tied to scheduling-time entities
- VirtualAssets are purely planning-time constructs

---

## Migration Strategy

### For API Consumers

If your code references Patterns or PatternZones:

1. **Pattern references** → Replace with **Program** references
2. **PatternZone references** → Replace with **Zone** references
3. **Pattern expansion** → Program expansion happens at playlist generation
4. **VirtualProducer** → Remove, use standard Producer with expanded VirtualAssets

### For Internal Teams

1. **Database migrations:**
   - Remove `pattern` table (if exists)
   - Remove `pattern_id` from `zone` table
   - Add `schedulable_assets` array to `zone` table
   - Update Program schema to use `asset_chain` linked list

2. **Code updates:**
   - Update all Pattern references to Program
   - Update Zone code to work with SchedulableAssets directly
   - Move expansion logic from ScheduleDay generation to Playlist generation
   - Update Producer code to remove VirtualProducer references

3. **Contract tests:**
   - Update contract tests to use new architecture
   - Legacy contract files are marked with deprecation notices
   - See `docs/contracts/resources/` for updated contracts

---

## Related Documentation

- **[Architecture Overview](../overview/architecture.md)** - High-level architecture
- **[Domain: Program](../domain/Program.md)** - Program domain model (replaced Pattern)
- **[Domain: Zone](../domain/Zone.md)** - Zone domain model
- **[Domain: SchedulePlan](../domain/SchedulePlan.md)** - SchedulePlan domain model
- **[Domain: Playlist](../architecture/Playlist.md)** - Playlist architecture
- **[Verification Report](../VERIFICATION_REPORT.md)** - Comprehensive verification of architecture changes

---

## Questions?

If you encounter legacy Pattern references or need clarification on the migration:

1. Check this mapping table
2. Review the domain documentation for the new concept
3. Check contract files for deprecation notices
4. Refer to the verification report for detailed architecture analysis

---

_Last updated: November 2025_

