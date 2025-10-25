# RetroVue Layer Boundaries & Architecture

> **The definitive guide to RetroVue's internal architecture**  
> Layer boundaries, import rules, and the separation of concerns that protect broadcast correctness.

---

## Overview

RetroVue simulates a **linear broadcast TV network** with strict architectural boundaries that enforce:

- **Operator Control**: Only approved content can air
- **Scheduling Discipline**: Time-based planning follows broadcast rules
- **Runtime Safety**: Playback cannot bypass approval gates

### Core Principle

> **Nothing crosses layer boundaries without permission.**

The system is intentionally layered so that:

1. **Operators** (via CLI) define what the station is allowed to air
2. **Scheduling logic** plans what will air and when
3. **Runtime logic** actually plays it out for viewers

---

## Layer Map

```
retrovue/
├── cli/              # Operator commands and tooling
├── infra/            # Write-path: configuration, DB session mgmt, admin services
├── schedule_manager/ # Scheduling brain: builds playout and EPG horizons
├── runtime/          # Playout execution, channel orchestration
└── domain/           # Content/ingest domain models and enrichment logic
```

Each layer has a specific job and strict limits.

## Layer Responsibilities

### 1. CLI Layer (`retrovue/cli/`)

**Purpose:** Operator interface and configuration management.

#### **WHAT**

- Typer commands exposed as `retrovue ...`
- Configuration and inspection tools
- Operator approval workflows

#### **Commands**

- `retrovue channel add` - Create channels
- `retrovue template add` - Create scheduling templates
- `retrovue template block add` - Define time blocks
- `retrovue schedule assign` - Assign templates to channels
- `retrovue asset add/update/list` - Manage content assets
- Existing ingest/review commands

#### **WHAT IT CAN DO**

- ✅ Collect user/operator intent
- ✅ Call `infra.admin_services` to mutate configuration
- ✅ Print status, dump tables, sanity checks
- ✅ Approve content for broadcast (`canonical=true`)

#### **WHAT IT CANNOT DO**

