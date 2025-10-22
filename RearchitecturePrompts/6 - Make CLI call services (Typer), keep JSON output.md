Goal: Migrate CLI to call application services instead of touching DB. Keep old commands, but rewire internals.

Commands (Typer):

- retrovue ingest run --source plex|filesystem --enrichers ffprobe
- retrovue assets list --status pending|canonical --format json
- retrovue review list --format json
- retrovue review resolve --id <id> --episode-id <episode_id> --notes "..."

Acceptance criteria:

- Commands return machine-friendly JSON when --format json is provided.
- No direct DB session creation inside CLI files; all via app services.
- Add tests for command output shape (snapshot tests okay).

Touch files:

- src/retrovue/cli/main.py (new or refactor)
- tests/cli/test_cli.py
