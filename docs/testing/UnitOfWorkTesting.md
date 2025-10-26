# Unit of Work Testing Framework

## Purpose

Define the testing framework for Unit of Work (UoW) operations to ensure atomicity, consistency, and data integrity. All UoW operations MUST be thoroughly tested according to this framework.

## Testing Principles

### 1. Atomicity Testing

- **All-or-Nothing**: Verify operations either complete successfully or fail completely
- **Rollback Verification**: Ensure all changes are rolled back on failure
- **State Consistency**: Verify database is never left in partial state

### 2. Consistency Testing

- **Pre-flight Validation**: Test all validation rules
- **Post-operation Validation**: Test all consistency checks
- **Business Rule Compliance**: Verify business rules are enforced

### 3. Isolation Testing

- **Transaction Boundaries**: Test operation isolation
- **Concurrent Operations**: Test handling of concurrent operations
- **State Independence**: Verify operations don't interfere

## Test Categories

### 1. Unit Tests

#### Pre-flight Validation Tests

```python
def test_validate_collection_exists():
    """Test collection existence validation."""
    with session() as db:
        # Test valid collection
        collection = create_test_collection(db)
        result = validate_collection_exists(db, collection.id)
        assert result == collection

        # Test non-existent collection
        with pytest.raises(ValidationError):
            validate_collection_exists(db, "non-existent-id")

def test_validate_collection_enabled():
    """Test collection enabled validation."""
    with session() as db:
        # Test enabled collection
        collection = create_test_collection(db, enabled=True)
        validate_collection_enabled(collection)  # Should not raise

        # Test disabled collection
        collection = create_test_collection(db, enabled=False)
        with pytest.raises(ValidationError):
            validate_collection_enabled(collection)

def test_validate_no_conflicting_operations():
    """Test conflict detection validation."""
    with session() as db:
        collection = create_test_collection(db)

        # Test no conflicts
        validate_no_conflicting_operations(db, collection.id)  # Should not raise

        # Test with active operation
        create_active_operation(db, collection.id)
        with pytest.raises(ValidationError):
            validate_no_conflicting_operations(db, collection.id)
```

#### Post-operation Validation Tests

```python
def test_validate_no_orphaned_records():
    """Test orphaned record validation."""
    with session() as db:
        # Test clean database
        validate_no_orphaned_records(db)  # Should not raise

        # Test with orphaned records
        create_orphaned_episode(db)
        with pytest.raises(ValidationError):
            validate_no_orphaned_records(db)

def test_validate_collection_preserved():
    """Test collection preservation validation."""
    with session() as db:
        collection = create_test_collection(db)

        # Test preserved collection
        validate_collection_preserved(db, collection)  # Should not raise

        # Test deleted collection
        db.delete(collection)
        db.commit()
        with pytest.raises(ValidationError):
            validate_collection_preserved(db, collection)
```

### 2. Integration Tests

#### Complete Operation Tests

```python
def test_collection_wipe_success():
    """Test successful collection wipe operation."""
    with session() as db:
        # Setup test data
        collection = create_test_collection(db)
        assets = create_test_assets(db, collection, count=10)
        episodes = create_test_episodes(db, assets)
        seasons = create_test_seasons(db, episodes)
        titles = create_test_titles(db, seasons)

        # Execute wipe
        result = wipe_collection(collection.id, WipeOptions())

        # Verify results
        assert result.success
        assert result.deleted_assets == 10
        assert result.deleted_episodes == len(episodes)
        assert result.deleted_seasons == len(seasons)
        assert result.deleted_titles == len(titles)

        # Verify database state
        assert db.query(Asset).count() == 0
        assert db.query(Episode).count() == 0
        assert db.query(Season).count() == 0
        assert db.query(Title).count() == 0
        assert db.query(SourceCollection).filter_by(id=collection.id).first() is not None

def test_collection_wipe_failure_rollback():
    """Test collection wipe failure and rollback."""
    with session() as db:
        # Setup test data
        collection = create_test_collection(db)
        assets = create_test_assets(db, collection, count=5)

        # Mock failure during deletion
        with patch('retrovue.cli.commands.collection.db.delete') as mock_delete:
            mock_delete.side_effect = Exception("Simulated failure")

            # Execute wipe
            with pytest.raises(WipeError):
                wipe_collection(collection.id, WipeOptions())

            # Verify rollback
            assert db.query(Asset).count() == 5  # Assets still exist
            assert db.query(SourceCollection).filter_by(id=collection.id).first() is not None

def test_collection_ingest_success():
    """Test successful collection ingest operation."""
    with session() as db:
        # Setup test data
        collection = create_test_collection(db)
        asset_drafts = create_test_asset_drafts(count=5)

        # Mock importer
        with patch('retrovue.content_manager.ingest_orchestrator.ImporterRegistry') as mock_registry:
            mock_registry.fetch_assets_for_collection.return_value = asset_drafts

            # Execute ingest
            result = ingest_collection(collection.id, IngestFilters())

            # Verify results
            assert result.success
            assert result.processed_assets == 5
            assert result.created_assets == 5

            # Verify database state
            assert db.query(Asset).count() == 5
            assert db.query(Episode).count() == 5
            assert db.query(Season).count() == 1
            assert db.query(Title).count() == 1

def test_collection_ingest_failure_rollback():
    """Test collection ingest failure and rollback."""
    with session() as db:
        # Setup test data
        collection = create_test_collection(db)
        asset_drafts = create_test_asset_drafts(count=3)

        # Mock importer with failure
        with patch('retrovue.content_manager.ingest_orchestrator.ImporterRegistry') as mock_registry:
            mock_registry.fetch_assets_for_collection.return_value = asset_drafts

            # Mock failure during processing
            with patch('retrovue.content_manager.ingest_orchestrator.process_asset') as mock_process:
                mock_process.side_effect = Exception("Simulated failure")

                # Execute ingest
                with pytest.raises(IngestError):
                    ingest_collection(collection.id, IngestFilters())

                # Verify rollback
                assert db.query(Asset).count() == 0
                assert db.query(Episode).count() == 0
```

