# RetroVue System Architecture

> **The single source of truth for understanding RetroVue's architecture**  
> What we're building, why we built it this way, and how the components fit together.

---

## Vision

RetroVue simulates a **24/7 television network** — complete with multiple channels, scheduled shows, commercials, bumpers, promos, and emergency crawls — **without actually running 24/7 encoders**.

### Core Concept

Each channel maintains a **virtual linear timeline** in the database that always advances with wall-clock time. Even when nobody is watching, the system "knows" what's airing right now. When a viewer tunes in, RetroVue spins up a real playout pipeline at the correct point in the schedule — and when the last viewer leaves, the pipeline shuts down.

> **The illusion of a continuous broadcast is preserved without burning compute.**

### Design Philosophy

- **Scheduling is intentional and rule-driven**, just like a real broadcast station
- RetroVue isn't a playlist or shuffle engine — it's a **simulation of television as a medium**: predictable, rhythmic, and time-based
- **The goal is authenticity, not convenience**
- You don't pick what to watch — you tune in to whatever's on, mid-show if necessary
- **That feeling of shared linear time is the product**

### What RetroVue Is Not

| System         | Purpose                                                      | RetroVue's Difference                                                                                        |
| -------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| **Plex**       | VOD (video-on-demand) system — browse and play what you want | Linear, not on-demand. Generates channels that follow fixed schedules with ads, bumpers, and promos          |
| **VOD Server** | Responds to user requests for files                          | Curates time — channels appear to run continuously on their own schedules, whether anyone is watching or not |

---

## High-Level Architecture

RetroVue is composed of several layers working together to maintain, schedule, and deliver believable "live" channels.

### Library Domain (Content Ingest Layer)

**Purpose:** Gather metadata about available content (shows, movies, promos, commercials).

**How it works:**

- **Adapters** connect to external libraries (e.g., Plex, local folders, ad libraries)
- **Enrichers** process this metadata to extract what broadcast scheduling needs: runtime, ratings, ad break markers, tags, and restrictions

**Contract:** Library Domain is authoritative for content availability and metadata quality, but runtime never queries Library Domain directly. It's batch, not real-time.

> **Important:** Library Domain operations can be slow. Playback cannot depend on it.

> **See docs/components/content-manager.md for Library Domain details.**

### Broadcast Domain (Scheduling Layer)

Builds and maintains **two rolling planning horizons** for every channel:

#### EPG Horizon

| Property      | Value                                                        |
| ------------- | ------------------------------------------------------------ |
| **Purpose**   | Coarse, human-facing grid (e.g. "9:00 PM – Classic Sitcoms") |
| **Structure** | 30-minute blocks snapped to a fixed grid                     |
| **Range**     | 2–3 days into the future                                     |
| **Use**       | Feeds guides, "now/next" banners, and listings channels      |
| **Update**    | Extended or rolled forward daily                             |

#### Playlog Horizon

| Property      | Value                                                         |
| ------------- | ------------------------------------------------------------- |
| **Purpose**   | Fine, machine-facing playout plan                             |
| **Structure** | Fully resolved segments — episodes, ad pods, bumpers, padding |
| **Range**     | 2–3 hours into the future                                     |
| **Use**       | Drives actual playout and as-run logs                         |
| **Update**    | Continuously rolled forward                                   |

#### Timing Model

Every scheduled item has an `absolute_start` and `absolute_end` timestamp in wall-clock time. That's how we can determine, at 09:05, that a sitcom which began at 09:00 should start 5 minutes in. Because every Playlog Event carries `absolute_start` and `absolute_end`, ChannelManager can start playback mid-show at the correct offset instead of always starting from the top of the file.

#### Block Alignment Rule

- **EPG blocks** always align to 30-minute boundaries, even if episode runtimes don't
- **Playlog** fills the leftover time with ad pods, bumpers, and promos to end exactly on the boundary

> **Key Insight:** This dual-horizon model lets RetroVue act like a real network without needing to prebuild byte-accurate schedules for days in advance.

> **See docs/components/schedule-manager.md for horizon generation + timing.**

### Runtime / Channel Orchestration Layer

> **This is where channels come to life.**

#### Key Components

- **ProgramManager (ProgramDirector)** — supervises all channels
- **ChannelManager** — runs one specific channel

#### Responsibilities

- **ProgramManager** coordinates high-level system behavior — startup, shutdown, emergency mode — and monitors channel health
- **ChannelManager** owns the runtime lifecycle of its channel, handling viewer sessions and Producers

#### Viewer Flow

