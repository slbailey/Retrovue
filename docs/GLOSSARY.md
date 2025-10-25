_Related: [Style guide](STYLEGUIDE.md) • [Architecture overview](architecture/ArchitectureOverview.md) • [Runtime: Channel manager](runtime/ChannelManager.md)_

# Glossary

Short authoritative definitions for internal terms. Use these spellings and meanings consistently.

**AssetDraft**  
The ingest-time representation of a piece of content (episode, movie, bumper) before it is finalized in the RetroVue catalog. Enrichers can modify it during ingest.

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

- `scope=ingest`: operates on AssetDraft during ingest.
- `scope=playout`: operates on a playout plan before ffmpeg launch.  
  Enrichers are ordered and can be attached to Collections (ingest) or Channels (playout).

**MasterClock**  
Authoritative "now" for scheduling, playout, and logging decisions.

**As-run log**  
Historical record of what the Channel actually aired at specific timestamps, including fallbacks.

**Operator**  
A human configuring Sources, Collections, Channels, Producers, and Enrichers using the CLI.

**Source**  
An origin of media, like Plex or a filesystem share. Source plugins enumerate Collections and fetch raw assets for ingest.

See also:

- [Style guide](STYLEGUIDE.md)
- [Channel manager](runtime/ChannelManager.md)
- [Producer lifecycle](runtime/ProducerLifecycle.md)
