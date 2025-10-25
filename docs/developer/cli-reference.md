# Retrovue CLI

The Retrovue CLI provides a command-line interface for managing your media library, content ingestion, and review workflows.

## Installation

After installing Retrovue, the CLI is available as the `retrovue` command:

```bash
# Install in development mode
pip install -e .

# The CLI is now available
retrovue --help
```

## Command Structure

The CLI is organized into command groups:

- `retrovue assets` - Ingest world (content discovery, metadata, library operations)
- `retrovue catalog` - Broadcast world (airable, canonical-approved assets for scheduling)
- `retrovue review` - Review queue operations
- `retrovue test` - Testing operations for runtime components

## Global Options

All commands support these global options:

- `--json` - Output results in JSON format
- `--help` - Show help for the command

## Commands

### Test Commands

#### `retrovue test broadcast-day-alignment`

Test broadcast day alignment for HBO-style 05:00–07:00 scenario.

```bash
# Basic test with default settings
retrovue test broadcast-day-alignment

# Test with specific channel and timezone
retrovue test broadcast-day-alignment --channel "hbo_east" --timezone "America/New_York"

# JSON output for programmatic use
retrovue test broadcast-day-alignment --json
```

**Options:**

- `--channel, -c` - Test channel ID (default: "test_channel_1")
- `--timezone, -t` - Channel timezone (default: "America/New_York")
- `--json` - Output results in JSON format

**Purpose:**
Validates ScheduleService's broadcast-day logic and rollover handling. Tests the HBO-style 05:00–07:00 scenario to ensure proper broadcast day classification and seamless playback across the 06:00 rollover boundary.

#### `retrovue test masterclock`

Test MasterClock functionality with live examples.

```bash
# Basic MasterClock test
retrovue test masterclock

# Test with specific precision and timezone
retrovue test masterclock --precision millisecond --timezone "America/New_York"

# JSON output
retrovue test masterclock --json
```

**Options:**

- `--precision, -p` - Time precision: second, millisecond, microsecond (default: millisecond)
- `--timezone, -t` - Test timezone (default: "America/New_York")
- `--json` - Output results in JSON format

### Assets Commands (Ingest World)

#### `retrovue assets run`

Run content ingestion from a source.

```bash
# Ingest from filesystem
retrovue assets run filesystem:/path/to/media

# Ingest with specific library and enrichers
retrovue assets run plex --library-id 1 --enrichers ffprobe

# Output in JSON format
retrovue assets run filesystem:/media --json
```

**Arguments:**

- `source` - Source identifier (e.g., 'plex', 'filesystem:/path')

**Options:**

- `--library-id TEXT` - Library ID to process
- `--enrichers TEXT` - Comma-separated list of enrichers (e.g., 'ffprobe')
- `--json` - Output in JSON format

### Catalog Commands (Broadcast World)

#### `retrovue catalog add`

Add a new catalog entry (airable, canonical-approved asset).

```bash
# Add a canonical asset to the broadcast catalog
retrovue catalog add --title "Cheers S01E01" --duration 1440 --tags "sitcom" --path "/media/cheers01.mkv" --canonical true

# Add without canonical approval (not yet airable)
retrovue catalog add --title "New Episode" --duration 1800 --tags "drama" --path "/media/new.mkv" --canonical false
```

**Options:**

- `--title` - Asset title as it should appear on-air
- `--duration` - Duration in seconds
- `--tags` - Comma-separated tags used by scheduling rules
- `--path` - Playable file path
- `--canonical` - Mark as approved-for-air
- `--json` - Output as JSON

#### `retrovue catalog update`

Update an existing catalog entry.

```bash
# Approve an asset for broadcast
retrovue catalog update --id 12 --canonical true

# Update metadata
retrovue catalog update --id 12 --title "Updated Title" --tags "sitcom,comedy"
```

**Options:**

- `--id` - Catalog ID
- `--title` - Updated title
- `--duration` - Updated duration in seconds
- `--tags` - Updated comma-separated tags
- `--path` - Updated file path
- `--canonical` - Updated canonical status
- `--json` - Output as JSON

#### `retrovue catalog list`

List catalog entries (airable assets).

```bash
# List all catalog entries
retrovue catalog list

# List only canonical (approved) assets
retrovue catalog list --canonical-only

# Filter by tag
retrovue catalog list --tag sitcom

# JSON output
retrovue catalog list --json
```

**Options:**

- `--canonical-only` - Show only assets approved for scheduling
- `--tag` - Filter by tag (e.g. sitcom)
- `--json` - Output in JSON format

### Assets Commands (Ingest World)

#### `retrovue assets list`

List assets with optional status filtering.

```bash
# List all assets
retrovue assets list

# List only pending assets
retrovue assets list --status pending

# List only canonical assets
retrovue assets list --status canonical

# Output in JSON format
retrovue assets list --json
```

**Options:**

- `--status [pending|canonical|all]` - Filter by asset status (default: all)
- `--json` - Output in JSON format

#### `retrovue assets select`

Select an asset (returning UUID + lightweight metadata).

This is the primary command for choosing assets. Use this UUID with `retrovue assets get <uuid> --json` to retrieve full details.