```mermaid
graph TD
    A[Viewer tunes in] --> B[ChannelManager asks ScheduleManager<br/>"what should be airing right now + offset?"]
    B --> C[ChannelManager builds playout plan<br/>starting at correct position within current show]
    C --> D[ChannelManager spins up Producer<br/>to emit the stream]
    D --> E[Subsequent viewers attach<br/>to that same Producer]
    E --> F{Viewer count = 0?}
    F -->|Yes| G[ChannelManager tears down Producer]
    F -->|No| E
```

#### Fanout Invariant

- **Exactly one Producer** may be active per channel
- **Many viewers** can watch it simultaneously
- **When none remain**, the Producer stops

#### Responsibility Boundary

> **ProgramManager never assembles playout plans** — it delegates per-channel logic to ChannelManagers.

### Playout / Producer Layer

A **Producer** emits the audiovisual stream for a channel.

#### Types of Producers

| Type                     | Purpose                                          |
| ------------------------ | ------------------------------------------------ |
| **Programming Producer** | Standard episodes, ads, bumpers                  |
| **Emergency Producer**   | Full-screen alert or crawl takeover              |
| **Guide Producer**       | TV Guide-style output listing what's on now/next |

#### Key Principles

- **Producers are modular** — ChannelManager decides which Producer to use and what plan to give it
- **Producers don't pick content** — they render the playout plan they're given

#### Requirements

- ✅ **Must start mid-show** at any offset, matching current wall-clock time
- ✅ **Must follow the Playlog plan exactly** — order, duration, transitions
- ✅ **Must be composable** with overlays
- ✅ **Must terminate cleanly** when instructed

### System Time / MasterClock

> **A single MasterClock defines "station time" for the entire system.**

#### Rules

- **All scheduling, offset math, and playout alignment** reference this clock
- **No other component** may call `datetime.now()` or keep its own clock
- **MasterClock is also what future As-Run logging will use** to prove what actually aired
- **This ensures** logs, playback, and schedule alignment all agree

> **MasterClock is law.**  
> **Everyone asks it what "now" means.**

---

## Core Components

### ContentManager

#### **WHAT**

Handles ingestion of media metadata from external sources. Stores only broadcast-relevant info — runtime, rating, ad breaks, tags.

#### **WHY**

Scheduling depends on accurate runtime and ad break data to create believable commercial pods. We don't need full media management.

#### **HOW**

- Uses **adapters and enrichers** to populate the content catalog
- Marks items with scheduling eligibility (safe-for-daytime, genre tags, etc.)

> **In practice:** ContentManager provides the universe of eligible content that ScheduleManager can draw from.

### ScheduleManager (ScheduleService)

#### **WHAT**

Maintains EPG and Playlog horizons for each channel.

#### **WHY**

Viewers need a guide; the playout engine needs exact timing. Splitting them lets us plan days in broad strokes without resolving every frame ahead of time.

#### **HOW**

- **Applies block rules and templates** (e.g. "Weeknights 8–10 PM = classic sitcoms, PG-13 max")
- **Selects episodes**, inserts bumpers and promos, and pads blocks to end on time
- **Persists both horizons** with `absolute_start` / `absolute_end` timestamps
- **Rolls EPG daily** (~2–3 days out) and **Playlog continuously** (~2–3 hours ahead)

#### Invariants

- **EPG Horizon** ≥ 2 days ahead at all times
- **Playlog Horizon** ≥ 2 hours ahead at all times
- **ChannelManager assumes** these horizons exist and never builds schedules itself

### ProgramManager (ProgramDirector)

#### **WHAT**

Global supervisor and policy layer. Oversees all channels.

#### **WHY**

We need a single authority that can coordinate state across channels — e.g., triggering emergency takeover or reporting overall health.

#### **HOW**

- **Holds all ChannelManager instances**
- **Can toggle emergency mode** (swap all channels to EmergencyProducer)
- **Monitors channel health** and orchestrates lifecycle events
- **Provides a single control point for system-wide state** (for example, "all channels go to emergency crawl now.")

> **ProgramManager does not pick content or assemble plans** — it orchestrates systems and state.

### ChannelManager

#### **WHAT**

Per-channel runtime controller. Tracks viewer count and manages Producer lifecycle.

#### **WHY**

We only spin up resources when needed. It's also how viewers "drop in" mid-show without seeing startup artifacts.

#### **HOW**

- **On tune-in:** query ScheduleManager → get current item + offset → build playout plan → start Producer
- **On tune-out:** decrement viewer_count; if it hits 0, tear down Producer
- **Swaps Producers** if mode changes (e.g., emergency override)

#### Invariants

- **At most one Producer** active per channel
- **Producers start mid-show** if required
- **Viewer count reaching zero** triggers teardown

> **Operationally, ChannelManager is the channel at runtime.**

### Producer

#### **WHAT**

Encodes and streams content for a channel according to a playout plan.

