# Channel Manager

## Overview

The **ChannelManager** is RetroVue's per-channel runtime controller. It's responsible for managing live playback on ONE channel at a time, ensuring that the correct content is playing at the right time with the proper timing offset.

ChannelManager is subordinate to ProgramDirector and must obey global mode (normal / emergency / guide). It never invents content, never fixes schedule gaps, and never talks to the ingest pipeline.

ChannelManager is where "the channel goes on the air" — it is the board operator for that channel.

## What This Document Is

This document describes the **architecture and behavior** of ChannelManager. It explains:

- What ChannelManager does and doesn't do
- How it coordinates with other components
- How it manages the fanout model and Producer lifecycle
- How it fits into RetroVue's overall architecture

This is **not** a code-level API reference—it's about runtime responsibilities and boundaries.

## Core Responsibilities

### 1. **Runtime Playback Control**

- Ask ScheduleService (Schedule Manager) what should be airing "right now" for this channel
- Use MasterClock to compute the correct offset into the current program (e.g. if a viewer shows up mid-episode at 21:05:33, don't restart from frame 0)
- Resolve the playout plan (segment sequence, timing, etc.) and hand it to a Producer
- Ensure the correct Producer is active for the current mode (normal, emergency, guide)

### 2. **Producer Lifecycle & Fanout Model**

- Track active viewer sessions for this channel
- When the first viewer connects, start (or reuse) a Producer for this channel
- When the last viewer disconnects, stop and tear down the Producer
- Ensure there is never more than one active Producer for a channel at a time
- Swap Producers cleanly if ProgramDirector changes the global mode (e.g. emergency override)
- Surface the Producer's stream endpoint so viewers can attach

### 3. **Channel Policy Enforcement**

- Enforce channel-level restrictions and behavior (content restrictions, blackout handling, etc.)
- Obey ProgramDirector's global mode (normal vs emergency vs guide)
- Apply operational state (enabled/disabled, maintenance, etc.) for this channel

### 4. **Health, State, and Reporting**

- Track channel health and Producer status (starting / running / degraded / stopping)
- Keep runtime data like viewer_count, producer_status, and current mode
- Report that state upward to ProgramDirector
- Expose observability hooks (for dashboards / director console / analytics)
- ChannelManager is the authoritative status reporter for its channel; ProgramDirector and any operator UI should treat ChannelManager as the source of truth for on-air state and health

## Design Principles Alignment

ChannelManager is an Orchestrator (per-channel). Producers are Capability Providers that ChannelManager selects and controls. MasterClock is the only authority for "now" and ChannelManager is not allowed to compute time directly.

**Invariant:** A channel is either fully active or fully failed. There is no such thing as "partially started."

## Lifecycle Model: Viewer Fanout

The Producer only runs when there are active viewers.

- First viewer triggers Producer start
- Last viewer triggers Producer stop
- ChannelManager enforces this rule for its channel

ProgramDirector never directly starts or stops a Producer; it can only set global policy that ChannelManager must obey.

ViewerSession is observational and exists to drive fanout and analytics. ViewerSession never influences scheduling and cannot request content.

Viewers never talk to Producers directly; they attach via the stream endpoint exposed by ChannelManager.

## Relationship to Other Components

### ProgramDirector

- ChannelManager is subordinate to ProgramDirector
- ProgramDirector sets global operating mode (normal / emergency / guide)
- ChannelManager must obey that mode when choosing which Producer to run
- ProgramDirector may demand emergency override; ChannelManager is responsible for actually swapping the Producer
- ProgramDirector is allowed to ask "ensure channel X is on-air," but ProgramDirector is not allowed to micromanage ffmpeg or internal Producer state

### ScheduleService (Schedule Manager)

- ChannelManager is a read-only consumer of schedule data
- ChannelManager asks "what should be airing right now and at what offset?"
- ChannelManager is not allowed to:
  - edit schedules
  - backfill gaps
  - request "new content"
  - slide or retime assets
- If the schedule is bad or missing content, that is an upstream scheduling failure. ChannelManager must not improvise programming
- ChannelManager does not ask ScheduleService for future programming beyond what it needs to start or resume playout "right now." It is a runtime consumer, not a forward scheduler

### Producer

- ChannelManager selects, instantiates, and manages one Producer at a time for its channel
- ChannelManager calls Producer methods like start(), stop(), get_stream_endpoint(), and health()
- ChannelManager may replace the active Producer with a different Producer type (e.g. swap from NormalProducer to EmergencyProducer)
- ChannelManager is not allowed to reach into a Producer's internals (e.g. cannot manage an ffmpeg subprocess directly). It can only use the Producer interface defined in retrovue.runtime.producer.base

### MasterClock

- ChannelManager must use MasterClock to determine "now" and offset into the current asset
- ChannelManager must never call system time directly
- ChannelManager relies on MasterClock timestamps to align viewers joining mid-program

### ViewerSession

- ChannelManager owns tracking of active ViewerSessions for that channel
- Each ViewerSession represents an active tuning/viewer
- ViewerSessions drive the fanout model (start/stop) and populate viewer_count
- ViewerSession does NOT drive scheduling decisions and cannot ask for new content

## Runtime Data Model

ChannelManager cares about these important runtime fields on the Channel entity:

- **viewer_count** - number of active ViewerSessions for this channel
- **producer_status** - current Producer state (stopped, starting, running, stopping, error)
- **current_mode** - mode (normal / emergency / guide)

ChannelManager must keep these in sync with reality and report them to ProgramDirector.

ChannelManager can query a Producer for ProducerState via get_state(), but does not own Producer's internals.

## Hard Boundaries

**ChannelManager IS allowed to:**

- Read schedule data ("what should be airing right now + offset")
- Select and start a Producer
- Stop a Producer when viewer_count drops to 0
- Surface the Producer's stream endpoint to viewers
- Report health/status up to ProgramDirector

**ChannelManager IS NOT allowed to:**

- Invent or substitute content when the schedule is wrong
- Edit or write schedule data
- Directly access Content Manager or ingest
- Spawn its own "emergency content" without ProgramDirector policy
- Reach inside Producer implementation details (e.g. directly control ffmpeg)
- Compute wall clock time on its own (it must ask MasterClock)

## Failure and Recovery Model

If a Producer crashes or reports degraded health:

- ChannelManager can attempt to restart the same Producer for the channel
- If ProgramDirector has set an emergency mode, ChannelManager can switch to the EmergencyProducer instead of retrying normal playout

ProgramDirector defines policy for what should happen on failure (e.g. go to emergency crawl), but ChannelManager actually performs the swap.

If ChannelManager cannot bring up any Producer for a channel, that channel is considered failed (not 'partially on').

## Summary

ChannelManager is the per-channel board operator. It runs the fanout model. It is the only component that actually starts/stops Producers. It obeys ProgramDirector's global mode. It consumes the schedule but does not write it. It never chooses content; it only plays what it is told.

ChannelManager is how a RetroVue channel actually goes on-air.
