_Related: [Architecture overview](ArchitectureOverview.md) • [Data flow](DataFlow.md) • [Developer: Plugin authoring](../developer/PluginAuthoring.md)_

# System boundaries

This defines what RetroVue is responsible for and what it is not.

## RetroVue is responsible for

- Maintaining a persistent definition of each Channel.
- Building and advancing a schedule (EPG / Playlog horizons).
- Generating a playout plan at "now".
- Decorating that plan through playout enrichers.
- Launching and supervising ffmpeg to serve real bytes to viewers.
- Writing an as-run log.

## RetroVue is not responsible for

- Permanent 24/7 transcoding. ffmpeg exists only while someone is actually watching.
- Scraping / mounting arbitrary storage paths. The operator must provide valid `local_path` mappings per Collection.
- Automatically ingesting content without operator intent.
- Hardcoding metadata rules. Metadata is handled by ingest enrichers, which are pluggable.
- Directly embedding external live feeds unless implemented as a Producer plugin.

## Security / safety boundaries

- Plugins can register with registries, but cannot modify core orchestration or bypass ChannelManager control of ffmpeg.
- Enrichers operate on objects and return updated objects. They do not persist or assume ownership of durability.
- Producer plugins may not launch ffmpeg themselves.

See also:

- [Plugin authoring](../developer/PluginAuthoring.md)
- [CLI contract](../operator/CLI.md)