#### **WHY**

Separates "what to play" (scheduling) from "how to render/encode."

#### **HOW**

- **Reads plan:** program segments, ad pods, bumpers, padding
- **Runs FFmpeg** or equivalent to produce continuous MPEG-TS output
- **Supports mid-program start**, overlays, and clean stop
- **Other viewers attach** to this output stream (fanout model)

> **Only one Producer per channel.** Others may view its stream, but not spawn new ones.

> **See docs/components/program-manager.md for runtime coordination and playout.**

### Overlay / Branding Layer

#### **WHAT**

Visual layer for logos, lower-thirds, crawls, and rating bugs.

#### **WHY**

Adds authenticity, identity, and compliance features without modifying core video assets.

#### **HOW**

ChannelManager applies overlays to the playout plan before starting a Producer. Overlays are composable and independent of Producers.

> **Overlay exists to decorate output without changing how Producers function.**

### MasterClock

#### **WHAT**

Centralized station time authority.

#### **WHY**

Keeps scheduling, playout, and logging in perfect sync and makes time-based debugging possible.

#### **HOW**

- **Provides current station time** to ScheduleManager, ProgramManager, ChannelManager, and logging
- **All modules use this** — none call system time directly

> **If the scheduler says "play at 3:15 PM," everyone agrees what "3:15 PM" means.**

---

## Design Paradigms / Patterns

### Modular Components with Narrow Responsibilities

Each component solves one tier of the problem:

| Component           | Responsibility      |
| ------------------- | ------------------- |
| **ContentManager**  | metadata ingestion  |
| **ScheduleManager** | future planning     |
| **ProgramManager**  | global coordination |
| **ChannelManager**  | per-channel runtime |
| **Producer**        | output              |

> **This modularity keeps the system testable, composable, and safe to extend.**

### Adapters and Enrichers

- **Adapters** connect to diverse data sources (Plex, filesystem, ad libraries)
- **Enrichers** convert raw metadata into the broadcast concepts (runtime, ad breaks, rating, "safe for daypart")

> **This separation lets us evolve or replace sources without touching core scheduling.**

### Producers as Swap-In Output Drivers

- **Runtime never hardcodes** streaming logic
- **ChannelManager simply asks** a Producer to execute a plan
- **This allows alternate Producers** (guide channel, emergency feed) without changing orchestration logic

### Horizon-Based Scheduling

Planning happens in two scopes:

| Horizon             | Type                    | Scope       |
| ------------------- | ----------------------- | ----------- |
| **EPG Horizon**     | human-facing, coarse    | days ahead  |
| **Playlog Horizon** | machine-facing, precise | hours ahead |

> **This allows real-network authenticity without excessive precomputation.**

### On-Demand Channel Activation

- **Channels are virtual** until watched
- **The first viewer starts** the Producer, additional viewers attach to the same output, and the last viewer stops it
- **That's how RetroVue looks like** a 24/7 cable network while using minimal resources

> **This is the core economic insight: full network experience, fractional infrastructure cost.**

---

## Glossary

| Term                   | Definition                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Channel**            | A virtual broadcast stream with its own schedule and identity                                                                  |
| **Block / Block Rule** | Time segment (e.g., "Weeknights 8–10PM = Classic Sitcoms"). Defines allowed content and tone                                   |
| **EPG Horizon**        | Coarse, grid-aligned programming schedule, 2–3 days ahead. Rolled forward daily                                                |
| **Playlog Horizon**    | Fine-grained, fully resolved playout plan, 2–3 hours ahead. Continuously extended                                              |
| **Playlog Event**      | One scheduled segment with `absolute_start` / `absolute_end` timestamps (e.g., "Commercial Pod #2 from 09:14:30–09:15:00")     |
| **Viewer Fanout**      | Model where the first viewer triggers Producer startup, additional viewers share the same output, and last viewer shutdowns it |
| **ProgramManager**     | Oversees all channels; handles global policies and emergencies                                                                 |
| **ChannelManager**     | Controls runtime state of one channel; handles viewer count and Producer lifecycle                                             |
| **Producer**           | Generates the audiovisual output for a channel. Different types handle normal, guide, or emergency modes                       |
| **Overlay**            | Visual branding or crawl applied over the video feed                                                                           |
| **MasterClock**        | Single authoritative notion of "now." All timing derives from it; direct system time calls are prohibited                      |
| **Ad Pod**             | Cluster of commercials played together during a break                                                                          |
| **Bumper**             | Short station ID or transition clip between programs                                                                           |
| **As-Run Log**         | A record of what actually aired versus what was scheduled, using MasterClock timestamps. Planned feature                       |

---

_This document serves as the architectural foundation for RetroVue's development and maintenance._
