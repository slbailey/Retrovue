# RetroVue documentation index

RetroVue simulates a 24/7 linear TV network using scheduled content, playout logic, branding, and live ffmpeg output — but only spins real video when someone is actually watching.

This directory is organized by audience and layer.

## Architecture

High-level mental model of the system.

- [Architecture overview](architecture/ArchitectureOverview.md)
- [Data flow](architecture/DataFlow.md)
- [System boundaries](architecture/SystemBoundaries.md)

## Domain models

Core concepts RetroVue is built on. These define what the system is, not how it runs.

- [Source](domain/Source.md)
- [Enricher](domain/Enricher.md)
- [Playout pipeline](domain/PlayoutPipeline.md)
- [Channel](domain/Channel.md)
- [Scheduling](domain/Scheduling.md) - Scheduling system architecture
- [SchedulePlan](domain/SchedulePlan.md) - Schedule plan domain model
- [Program](domain/Program.md) - Program domain model (linked list of SchedulableAssets)
- [Zone](domain/Zone.md) - Zone domain model (time windows)
- [ScheduleDay](domain/ScheduleDay.md) - Resolved daily schedules
- [Playlist](architecture/Playlist.md) - Resolved pre-AsRun list of physical assets
- [PlaylogEvent](domain/PlaylogEvent.md) - Runtime execution plan

## Runtime

How RetroVue behaves at runtime. ChannelManager, ffmpeg lifecycle, timing.

- [Channel manager](runtime/ChannelManager.md)
- [Producer lifecycle](runtime/ProducerLifecycle.md)
- [MasterClock](domain/MasterClock.md)
- [As-run logging](runtime/AsRunLogging.md)

## Operator

How an operator configures and runs the system.

- [CLI contract](../contracts/README.md)
- [Operator workflows](operator/OperatorWorkflows.md)

## Developer

How to extend RetroVue safely by adding plugins.

- [Plugin authoring](developer/PluginAuthoring.md)
- [Registry API](developer/RegistryAPI.md)
- [Testing plugins](developer/TestingPlugins.md)

## Methodology

House writing style and doc rules.

- [AI assistant methodology](methodology/AI-Assistant-Methodology.md)
- [Style guide](STYLEGUIDE.md)
- [Glossary](GLOSSARY.md)
