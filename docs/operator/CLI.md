_Related: [Architecture overview](../architecture/ArchitectureOverview.md) • [Runtime: Channel manager](../runtime/ChannelManager.md) • [Domain: Source](../domain/Source.md)_

# RetroVue CLI Contract

This document defines the expected CLI surface for operators. These commands must match implementation and vice versa. If implementation deviates from this contract, implementation is wrong.

## Sources

### `retrovue source list-types`

Show available source types registered in the Source Registry (e.g. plex, filesystem, jellyfin).

**Output**: List of available source types with descriptions.

### `retrovue source add --type <type> [params...]`

Register a new Source instance.

**Required**:

- `--type` is mandatory.

Each type defines its own additional required params.

**Behavior**:

- If called with `--help` and no `--type`, print generic usage plus available types.
- If called with `--type <type> --help`, print that importer's specific parameter contract (required / optional flags, examples).

### `retrovue source list`

List configured Sources (IDs, names, types).

**Output**: Table showing source_id, name, type, status.

### `retrovue source update <source_id> [params...]`

Update connection details or label.

**Parameters**: Same as add command for the source type.

### `retrovue source remove <source_id>`

Remove that Source.

**Behavior**: Confirms removal and shows affected collections.

### `retrovue source sync-collections <source_id>`

Ask the importer to enumerate that Source's Collections (libraries). Create or update Collection rows in RetroVue.

**Output**: Shows discovered collections and sync status.

## Collections

### `retrovue collection list --source <source_id>`

Show Collections for a Source. For each:

- collection_id
- display_name
- source_path
- local_path (mapped path RetroVue will read)
- sync_enabled (true/false)
- ingestable (derived from sync_enabled + path reachability)

### `retrovue collection update <collection_id> --sync-enabled <true|false> [--local-path <path>]`

Enable/disable ingest for that Collection. Configure or change the local path mapping for that Collection.

**Parameters**:

- `--sync-enabled`: Enable or disable collection sync
- `--local-path`: Override local path mapping

### `retrovue collection attach-enricher <collection_id> <enricher_id> --priority <n>`

Attach an ingest-scope enricher to this Collection.

**Parameters**:

- `collection_id`: Target collection
- `enricher_id`: Enricher to attach
- `--priority`: Priority order (lower numbers run first)

### `retrovue collection detach-enricher <collection_id> <enricher_id>`

Remove enricher from collection.

## Ingest

### `retrovue ingest run <collection_id>`

Ingest that single Collection:

- Validate that the Collection is allowed and reachable.
- Call the importer for that Collection.
- Produce AssetDraft objects.
- Apply ingest-scope enrichers in priority order.
- Store the final enriched assets in the RetroVue catalog.

**Output**: Progress indicators and summary of ingested assets.

### `retrovue ingest run --source <source_id>`

Ingest all Collections under that Source where:

- sync_enabled=true
- local_path is valid/reachable

**Output**: Progress for each collection and overall summary.

## Enrichers

### `retrovue enricher list-types`

Show all enricher types known to the system (both ingest and playout scopes).

**Output**: List of enricher types with scope and description.

### `retrovue enricher add --type <type> --name <label> [config...]`

Create an enricher instance. Each enricher type defines its own config params.

**Required**:

- `--type`: Enricher type
- `--name`: Human-readable label

**Behavior**:

- If called with `--help` and no `--type`, print generic usage plus available types.
- If called with `--type <type> --help`, print that enricher's specific parameter contract.

### `retrovue enricher list`

List configured enricher instances with:

- enricher_id
- type
- scope (ingest or playout)
- name/label

### `retrovue enricher update <enricher_id> [config...]`

Update enricher configuration.

**Parameters**: Same as add command for the enricher type.

### `retrovue enricher remove <enricher_id>`

Remove enricher instance.

**Behavior**: Confirms removal and shows affected collections/channels.

## Producers and Channels

### `retrovue producer list-types`

Show available producer types (linear, prevue, yule-log, etc.).

**Output**: List of producer types with descriptions.

### `retrovue producer add --type <type> --name <label> [config...]`

Create a producer instance.

**Required**:

- `--type`: Producer type
- `--name`: Human-readable label

**Behavior**:

- If called with `--help` and no `--type`, print generic usage plus available types.
- If called with `--type <type> --help`, print that producer's specific parameter contract.

### `retrovue producer list`

List configured producer instances.

**Output**: Table showing producer_id, type, name, status.

### `retrovue producer update <producer_id> [config...]`

Update producer configuration.

**Parameters**: Same as add command for the producer type.

### `retrovue producer remove <producer_id>`

Remove producer instance.

**Behavior**: Confirms removal and shows affected channels.

### `retrovue channel list`

Show Channels and for each:

- channel_id
- name/branding label
- active producer instance
- attached playout enrichers (with priority)

### `retrovue channel attach-enricher <channel_id> <enricher_id> --priority <n>`

Attach a playout-scope enricher to the Channel. Enrichers run in ascending priority.

**Parameters**:

- `channel_id`: Target channel
- `enricher_id`: Enricher to attach
- `--priority`: Priority order (lower numbers run first)

### `retrovue channel detach-enricher <channel_id> <enricher_id>`

Remove enricher from channel.

## Help Expectations

### `retrovue source add --help`

Prints generic help and lists all known source types.

### `retrovue source add --type <type> --help`

Prints the specific required/optional params for that type. This help content is provided by the importer plugin's registered param spec, not hardcoded in the CLI.

### `retrovue enricher add --help`

Prints generic help and lists all known enricher types.

### `retrovue enricher add --type <type> --help`

Prints the specific required/optional params for that enricher type.

### `retrovue producer add --help`

Prints generic help and lists all producer types.

### `retrovue producer add --type <type> --help`

Prints the specific required/optional params for that producer type.

## CLI contract requirements

This CLI contract defines the complete operator interface for RetroVue. All commands must:

- Follow consistent naming patterns
- Provide appropriate help text
- Support both individual and bulk operations
- Show clear progress indicators
- Validate inputs before execution
- Provide meaningful error messages

Implementation must match this contract exactly. Any deviation requires updating this documentation first.

## See also

- [Architecture overview](../architecture/ArchitectureOverview.md) - System architecture and design
- [Domain: Source](../domain/Source.md) - External content providers
- [Domain: Enricher](../domain/Enricher.md) - Content enrichment system
- [Runtime: Channel manager](../runtime/ChannelManager.md) - Channel runtime operations
- [Developer: Plugin authoring](../developer/PluginAuthoring.md) - Plugin development guide
