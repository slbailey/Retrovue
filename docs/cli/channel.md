# Channel Commands

_Related: [Channel Contracts](../contracts/resources/ChannelContract.md) • [Channel Domain](../domain/Channel.md)_

## Overview

Channel commands manage broadcast channels and their configuration.

## Commands

### `retrovue channel list`

List all channels.

**Syntax:**
```bash
retrovue channel list [--json] [--test-db]
```

**Examples:**
```bash
retrovue channel list
retrovue channel list --json
```

### `retrovue channel add`

Create a new broadcast channel.

**Syntax:**
```bash
retrovue channel add --name <name> --grid-size-minutes <size> [options] [--json] [--test-db]
```

**Required Options:**
- `--name <name>` - Channel name (unique)
- `--grid-size-minutes <size>` - Grid size in minutes (15, 30, or 60)

**Optional Options:**
- `--grid-offset-minutes <offset>` - Grid alignment offset (default: 0)
- `--broadcast-day-start <time>` - Programming day anchor in HH:MM format (default: 06:00)
- `--active/--inactive` - Initial active state (default: active)
- `--json` - Output in JSON format
- `--test-db` - Use test database

**Examples:**
```bash
retrovue channel add --name "RetroToons" --grid-size-minutes 30
retrovue channel add --name "MidnightMovies" --grid-size-minutes 60 --broadcast-day-start "05:00"
```

### `retrovue channel show`

Show detailed channel information.

**Syntax:**
```bash
retrovue channel show <channel-id> [--json] [--test-db]
```

**Arguments:**
- `<channel-id>` - Channel UUID or slug

**Examples:**
```bash
retrovue channel show retrotoons
retrovue channel show 550e8400-e29b-41d4-a716-446655440000 --json
```

### `retrovue channel update`

Update channel configuration.

**Syntax:**
```bash
retrovue channel update <channel-id> [options] [--json] [--test-db]
```

**Arguments:**
- `<channel-id>` - Channel UUID or slug

**Options:**
- `--name <name>` - Update channel name
- `--grid-size-minutes <size>` - Update grid size
- `--grid-offset-minutes <offset>` - Update grid offset
- `--broadcast-day-start <time>` - Update programming day anchor
- `--active/--inactive` - Update active state

**Examples:**
```bash
retrovue channel update retrotoons --name "RetroToons HD"
retrovue channel update retrotoons --broadcast-day-start "07:00"
```

### `retrovue channel validate`

Validate channel configuration and dependencies.

**Syntax:**
```bash
retrovue channel validate <channel-id> [--json] [--test-db]
```

**Examples:**
```bash
retrovue channel validate retrotoons
retrovue channel validate retrotoons --json
```

## See also

- [Channel Add Contract](../contracts/resources/ChannelAddContract.md) - Create channel behavior
- [Channel Update Contract](../contracts/resources/ChannelUpdateContract.md) - Update channel behavior
- [Channel Domain](../domain/Channel.md) - Domain model

