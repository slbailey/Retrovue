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

- `retrovue ingest` - Content ingestion operations
- `retrovue assets` - Asset management operations
- `retrovue review` - Review queue operations

## Global Options

All commands support these global options:

- `--json` - Output results in JSON format
- `--help` - Show help for the command

## Commands

### Ingest Commands

#### `retrovue ingest run`

Run content ingestion from a source.

```bash
# Ingest from filesystem
retrovue ingest run filesystem:/path/to/media

# Ingest with specific library and enrichers
retrovue ingest run plex --library-id 1 --enrichers ffprobe

# Output in JSON format
retrovue ingest run filesystem:/media --json
```

**Arguments:**

- `source` - Source identifier (e.g., 'plex', 'filesystem:/path')

**Options:**

- `--library-id TEXT` - Library ID to process
- `--enrichers TEXT` - Comma-separated list of enrichers (e.g., 'ffprobe')
- `--json` - Output in JSON format

### Assets Commands

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
# 1. Ingest content from filesystem
retrovue ingest run filesystem:/media/movies --enrichers ffprobe

# 2. List discovered assets
retrovue assets list --status pending

# 3. Check review queue
retrovue review list

# 4. Resolve a review item
retrovue review resolve 123e4567-e89b-12d3-a456-426614174000 987fcdeb-51a2-43d1-b456-426614174000

# 5. List canonical assets
retrovue assets list --status canonical
```

### Automation Script

```bash
#!/bin/bash
# Automated content processing

echo "Starting content ingestion..."
retrovue ingest run filesystem:/media --json > ingest_results.json

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
retrovue ingest --help
retrovue assets list --help
retrovue review resolve --help
```
