# Domain — EPG generation

## Purpose

The Electronic Program Guide (EPG) provides viewers with information about what's currently airing and what's scheduled to air on each channel. The EPG is generated dynamically from live schedule state rather than being maintained as a separate persistent data structure.

## Data sources

The EPG is built from the following data sources:

- **BroadcastChannel**: Defines the channels and their timing policies
- **BroadcastPlaylogEvent**: Records what was actually played and when
- **CatalogAsset**: Contains the metadata for scheduled content
- **Schedule state**: Live scheduling information managed by ScheduleService

## Runtime relationship

The on-screen guide (and the GuideProducer channel) is generated from live schedule state, not from a permanently maintained epg_entries table. The EPG view is built by joining BroadcastPlaylogEvent to CatalogAsset to present "now / next" with title-level metadata.

## Naming and consistency rules

- **BroadcastChannel.id** (INTEGER PK) is the canonical channel identity for internal operations
- **BroadcastChannel.uuid** is the external identity we surface to logs/clients for correlation
- Any earlier channels table with UUID PK is deprecated
- EPG generation follows the same identity rules as other broadcast domain entities