```bash
# Select a random episode from a series (positional argument)
retrovue assets select "Cheers" --mode random --json

# Select a random episode from a series (flag argument)
retrovue assets select --series "Cheers" --mode random --json

# Select the next episode in sequence (S01E01 when no history exists)
retrovue assets select --series "Cheers" --mode sequential

# Select by genre (when implemented)
retrovue assets select --genre horror --mode random --json

# Typical workflow: select then get full details
retrovue assets select "Cheers" --mode random --json \
| jq -r .uuid \
| xargs retrovue assets get --json
```

**Arguments:**

- `SERIES` - Series name (positional argument, mutually exclusive with --series)

**Options:**

- `--series TEXT` - Series name (flag argument, mutually exclusive with positional)
- `--genre TEXT` - Filter by genre (not yet implemented)
- `--mode [random|sequential]` - Selection mode (default: random)
- `--json` - Output in JSON format

**Selection Modes:**

- `random` - Choose a random episode from the series
- `sequential` - Choose the next episode in natural order (by season_number, episode_number)
  - For now, if there is no play history, picks the first episode (S01E01)
  - TODO: Add per-channel last-played logic

**JSON Output Format:**

```json
{
  "uuid": "b4739f5c-7f91-4937-a7b2-4a5ba8ef4249",
  "id": 5,
  "title": "The Tortelli Tort",
  "series_title": "Cheers",
  "season_number": 1,
  "episode_number": 3,
  "kind": "episode",
  "selection": {
    "mode": "random",
    "criteria": {
      "series": "Cheers"
    }
  }
}
```

**Human Output Format:**

```
Cheers S01E03 "The Tortelli Tort"  b4739f5c-7f91-4937-a7b2-4a5ba8ef4249
```

**Notes:**

- Numbers must be numeric (not strings)
- Use this UUID with `retrovue assets get <uuid> --json` to retrieve file_path/duration/etc.
- Selection requires at least one filter: series or genre
- You cannot provide both a positional argument and the --series flag

#### `retrovue assets series` (DEPRECATED)

List series or episodes for a specific series.

**DEPRECATED:** When a series is provided, use `assets select` to choose an episode.

```bash
# List all available series (still works)
retrovue assets series

# Show episodes for a specific series (DEPRECATED - use assets select)
retrovue assets series "Batman TAS"  # DEPRECATED: Use 'assets select "Batman TAS"'
retrovue assets series --series "Batman TAS"  # DEPRECATED: Use 'assets select --series "Batman TAS"'

# Output in JSON format
retrovue assets series "Batman TAS" --json  # DEPRECATED: Use 'assets select "Batman TAS" --json'
retrovue assets series --series "Batman TAS" --json  # DEPRECATED: Use 'assets select --series "Batman TAS" --json'
```

**Arguments:**

- `SERIES` - Series name (positional argument, mutually exclusive with --series)

**Options:**

- `--series TEXT` - Series name (flag argument, mutually exclusive with positional)
- `--json` - Output in JSON format

**Deprecation Behavior:**

When a series is provided, this command:

1. Prints a deprecation warning to stderr
2. Delegates internally to `assets select` with the same series and `--mode random`
3. Returns the same selection JSON as `assets select` (not the old seasons tree)

When no series is provided, it still lists all series as `{"series": [...]}`.

**JSON Output Format:**

When requesting a specific series (DEPRECATED), the JSON output now matches `assets select`:

```json
{
  "uuid": "b4739f5c-7f91-4937-a7b2-4a5ba8ef4249",
  "id": 5,
  "title": "The Tortelli Tort",
  "series_title": "Cheers",
  "season_number": 1,
  "episode_number": 3,
  "kind": "episode",
  "selection": {
    "mode": "random",
    "criteria": {
      "series": "Cheers"
    }
  }
}
```

When listing all series, the JSON output is:

```json
{
  "series": ["Batman TAS", "Frasier", "Cheers"]
}
```

**Notes:**

- Numeric fields (id, season_number, episode_number) are returned as numbers, not strings
- You cannot provide both a positional argument and the --series flag
- Use `assets select` for new code instead of this deprecated command

### Review Commands

#### `retrovue review list`

List items in the review queue.

```bash
# List all review items
retrovue review list

# Output in JSON format
retrovue review list --json
```

#### `retrovue review resolve`

Resolve a review queue item by associating it with an episode.

```bash
# Resolve a review item
retrovue review resolve <review-id> <episode-id>

# Resolve with notes
retrovue review resolve <review-id> <episode-id> --notes "Manually verified"

# Output in JSON format
retrovue review resolve <review-id> <episode-id> --json
```

**Arguments:**

- `review_id` - Review ID to resolve
- `episode_id` - Episode ID to associate

**Options:**

- `--notes TEXT` - Resolution notes
- `--json` - Output in JSON format

## JSON Output

When using the `--json` flag, all commands output structured JSON data that can be easily parsed by other tools or scripts.

### Example JSON Output

**Ingest Response:**

