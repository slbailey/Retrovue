# Retrovue CLI Contract

This document is a binding contract for the Retrovue CLI.

It defines:

- Command shapes (`retrovue <noun> <verb> [options]`)
- Required flags
- Help text guarantees
- Exit code expectations
- Safety rules for destructive commands (confirmation, `--force`, `--dry-run`)
- JSON output expectations where applicable

## Contract Testing Pattern

Each CLI command follows the **one contract per noun/verb** pattern with **two test files**:

1. **CLI Contract Test**: `tests/contracts/test_{noun}_{verb}_contract.py`

   - Validates CLI syntax, flags, prompts, help text, output format
   - Tests operator-facing behavior and user experience
   - Ensures stable command interface

2. **Data Contract Test**: `tests/contracts/test_{noun}_{verb}_data_contract.py`
   - Validates database persistence and data integrity
   - Tests actual data changes, side effects, and cleanup
   - Ensures correct database state transitions

All tests in `tests/contracts/` that assert CLI behavior refer to this document.

Changing any CLI surface (command names, flags, prompts, exit codes, output format)
without updating this file FIRST is treated as a breaking change.

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

### `retrovue source discover <source_id>`

Discover and add collections (libraries) from a source to the repository.

**Output**: Shows discovered collections and adds them to the database (disabled by default).

### `retrovue source <source_id> ingest`

Ingest all sync-enabled, ingestible collections from a source.

**Output**: Shows ingest results and asset counts for each collection.

**Examples**:

- `retrovue source "My Plex Server" ingest`
- `retrovue source plex-5063d926 ingest`

### `retrovue source <source_id> attach-enricher <enricher_id> [--priority <n>]`

Attach an ingest-scope enricher to all collections in a source.

**Parameters:**

- `source_id`: Source to attach enricher to (can be ID, external ID, or name)
- `enricher_id`: Enricher to attach
- `--priority`: Execution priority (lower numbers run first, default: 1)

**Behavior:**

- Attaches the specified enricher to all collections under the source
- Enricher will run during ingest process for each collection
- Priority determines execution order (lower numbers run first)

**Examples:**

- `retrovue source "My Plex Server" attach-enricher enricher-ffprobe-1`
- `retrovue source plex-5063d926 attach-enricher enricher-metadata-1 --priority 2`
- `retrovue source "My Plex Server" attach-enricher enricher-llm-1 --priority 3`

### `retrovue source <source_id> detach-enricher <enricher_id>`

Detach an ingest-scope enricher from all collections in a source.

**Parameters:**

- `source_id`: Source to detach enricher from (can be ID, external ID, or name)
- `enricher_id`: Enricher to detach

**Behavior:**

- Removes the specified enricher from all collections under the source
- Enricher will no longer run during ingest process for each collection

**Examples:**

- `retrovue source "My Plex Server" detach-enricher enricher-ffprobe-1`
- `retrovue source plex-5063d926 detach-enricher enricher-metadata-1`
- `retrovue source "My Plex Server" detach-enricher enricher-llm-1`

## Collections

### `retrovue collection list --source <source_id>`

Show Collections for a Source. For each:

- collection_id (UUID from database)
- external_id (Plex library key or external identifier)
- display_name
- source_path (plex_section_ref from config)
- sync_enabled (true/false, can only be enabled if ingestible)
- ingestable (derived from path reachability, independent of sync status)
- path_mappings (list of plex_path -> local_path mappings)

**Output**: Table showing collection details with real database data including path mappings.

**Note**: This command now queries the actual database for collections. Collections must be discovered from sources using `retrovue source discover` before they will appear in this list.

### `retrovue collection list-all`

Show all Collections across all Sources. For each:

- collection_id (UUID from database, full format for copy/paste)
- name (collection display name)
- source (source name and type)
- sync_enabled (true/false, can only be enabled if ingestible)
- ingestible (derived from path reachability, independent of sync status)

**Output**: Table showing all collections with source information and status.

**Note**: This command provides a unified view of all collections across the entire RetroVue system. The full UUID is displayed for easy copy/paste to other commands.

### `retrovue collection update <collection_id> --sync-enabled <true|false> [--local-path <path>]`

Enable/disable ingest for that Collection. Configure or change the local path mapping for that Collection.

**Parameters**:

- `collection_id`: Collection UUID, external ID, or name (case-insensitive search)
- `--sync-enabled`: Enable or disable collection sync (can only enable if collection is ingestible)
- `--local-path`: Override local path mapping

**Sync Enablement Rules**:

- Sync can only be enabled if the collection is ingestible (has valid, accessible local paths)
- If sync is enabled but collection becomes non-ingestible, sync will not execute
- Disabling sync is always allowed

**Collection Identification**: The command supports multiple ways to identify collections:

- Full UUID: `2a3cd8d1-2345-6789-abcd-ef1234567890` (always unique)
- External ID: `18` (Plex library key, unique per source)
- Name: `"TV Shows"` (case-insensitive, but must be unique)

**Note**: If multiple collections have the same name, the command will show all matches and require you to use the full UUID for disambiguation.

### `retrovue collection attach-enricher <collection_id> <enricher_id> --priority <n>`

Attach an ingest-scope enricher to this Collection.

**Parameters**:

- `collection_id`: Target collection
- `enricher_id`: Enricher to attach
- `--priority`: Priority order (lower numbers run first)

### `retrovue collection detach-enricher <collection_id> <enricher_id>`

Remove enricher from collection.

### `retrovue collection delete <collection_id> [--force]`

Delete a collection and all its associated data.

**Parameters**:

- `collection_id`: Collection UUID, external ID, or name (case-insensitive search)
- `--force`: Force deletion without confirmation prompt

**Collection Identification**: The command supports multiple ways to identify collections:

- Full UUID: `2a3cd8d1-2345-6789-abcd-ef1234567890` (always unique)
- External ID: `18` (Plex library key, unique per source)
- Name: `"TV Shows"` (case-insensitive, but must be unique)

**Note**: If multiple collections have the same name, the command will show all matches and require you to use the full UUID for disambiguation.

**Behavior**:

- Confirms removal and shows affected path mappings
- Deletes the collection and all associated PathMapping records
- This action cannot be undone

### `retrovue collection wipe <collection_id> [--force] [--dry-run] [--json]`

**NUCLEAR OPTION**: Completely wipe a collection and ALL its associated data.

This command performs a complete cleanup that deletes:

- All assets from the collection
- All episodes from the collection
- All seasons (if no episodes remain)
- All TV shows/titles (if no seasons remain)
- All review queue entries for assets from the collection
- All catalog entries for assets from the collection

**IMPORTANT**: The collection itself and its path mappings are preserved for re-ingest.

**Parameters**:

- `collection_id`: Collection UUID, external ID, or name (case-insensitive search)
- `--force`: Force wipe without confirmation prompt
- `--dry-run`: Show what would be deleted without actually deleting
- `--json`: Output detailed statistics in JSON format

**Collection Identification**: Same as `delete` command above.

**Safety Features**:

- **Dry Run**: Always use `--dry-run` first to see what will be deleted
- **Confirmation**: Must type "DELETE" to confirm (unless `--force`)
- **Detailed Reporting**: Shows exact counts of what will be deleted
- **Transaction Safety**: All changes rolled back if any step fails

**Examples**:

```bash
# See what would be deleted (safe)
retrovue collection wipe "TV Shows" --dry-run

# Get detailed stats in JSON
retrovue collection wipe "TV Shows" --dry-run --json

# Actually wipe (with confirmation)
retrovue collection wipe "TV Shows"

# Force wipe without confirmation (dangerous!)
retrovue collection wipe "TV Shows" --force
```

**Complete Fresh Start Workflow**:

```bash
# 1. See what will be deleted
retrovue collection wipe "TV Shows" --dry-run

# 2. Actually wipe everything
retrovue collection wipe "TV Shows"

# 3. Re-discover the collection
retrovue source discover <source_id>

# 4. Re-ingest from scratch
retrovue collection ingest "TV Shows"
```

**⚠️ WARNING**: This action cannot be undone. Use with extreme caution!

### `retrovue collection <collection_id> ingest [--title <title>] [--season <n>] [--episode <n>]`

Ingest content from a collection.

**Parameters**:

- `collection_id`: Collection UUID, external ID, or name (case-insensitive search)
- `--title`: Specific title to ingest (movie/show name)
- `--season`: Season number (for TV shows)
- `--episode`: Episode number (requires --season)

**Modes**:

1. **Full collection**: `retrovue collection "TV Shows" ingest`
2. **Specific title**: `retrovue collection "Movies" ingest --title "Airplane (2012)"`
3. **TV show**: `retrovue collection "TV Shows" ingest --title "The Big Bang Theory"`
4. **Season**: `retrovue collection "TV Shows" ingest --title "The Big Bang Theory" --season 1`
5. **Episode**: `retrovue collection "TV Shows" ingest --title "The Big Bang Theory" --season 1 --episode 1`

**Examples**:

- `retrovue collection "TV Shows" ingest`
- `retrovue collection "Movies" ingest --title "Airplane (2012)"`
- `retrovue collection "TV Shows" ingest --title "The Big Bang Theory" --season 1`
- `retrovue collection "TV Shows" ingest --title "The Big Bang Theory" --season 1 --episode 1`

## Ingest

Ingest commands are integrated into source and collection management:

- `retrovue source <source_id> ingest` - Ingest all collections from a source
- `retrovue collection <collection_id> ingest` - Ingest a specific collection
- `retrovue collection <collection_id> ingest --title <title>` - Ingest specific content

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
