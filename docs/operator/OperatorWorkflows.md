_Related: [Operator CLI](CLI.md) • [Domain: Enricher](../domain/Enricher.md) • [Runtime: Channel manager](../runtime/ChannelManager.md)_

# Operator workflows

## Purpose

Give operators the typical flows they'll run using the CLI.

This document references the CLI contract. The CLI contract is the source of truth for syntax.

## Common workflows

### 1. Add a new Source and ingest it

1. List available Source types:
   - `retrovue source list-types`
2. Add a new Source instance:
   - `retrovue source add --type <type> --name <label> ...`
3. Sync collections from that Source:
   - `retrovue source sync-collections <source_id>`
4. View collections and enable ingest on specific ones:
   - `retrovue collection list --source <source_id>`
   - `retrovue collection update <collection_id> --sync-enabled true --local-path /mnt/media/...`
5. Ingest:
   - `retrovue ingest run <collection_id>`  
     or  
     `retrovue ingest run --source <source_id>`

### 2. Attach ingest enrichers

1. List available enricher types:
   - `retrovue enricher list-types`
2. Create an enricher instance:
   - `retrovue enricher add --type <type> --name <label> ...`
3. Attach it to the collection with a priority:
   - `retrovue collection attach-enricher <collection_id> <enricher_id> --priority <n>`

Lower priority number means it runs earlier.

### 3. Configure a Channel for playout

1. Create a Producer instance:
   - `retrovue producer add --type <type> --name <label> ...`
2. Confirm the Channel is associated with the correct Producer:
   - `retrovue channel list`
3. Configure playout enrichers and attach them with priorities:
   - `retrovue channel attach-enricher <channel_id> <enricher_id> --priority <n>`

### 4. Audit playout health

- `retrovue channel list` shows the active Producer and attached playout enrichers.
- As-run logs (internal) confirm what actually aired vs what was expected.

See also:

- [CLI contract](CLI.md)
- [Enricher](../domain/Enricher.md)
- [Channel manager](../runtime/ChannelManager.md)