- ❌ Directly talk to database sessions
- ❌ Generate scheduling horizons or playout plans
- ❌ Spawn playback pipelines
- ❌ Run the station (CLI configures, doesn't operate)

> **CLI does not "run the station." CLI configures the station.**

### 2. Infrastructure Layer (`retrovue/infra/`)

**Purpose:** System configuration write-path and database management.

#### **WHAT**

- Database session/engine helpers (`infra/db.py`)
- Admin services for infrastructure table mutations (`infra/admin_services.py`)
- Configuration persistence and validation

#### **Admin Services**

- `ChannelAdminService.create_channel(...)`
- `TemplateAdminService.create_template(...)`
- `TemplateAdminService.add_block(...)`
- `ScheduleAdminService.assign_template_for_day(...)`
- `AssetAdminService.add_asset(...)`
- `AssetAdminService.update_asset(...)`
- `AssetAdminService.list_assets(...)`

#### **WHAT IT CAN DO**

- ✅ Open database sessions
- ✅ Insert/update rows in infrastructure tables:
  - `channel`
  - `template`
  - `template_block`
  - `schedule_day`
  - `asset`
- ✅ Enforce business rules (canonical gating)
- ✅ Validate configuration integrity

#### **WHAT IT CANNOT DO**

- ❌ Generate playlogs
- ❌ Decide what airs "right now"
- ❌ Start or control playout pipelines
- ❌ Bypass canonical approval
- ❌ Mark unreviewed media as airable

> **Infra is the only layer (besides CLI) allowed to write infrastructure tables. Everyone else treats those tables as read-only.**

### 3. Schedule Manager Layer (`retrovue/schedule_manager/`)

**Purpose:** Scheduling brain that builds playout and EPG horizons.

#### **WHAT**

- **`schedule_manager/models.py`** - ORM models for:
  - `Channel`
  - `Template`
  - `TemplateBlock`
  - `ScheduleDay`
  - `Asset` (broadcast-facing, canonical approval gating)
  - `PlaylogEvent` (what will air / what aired)
- **`schedule_manager/schedule_service.py`** - Content selection and timeline layout
- **`schedule_manager/schedule_orchestrator.py`** - Daemon that keeps horizons extended
- **`schedule_manager/rules.py`** - Interprets `rule_json` from TemplateBlock

#### **WHAT IT CAN DO**

- ✅ Read infrastructure tables (read-only)
- ✅ Compute broadcast day boundaries (e.g. 06:00 → 06:00 local)
- ✅ Handle grid slotting (30-minute blocks, optional offset)
- ✅ Generate per-channel playout/EPG horizons
- ✅ Create `playlog_event` rows (near-term playout horizon)
- ✅ Answer "what should be airing right now?" with offsets

#### **WHAT IT CANNOT DO**

- ❌ Change channel configuration
- ❌ Change template definitions
- ❌ Approve or reject assets
- ❌ Modify `asset.canonical`
- ❌ Touch ingest pipeline data
- ❌ Create channels, assets, templates, etc.

> **ScheduleService is read-only on infrastructure and writes only to runtime schedule tables (`playlog_event`).**

### 4. Runtime Layer (`retrovue/runtime/`)

**Purpose:** Execution and playout control.

#### **WHAT**

- **ChannelManager** - Per-channel runtime controller
- **ProgramDirector** - Global system coordinator
- **MasterClock** - Centralized time authority
- **AsRunLogger** - Playback logging
- **Producer orchestration** - FFmpeg pipeline setup, emergency mode, guide channel mode

#### **WHAT IT CAN DO**

- ✅ Ask ScheduleService "what's airing right now + offset?"
- ✅ Spin up Producer when first viewer tunes in
- ✅ Tear down Producer when last viewer leaves
- ✅ Log what actually aired (to AsRun)
- ✅ Handle emergency mode and guide channels

#### **WHAT IT CANNOT DO**

- ❌ Write to infrastructure tables (`channel`, `template`, `asset`, etc.)
- ❌ Approve new media for broadcast
- ❌ Change core scheduling math (grid size, rollover)
- ❌ Bypass canonical gating
- ❌ Air non-canonical content

> **Runtime's job is to make the station look live, not to invent programming.**

### 5. Domain Layer (`retrovue/domain/`)

**Purpose:** Content ingestion, review, enrichment, and metadata.

#### **WHAT**

- Media coming from Plex / filesystem / TMM
- Tag extraction and metadata normalization
- Duration, chapters → ad breaks
- Human or automated review before "safe to air"
- Content warehouse + QC

#### **WHAT IT CAN DO**

- ✅ Pull from external sources
- ✅ Normalize and enrich metadata
- ✅ Track review state
- ✅ Process content for broadcast readiness

#### **WHAT IT CANNOT DO**

- ❌ Mark something canonical for on-air use by itself
- ❌ Directly tell ScheduleService what to schedule
- ❌ Directly drive runtime playout
- ❌ Bypass operator approval

> **This layer feeds infrastructure, but does not become infrastructure automatically.**

---

## Import Rules & Dependencies

> **This is the contract that prevents architectural drift.**

### Allowed Imports

| Layer                | Can Import From                                                                   |
| -------------------- | --------------------------------------------------------------------------------- |
| **CLI**              | `infra`, `schedule_manager`, `domain`                                             |
| **Infra**            | `schedule_manager.models`, `domain`, `infra.db`                                   |
| **Schedule Manager** | `schedule_manager.models`, `infra.db` (read-only), `runtime.master_clock`         |
| **Runtime**          | `schedule_manager` (read-only), `schedule_manager.models`, `runtime.master_clock` |
| **Domain**           | None (stays clean; lowest layer, no upward dependencies)                          |

### Forbidden Imports

> **These violations break the architectural contract:**

- **Runtime** ❌ must NOT import `infra.admin_services`
- **Runtime** ❌ must NOT import `infra/db` for writes
- **Schedule Manager** ❌ must NOT call `infra.admin_services` to create/modify channels, templates, assets
- **Infra** ❌ must NOT import `runtime` (infra is configuration, not live playout)
- **CLI** ❌ must NOT import `runtime` to "start playback" (CLI is configuration, not on-air control)

> **If you violate these, you're letting the wrong layer mutate or shortcut authority.**

---

## Canonical Gating (Non-Negotiable Rule)

> **Only assets with `canonical=true` in `schedule_manager.models.Asset` are eligible for scheduling.**

### The Rule

- **ScheduleService** must refuse to schedule non-canonical assets
- **Runtime** must refuse to play non-canonical assets
- **Only operators** can approve content for broadcast

### The Only Path to Canonical

```
retrovue asset add / retrovue asset update
    ↓
infra.admin_services.AssetAdminService
    ↓
Database write with canonical=true
```

### What's Forbidden

- **ScheduleService** ❌ forbidden from promoting content to canonical
- **Runtime** ❌ forbidden from promoting content to canonical
- **Ingest/domain** ❌ forbidden from promoting content to canonical automatically

> **That separation is how we protect on-air quality.**

---

## Broadcast Discipline

### Time Math Authority

- **Schedule Manager** owns time math: grid size, grid offset, and 06:00→06:00 broadcast day rollover
- **Runtime** must obey that math and is forbidden from redefining "what day is it?" or "where does the block start?"
- **MasterClock** is the only approved source of "now"
- **ProgramDirector** can set global mode (normal/emergency/guide), but cannot rewrite scheduling policy

### Why This Matters

RetroVue is not "just play files in order."

We are simulating a **TV station**:

1. **Operators** approve what's allowed to air
2. **Schedulers** lay down a believable grid and future horizon
3. **Runtime** makes it look and feel like a live channel when you tune in

**Nobody is allowed to silently skip these steps.**

> **If we follow these boundaries in code, the illusion holds, the system scales, and you never wake up to something airing that you didn't sign off on.**

---

_This document serves as the architectural foundation for RetroVue's development and maintenance._

_Last updated: 2025-01-24_
