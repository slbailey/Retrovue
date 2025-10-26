# Collection Wipe Contract

## Purpose

Define the contract for the `retrovue collection wipe` command, which provides a complete cleanup mechanism for collections and all their associated data.

## Command Signature

```bash
retrovue collection wipe <collection_identifier> [--force] [--dry-run] [--json]
```

## Parameters

### Required

- `collection_identifier`: Collection UUID, external ID, or name (case-insensitive search)

### Optional

- `--force`: Force wipe without confirmation prompt
- `--dry-run`: Show what would be deleted without actually deleting
- `--json`: Output detailed statistics in JSON format

## Behavior Contract

### 1. Unit of Work Requirements

The command MUST follow the Unit of Work paradigm:

- **Atomicity**: All-or-nothing operation - either complete success or complete rollback
- **Pre-flight Validation**: Validate all prerequisites before making any changes
- **Post-operation Validation**: Verify database consistency after all changes
- **Transaction Isolation**: Run in a single database transaction
- **Error Handling**: Roll back on any failure and provide clear error messages

### 2. Collection Identification

The command MUST:

- Accept collection UUID, external ID, or name as identifier
- Perform case-insensitive search for name matches
- Return error if no collection found
- Return error if multiple collections match name (ambiguous)

### 3. Pre-flight Validation

The command MUST validate before any changes:

- Collection exists and is accessible
- No conflicting operations in progress
- All required dependencies are available
- Database constraints can be satisfied
- Business rules are met

### 4. Asset Discovery

The command MUST:

- Find assets using `collection_id` for new assets (with collection_id field)
- Fall back to path mapping patterns for legacy assets (without collection_id)
- Combine both sets to get complete asset list
- Use PostgreSQL regexp for path matching to handle Windows paths

### 5. Deletion Order

The command MUST delete in this exact order:

1. Review queue entries (by asset_id)
2. Episode-asset junction records (by asset_id)
3. Assets (by asset_id)
4. Orphaned episodes (episodes with no remaining assets)
5. Orphaned seasons (seasons with no remaining episodes)
6. Orphaned titles (titles with no remaining seasons)

**IMPORTANT**: The command MUST NOT delete:

- Path mappings (preserved for re-ingest)
- The collection itself (preserved for re-ingest)

### 6. Post-operation Validation

The command MUST validate after all changes:

- No orphaned records exist
- Collection and path mappings are preserved
- All database constraints are satisfied
- Database state is consistent

### 7. Safety Features

The command MUST:

- Require confirmation unless `--force` is specified
- Show detailed statistics before deletion
- Support dry-run mode to preview changes
- Use database transactions for atomicity
- Provide JSON output for programmatic use

### 8. Error Handling

The command MUST:

- Validate collection exists before proceeding
- Handle database constraint violations gracefully
- Provide clear error messages for common failures
- Roll back transactions on any failure
- Preserve database consistency on failure

## Output Contract

### Dry Run Mode

```
Collection wipe analysis for: <collection_name>
  Collection ID: <uuid>
  External ID: <external_id>

Items that will be deleted:
  Review queue entries: <count>
  Episode-asset links: <count>
  Assets: <count>
  Episodes: <count>
  Seasons: <count>
  TV Shows/Titles: <count>

DRY RUN - No changes made
```

### JSON Output

```json
{
  "collection": {
    "id": "<uuid>",
    "name": "<name>",
    "external_id": "<external_id>"
  },
  "items_to_delete": {
    "review_queue_entries": <count>,
    "episode_assets": <count>,
    "assets": <count>,
    "episodes": <count>,
    "seasons": <count>,
    "titles": <count>
  },
  "dry_run": true
}
```

### Confirmation Prompt

```
⚠️  WARNING: This will permanently delete ALL data for collection "TV Shows"
   - 10,316 assets
   - 10,332 episodes
   - 10,332 seasons
   - 10,332 TV shows/titles
   - 24,185 review queue entries

This action cannot be undone!

Type 'DELETE' to confirm:
```

## Database Schema Requirements

### Asset Entity

```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL UNIQUE,
    uri TEXT NOT NULL UNIQUE,
    collection_id UUID REFERENCES source_collections(id) ON DELETE SET NULL,
    -- ... other fields
);

CREATE INDEX ix_assets_collection_id ON assets(collection_id);
```

### Relationships

- `Asset.collection_id` → `SourceCollection.id` (nullable, SET NULL on delete)
- `ReviewQueue.asset_id` → `Asset.id` (CASCADE on delete)
- `EpisodeAsset.asset_id` → `Asset.id` (CASCADE on delete)
- `EpisodeAsset.episode_id` → `Episode.id` (CASCADE on delete)
- `Episode.season_id` → `Season.id` (CASCADE on delete)
- `Season.title_id` → `Title.id` (CASCADE on delete)

## Implementation Requirements

### 1. Unit of Work Implementation

The implementation MUST follow the Unit of Work pattern:

```python
def wipe_collection(collection_id: str, options: WipeOptions) -> WipeResult:
    """
    Completely wipe a collection and all associated data.

    Pre-conditions:
    - Collection exists and is accessible
    - No conflicting operations in progress
    - All dependencies are identified

    Post-conditions:
    - All collection data is deleted
    - No orphaned records exist
    - Collection and path mappings are preserved
    - Database state is consistent

    Atomicity:
    - If any deletion step fails, entire operation rolls back
    - If any validation fails, entire operation rolls back
    - If any constraint violation occurs, entire operation rolls back
    """
    with session() as db:
        try:
            # Phase 1: Pre-flight validation
            collection = validate_collection_exists(db, collection_id)
            validate_no_conflicting_operations(db, collection_id)
            validate_wipe_prerequisites(db, collection)

            # Phase 2: Execute wipe
            result = execute_collection_wipe(db, collection, options)

            # Phase 3: Post-operation validation
            validate_no_orphaned_records(db)
            validate_collection_preserved(db, collection)
            validate_path_mappings_preserved(db, collection)
            validate_database_consistency(db)

            return result

        except Exception as e:
            logger.error("collection_wipe_failed", collection_id=collection_id, error=str(e))
            raise WipeError(f"Collection wipe failed: {e}")
```