```json
{
  "source": "filesystem:/media",
  "library_id": null,
  "enrichers": ["ffprobe"],
  "counts": {
    "discovered": 10,
    "registered": 8,
    "enriched": 6,
    "canonicalized": 4,
    "queued_for_review": 2
  }
}
```

**Assets List Response:**

```json
{
  "assets": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "uri": "file:///media/movie.mp4",
      "size": 1048576,
      "duration_ms": 7200000,
      "video_codec": "h264",
      "audio_codec": "aac",
      "container": "mp4",
      "hash_sha256": "abc123...",
      "discovered_at": "2024-01-01T12:00:00Z",
      "canonical": true
    }
  ],
  "total": 1,
  "status_filter": "canonical"
}
```

## Error Handling

The CLI provides clear error messages and appropriate exit codes:

- **Exit code 0**: Success
- **Exit code 1**: General error (invalid arguments, service errors)
- **Exit code 2**: Not found (asset, review, etc.)

## Examples

### Complete Workflow

```bash
# 1. Ingest content from filesystem (ingest world)
retrovue assets run filesystem:/media/movies --enrichers ffprobe

# 2. List discovered assets (ingest world)
retrovue assets list --status pending

# 3. Check review queue
retrovue review list

# 4. Resolve a review item
retrovue review resolve 123e4567-e89b-12d3-a456-426614174000 987fcdeb-51a2-43d1-b456-426614174000

# 5. Add approved content to broadcast catalog (broadcast world)
retrovue catalog add --title "Approved Movie" --duration 7200 --tags "action" --path "/media/movie.mkv" --canonical true

# 6. List airable assets (broadcast world)
retrovue catalog list --canonical-only
```

### Automation Script

```bash
#!/bin/bash
# Automated content processing

echo "Starting content ingestion..."
retrovue assets run filesystem:/media --json > ingest_results.json

echo "Processing review queue..."
retrovue review list --json > review_queue.json

# Process review items automatically
jq -r '.reviews[] | select(.confidence < 0.5) | .id' review_queue.json | while read review_id; do
    echo "Auto-resolving low-confidence review: $review_id"
    retrovue review resolve "$review_id" "auto-resolved-episode" --notes "Auto-resolved due to low confidence"
done
```

## Integration

The CLI is designed to integrate seamlessly with the Retrovue service layer:

- **Service-oriented**: All commands call application services, never direct database access
- **Consistent responses**: Uses the same Pydantic models as the API
- **Transaction safety**: Proper commit/rollback handling for all operations
- **JSON-first**: Structured output for easy integration with other tools

## Troubleshooting

### Common Issues

**"Module not found" errors:**

```bash
# Make sure you've installed the package
pip install -e .
```

**Database connection errors:**

```bash
# Check your database configuration
# The CLI uses the same database settings as the API
```

**Permission errors:**

```bash
# Ensure you have read/write access to the media directories
# and database files
```

### Getting Help

```bash
# Get help for any command
retrovue --help
retrovue assets --help
retrovue catalog --help
retrovue assets list --help
retrovue catalog list --help
retrovue review resolve --help
```

### Play Commands (IPTV Streaming)

#### `retrovue play`

Resolve an episode from your content library and expose it as a live MPEG-TS stream for IPTV playback.

```bash
# Start streaming a specific episode on the default port
retrovue play "Cheers" --season 1 --episode 3

# Enable verbose debugging (FFmpeg -loglevel debug) and input validation
retrovue play "Cheers" --season 1 --episode 3 --debug

# Kill any process bound to the chosen port before starting
retrovue play "Cheers" --season 1 --episode 3 --kill-existing

# Custom HTTP port
retrovue play "Cheers" --season 1 --episode 3 --port 8080

# Transcode explicitly (H.264/AAC)
retrovue play "Cheers" --season 1 --episode 3 --transcode
```

**Arguments:**

- `SERIES` - Series title (e.g., "Cheers")

**Options:**

- `--season, -s INTEGER` - Season number (required)
- `--episode, -e INTEGER` - Episode number (required)
- `--channel-id, -c INTEGER` - Channel ID used in the streaming URL (default: 1)
- `--port, -p INTEGER` - HTTP port to serve MPEG-TS streams (default: 8000)
- `--transcode` - Force H.264/AAC output for broad compatibility
- `--debug` - Enable verbose FFmpeg logging and input validation
- `--kill-existing` - Kill any process already bound to the specified port

The stream will be available at:

```
http://localhost:<port>/iptv/channel/<channel_id>.ts
```

#### `retrovue play-channel`

Start the IPTV server and expose a single channel by channel ID.

```bash
# Start channel 1 on the default port
retrovue play-channel 1

# Kill existing process on port 8000 before starting
retrovue play-channel 1 --kill-existing

# Custom port
retrovue play-channel 1 --port 9000
```

**Options:**

- `--port, -p INTEGER` - HTTP port (default: 8000)
- `--kill-existing` - Kill any process already bound to the specified port

### Module Entry Points

The FFmpeg command builder can be imported from the streaming package:

```python
from retrovue.streaming.ffmpeg_cmd import build_cmd
```

You can also invoke it as a Python module (for quick availability checks):

```bash
python -m retrovue.streaming.ffmpeg_cmd
```
