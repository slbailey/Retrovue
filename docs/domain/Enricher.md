_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Enricher

## Purpose

Enricher defines a pluggable module that adds value to an object and returns the improved object. Enrichers are stateless pure functions: they receive an object and return the updated object; they do not persist and they do not own orchestration. Enrichers are optional and may be applied in sequence.

## Core model / scope

Enrichers declare their scope so the system knows where they are allowed to run.

**scope=ingest**
Input: AssetDraft generated during ingest.
Output: AssetDraft with richer metadata.
Examples:

- Parse .nfo / .jpg sidecar files (tinyMediaManager style).
- Pull metadata from TheTVDB / TMDB.
- Use an LLM to generate synopsis, parental guidance tags, and ad-break markers.

**scope=playout**
Input: a playout plan for a channel (the assembled "what to stream now" structure before ffmpeg is launched).
Output: a modified playout plan.
Examples:

- Apply crossfade between segments instead of hard cuts.
- Add a network watermark bug.
- Add an "Up Next" lower-third.
- Add an emergency crawl/ticker.
- Apply VCR/noise aesthetic.

## Contract / interface

Each enricher must implement:

- a unique type identifier (e.g. nfo-file, thetvdb, fade-transition, channel-bug)
- a parameter spec describing its configuration (for CLI help)
- apply(input) -> output, where input and output types depend on scope

Enrichers must be pure in the sense that they receive an object and return a new or updated version of that object. Enrichers do not perform persistence themselves.

Enrichers must tolerate being skipped. The system is allowed to run zero enrichers.

## Execution model

Enrichers run under orchestration, not autonomously.

**Ingest orchestration:**

After an importer produces AssetDraft objects for a Collection, RetroVue looks up which ingest-scope enrichers are attached to that Collection.

RetroVue runs those enrichers in priority order.

The final enriched AssetDraft is then stored in the RetroVue catalog.

**Playout orchestration:**

After a Producer generates a base playout plan for a Channel, RetroVue looks up which playout-scope enrichers are attached to that Channel.

RetroVue runs those enrichers in priority order.

The final enriched playout plan is used to launch ffmpeg.

Collections can have 0..N ingest enrichers attached.

Channels can have 0..N playout enrichers attached.

Each attachment has an integer priority or order.

Enrichers are applied in ascending priority.

This resolves conflicts such as:

- "Filename parser" sets a title.
- "TheTVDB enricher" fills missing fields but does not overwrite certain fields.
- "LLM enricher" writes synopsis and content warnings last.

## Failure / fallback behavior

Enrichers are not permitted to block ingestion or playout by default.

If an enricher fails on a single AssetDraft during ingest, that error is logged and ingest continues with the partially enriched asset.

If a playout enricher fails when assembling the playout plan for a channel, RetroVue falls back to the most recent successful version of the plan without that enricher's mutation.

Fatal stop conditions (skip entirely) are defined outside the enricher layer:

- Collection not allowed (sync_enabled=false)
- Collection path not resolvable / not reachable
- Importer cannot enumerate assets

## Operator workflows

**retrovue enricher list-types**
List known enricher types available in this build (both ingest and playout scopes).

**retrovue enricher add --type <type> --name <label> [config...]**
Create an enricher instance. Stores configuration values such as API keys, fade duration, watermark asset path.

**retrovue enricher list**
Show configured enricher instances.

**retrovue enricher update <enricher_id> ...**
Modify configuration.

**retrovue enricher remove <enricher_id>**
Remove configuration.

**retrovue collection attach-enricher <collection_id> <enricher_id> --priority <n>**
Attach an ingest-scope enricher to a Collection.

**retrovue collection detach-enricher <collection_id> <enricher_id>**

**retrovue channel attach-enricher <channel_id> <enricher_id> --priority <n>**
Attach a playout-scope enricher to a Channel.

**retrovue channel detach-enricher <channel_id> <enricher_id>**

## Naming rules

The word "enricher" is universal. We do not use "enhancer," "overlay stage," or "post-processor."

- "ingest enricher" means an enricher with scope=ingest.
- "playout enricher" means an enricher with scope=playout.
- "AssetDraft" is the ingest-time object before catalog promotion.
- "Playout plan" is the channel's assembled output plan prior to ffmpeg launch.

## See also

- [Playout pipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