### 2. Pre-flight Validation Functions

```python
def validate_collection_exists(db: Session, collection_id: str) -> SourceCollection:
    """Validate collection exists and return it."""
    collection = find_collection(db, collection_id)
    if not collection:
        raise ValidationError(f"Collection '{collection_id}' not found")
    return collection

def validate_no_conflicting_operations(db: Session, collection_id: str) -> None:
    """Validate no conflicting operations are in progress."""
    # Check for active ingest operations
    # Check for active wipe operations
    # Check for any locks on the collection
    pass

def validate_wipe_prerequisites(db: Session, collection: SourceCollection) -> None:
    """Validate all prerequisites for wipe operation."""
    # Validate collection is accessible
    # Validate no critical dependencies
    # Validate business rules allow wipe
    pass
```

### 3. Post-operation Validation Functions

```python
def validate_no_orphaned_records(db: Session) -> None:
    """Validate no orphaned records exist."""
    orphaned_episodes = db.query(Episode).outerjoin(EpisodeAsset).filter(
        EpisodeAsset.episode_id.is_(None)
    ).count()
    if orphaned_episodes > 0:
        raise ValidationError(f"Found {orphaned_episodes} orphaned episodes")

    orphaned_seasons = db.query(Season).outerjoin(Episode).filter(
        Episode.id.is_(None)
    ).count()
    if orphaned_seasons > 0:
        raise ValidationError(f"Found {orphaned_seasons} orphaned seasons")

    orphaned_titles = db.query(Title).outerjoin(Season).filter(
        Season.id.is_(None)
    ).count()
    if orphaned_titles > 0:
        raise ValidationError(f"Found {orphaned_titles} orphaned titles")

def validate_collection_preserved(db: Session, collection: SourceCollection) -> None:
    """Validate collection is preserved."""
    preserved_collection = db.query(SourceCollection).filter(
        SourceCollection.id == collection.id
    ).first()
    if not preserved_collection:
        raise ValidationError("Collection was deleted during wipe")

def validate_path_mappings_preserved(db: Session, collection: SourceCollection) -> None:
    """Validate path mappings are preserved."""
    path_mappings = db.query(PathMapping).filter(
        PathMapping.collection_id == collection.id
    ).count()
    if path_mappings == 0:
        raise ValidationError("Path mappings were deleted during wipe")

def validate_database_consistency(db: Session) -> None:
    """Validate overall database consistency."""
    # Check foreign key constraints
    # Check business rule compliance
    # Check data integrity
    pass
```

### 4. Asset Discovery Logic

```python
# Find assets with collection_id (new assets)
assets_with_collection_id = db.query(Asset).filter(
    Asset.collection_id == collection.id
).all()

# Find assets via path mapping (legacy assets)
path_mappings = db.query(PathMapping).filter(
    PathMapping.collection_id == collection.id
).all()
assets_from_paths = []
for mapping in path_mappings:
    if mapping.local_path:
        escaped_path = mapping.local_path.replace("\\", "\\\\")
        matching_assets = db.query(Asset).filter(
            Asset.uri.op('~')(f'^{escaped_path}'),
            Asset.collection_id.is_(None)
        ).all()
        assets_from_paths.extend(matching_assets)

# Combine both sets
all_assets = assets_with_collection_id + assets_from_paths
```

### 2. Deletion Logic

```python
# 1. Delete review queue entries
db.query(ReviewQueue).filter(
    ReviewQueue.asset_id.in_(asset_ids)
).delete(synchronize_session=False)

# 2. Delete episode-asset links
db.query(EpisodeAsset).filter(
    EpisodeAsset.asset_id.in_(asset_ids)
).delete(synchronize_session=False)

# 3. Delete assets
db.query(Asset).filter(
    Asset.id.in_(asset_ids)
).delete(synchronize_session=False)

# 4. Delete orphaned episodes
orphaned_episodes = db.query(Episode).outerjoin(EpisodeAsset).filter(
    EpisodeAsset.asset_id.is_(None)
).all()
for episode in orphaned_episodes:
    db.delete(episode)

# 5. Delete orphaned seasons
orphaned_seasons = db.query(Season).outerjoin(Episode).filter(
    Episode.id.is_(None)
).all()
for season in orphaned_seasons:
    db.delete(season)

# 6. Delete orphaned titles
orphaned_titles = db.query(Title).outerjoin(Season).filter(
    Season.id.is_(None)
).all()
for title in orphaned_titles:
    db.delete(title)

# Note: Path mappings and collection are preserved for re-ingest
```

## Testing Requirements

### Unit Tests

- Test collection identification (UUID, external ID, name)
- Test asset discovery (collection_id vs path mapping)
- Test deletion order
- Test error handling
- Test dry-run mode
- Test JSON output

### Integration Tests

- Test complete wipe workflow
- Test database transaction rollback
- Test with real collection data
- Test confirmation prompts
- Test force mode

## See Also

- [CLI Documentation](../operator/CLI.md)
- [Ingest Pipeline Documentation](../domain/IngestPipeline.md)
- [Database Schema](../data-model/README.md)
