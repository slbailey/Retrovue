_Related: [Style guide](STYLEGUIDE.md) • [Architecture overview](architecture/ArchitectureOverview.md) • [Runtime: Channel manager](runtime/ChannelManager.md)_

# Glossary

Short authoritative definitions for internal terms. Use these spellings and meanings consistently.

**Asset**  
The leaf unit RetroVue can eventually broadcast. Each asset belongs to exactly one collection and has a lifecycle state (`new`, `enriching`, `ready`, `retired`) indicating its readiness for scheduling. Only assets in `ready` state are eligible for broadcast.

**Collection**  
A logical grouping of related content from a source (e.g., "The Simpsons", "Classic Movies", "Commercials"). Collections organize content into broadcast-relevant categories.

**Source**  
An origin of media content (e.g., Plex server, local filesystem, ad library). Sources are discovered and enumerated to find available content.

**Channel**  
A persistent virtual linear feed with identity, schedule, branding, and attached enrichers. A Channel exists even if nobody is watching.

**ChannelManager**  
Runtime controller that decides when to start ffmpeg for a Channel, what playout plan to feed it, and when to tear it down.

**EPG**  
Electronic program guide. High-level future schedule for a Channel ("9:00 Movie", "11:00 Cartoons"). Typically planned days ahead.

**Playlog / playout horizon**  
Fine-grained, timestamped list of specific segments (episode slices, ad pods, bumpers) that should air for a Channel in the near future (hours ahead).

**Playout plan**  
Structured output from a Producer that says what should be airing right now, including ordered segments, offsets, and transitions. This is later decorated by playout enrichers and handed to ffmpeg.

**Producer**  
Module that builds a playout plan for "what should air right now" on a Channel.

**Producer Registry**  
Registry where Producer plugin types are registered and configured for Channels.

**Enricher**  
Pluggable module that takes an input object and returns an updated version of that object.

- `scope=ingest`: operates on Asset during ingest enrichment.
- `scope=playout`: operates on a playout plan before ffmpeg launch.  
  Enrichers are ordered and can be attached to Collections (ingest) or Channels (playout).

Ingest enrichers are allowed to mutate asset metadata and state (e.g. move new → enriching → ready).  
Playout enrichers do not mutate assets; they decorate playout segments.

**Segment**  
A concrete playout chunk derived from a scheduled asset. A segment contains file path(s), time offsets, and overlay instructions that ffmpeg will actually execute. Assets are conceptual content; segments are executable playout instructions.

**MasterClock**  
Authoritative "now" for scheduling, playout, and logging decisions.

**As-run log**  
Historical record of what the Channel actually aired at specific timestamps, including fallbacks.

**Operator**  
A human configuring Sources, Collections, Channels, Producers, and Enrichers using the CLI.

See also:

- [Style guide](STYLEGUIDE.md)
- [Channel manager](runtime/ChannelManager.md)
- [Producer lifecycle](runtime/ProducerLifecycle.md)