### 3. Contract Tests

#### Operation Contract Tests

```python
def test_wipe_operation_contract():
    """Test wipe operation follows contract exactly."""
    with session() as db:
        collection = create_test_collection(db)

        # Test pre-flight validation
        with patch('retrovue.cli.commands.collection.validate_collection_exists') as mock_validate:
            mock_validate.side_effect = ValidationError("Collection not found")

            with pytest.raises(WipeError):
                wipe_collection(collection.id, WipeOptions())

            # Verify no changes made
            assert db.query(Asset).count() == 0

def test_ingest_operation_contract():
    """Test ingest operation follows contract exactly."""
    with session() as db:
        collection = create_test_collection(db)

        # Test pre-flight validation
        with patch('retrovue.content_manager.ingest_orchestrator.validate_collection_enabled') as mock_validate:
            mock_validate.side_effect = ValidationError("Collection not enabled")

            with pytest.raises(IngestError):
                ingest_collection(collection.id, IngestFilters())

            # Verify no changes made
            assert db.query(Asset).count() == 0
```

### 4. Performance Tests

#### Large Dataset Tests

```python
def test_wipe_large_collection():
    """Test wipe operation with large dataset."""
    with session() as db:
        collection = create_test_collection(db)

        # Create large dataset
        assets = create_test_assets(db, collection, count=10000)
        episodes = create_test_episodes(db, assets)
        seasons = create_test_seasons(db, episodes)
        titles = create_test_titles(db, seasons)

        # Measure performance
        start_time = time.time()
        result = wipe_collection(collection.id, WipeOptions())
        end_time = time.time()

        # Verify success
        assert result.success
        assert end_time - start_time < 30  # Should complete within 30 seconds

def test_ingest_large_collection():
    """Test ingest operation with large dataset."""
    with session() as db:
        collection = create_test_collection(db)

        # Create large dataset
        asset_drafts = create_test_asset_drafts(count=5000)

        # Mock importer
        with patch('retrovue.content_manager.ingest_orchestrator.ImporterRegistry') as mock_registry:
            mock_registry.fetch_assets_for_collection.return_value = asset_drafts

            # Measure performance
            start_time = time.time()
            result = ingest_collection(collection.id, IngestFilters())
            end_time = time.time()

            # Verify success
            assert result.success
            assert end_time - start_time < 60  # Should complete within 60 seconds
```

## Test Utilities

### Database Fixtures

```python
@pytest.fixture
def test_db():
    """Create test database session."""
    with session() as db:
        yield db
        # Cleanup handled by transaction rollback

@pytest.fixture
def test_collection(test_db):
    """Create test collection."""
    collection = SourceCollection(
        id=uuid.uuid4(),
        name="Test Collection",
        external_id="test-collection",
        enabled=True
    )
    test_db.add(collection)
    test_db.flush()
    return collection

@pytest.fixture
def test_assets(test_db, test_collection):
    """Create test assets."""
    assets = []
    for i in range(10):
        asset = Asset(
            id=i + 1,
            uuid=uuid.uuid4(),
            uri=f"/test/path/asset_{i}.mkv",
            collection_id=test_collection.id,
            canonical=True
        )
        test_db.add(asset)
        assets.append(asset)
    test_db.flush()
    return assets
```

### Validation Helpers

```python
def assert_no_orphaned_records(db: Session):
    """Assert no orphaned records exist."""
    orphaned_episodes = db.query(Episode).outerjoin(EpisodeAsset).filter(
        EpisodeAsset.episode_id.is_(None)
    ).count()
    assert orphaned_episodes == 0, f"Found {orphaned_episodes} orphaned episodes"

    orphaned_seasons = db.query(Season).outerjoin(Episode).filter(
        Episode.id.is_(None)
    ).count()
    assert orphaned_seasons == 0, f"Found {orphaned_seasons} orphaned seasons"

    orphaned_titles = db.query(Title).outerjoin(Season).filter(
        Season.id.is_(None)
    ).count()
    assert orphaned_titles == 0, f"Found {orphaned_titles} orphaned titles"

def assert_collection_preserved(db: Session, collection: SourceCollection):
    """Assert collection is preserved."""
    preserved = db.query(SourceCollection).filter(
        SourceCollection.id == collection.id
    ).first()
    assert preserved is not None, "Collection was deleted"

def assert_path_mappings_preserved(db: Session, collection: SourceCollection):
    """Assert path mappings are preserved."""
    mappings = db.query(PathMapping).filter(
        PathMapping.collection_id == collection.id
    ).count()
    assert mappings > 0, "Path mappings were deleted"
```

## Test Execution

### Running Tests

```bash
# Run all UoW tests
pytest tests/unit_of_work/ -v

# Run specific test categories
pytest tests/unit_of_work/test_validation.py -v
pytest tests/unit_of_work/test_integration.py -v
pytest tests/unit_of_work/test_contracts.py -v

# Run with coverage
pytest tests/unit_of_work/ --cov=retrovue --cov-report=html
```

### Continuous Integration

All UoW tests MUST pass before:

- Code can be merged to main branch
- Releases can be created
- Production deployments

## See Also

- [Unit of Work Contract](UnitOfWorkContract.md)
- [Collection Wipe Contract](CollectionWipeContract.md)
- [Ingest Pipeline Documentation](../domain/IngestPipeline.md)

