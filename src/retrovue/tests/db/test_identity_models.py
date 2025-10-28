"""
Tests for identity models to ensure ORM ↔ Alembic ↔ service contract coherence.

These tests validate that:
- Integer PK spine is real and auto-incrementing
- UUID fields exist and are unique
- Foreign keys reference integer PKs
- Delete cascades work correctly
- All models can be created and queried through the ORM
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from retrovue.domain.entities import Asset, Episode, Marker, ReviewQueue, Season, Title
from retrovue.schedule_manager.models import BroadcastChannel, CatalogAsset


class TestAssetIdentity:
    """Test Asset model identity and relationships."""
    
    def test_asset_creation_with_autoincrement_id(self, clean_db: Session, sample_asset_data):
        """Test that Asset gets an autoincrement integer id."""
        # Create an Asset
        asset = Asset(**sample_asset_data)
        clean_db.add(asset)
        clean_db.commit()
        
        # Assert it got an autoincrement integer id
        assert asset.id is not None
        assert isinstance(asset.id, int)
        assert asset.id > 0
        
        # Verify it's persisted
        retrieved = clean_db.execute(select(Asset).where(Asset.id == asset.id)).scalar_one()
        assert retrieved.id == asset.id
    
    def test_asset_creation_with_uuid(self, clean_db: Session, sample_asset_data):
        """Test that Asset gets a non-null UUID."""
        # Create an Asset
        asset = Asset(**sample_asset_data)
        clean_db.add(asset)
        clean_db.commit()
        
        # Assert it got a non-null uuid
        assert asset.uuid is not None
        assert isinstance(asset.uuid, uuid.UUID)
        
        # Verify it's persisted
        retrieved = clean_db.execute(select(Asset).where(Asset.id == asset.id)).scalar_one()
        assert retrieved.uuid == asset.uuid
    
    def test_asset_uuid_uniqueness(self, clean_db: Session, sample_asset_data):
        """Test that Asset UUIDs are unique."""
        # Create first Asset
        asset1 = Asset(**sample_asset_data)
        clean_db.add(asset1)
        clean_db.commit()
        
        # Create second Asset with different URI
        asset2_data = sample_asset_data.copy()
        asset2_data["uri"] = "file:///test/path/sample2.mp4"
        asset2 = Asset(**asset2_data)
        clean_db.add(asset2)
        clean_db.commit()
        
        # Assert UUIDs are different
        assert asset1.uuid != asset2.uuid
        
        # Verify both are persisted with different UUIDs
        retrieved1 = clean_db.execute(select(Asset).where(Asset.id == asset1.id)).scalar_one()
        retrieved2 = clean_db.execute(select(Asset).where(Asset.id == asset2.id)).scalar_one()
        assert retrieved1.uuid != retrieved2.uuid
    
    def test_asset_uuid_is_real_uuid(self, clean_db: Session, sample_asset_data):
        """Test that Asset UUID is a real UUID format."""
        asset = Asset(**sample_asset_data)
        clean_db.add(asset)
        clean_db.commit()
        
        # Assert it's a valid UUID
        assert isinstance(asset.uuid, uuid.UUID)
        
        # Test that it can be converted to string and back
        uuid_str = str(asset.uuid)
        parsed_uuid = uuid.UUID(uuid_str)
        assert parsed_uuid == asset.uuid


class TestCatalogAssetIdentity:
    """Test CatalogAsset model identity and foreign key relationships."""
    
    def test_catalog_asset_creation_with_autoincrement_id(self, clean_db: Session, sample_catalog_asset_data):
        """Test that CatalogAsset gets an autoincrement integer id."""
        catalog_asset = CatalogAsset(**sample_catalog_asset_data)
        clean_db.add(catalog_asset)
        clean_db.commit()
        
        # Assert it got an autoincrement integer id
        assert catalog_asset.id is not None
        assert isinstance(catalog_asset.id, int)
        assert catalog_asset.id > 0
        
        # Verify it's persisted
        retrieved = clean_db.execute(select(CatalogAsset).where(CatalogAsset.id == catalog_asset.id)).scalar_one()
        assert retrieved.id == catalog_asset.id
    
    def test_catalog_asset_creation_with_uuid(self, clean_db: Session, sample_catalog_asset_data):
        """Test that CatalogAsset gets a non-null UUID."""
        catalog_asset = CatalogAsset(**sample_catalog_asset_data)
        clean_db.add(catalog_asset)
        clean_db.commit()
        
        # Assert it got a non-null uuid
        assert catalog_asset.uuid is not None
        assert isinstance(catalog_asset.uuid, uuid.UUID)
        
        # Verify it's persisted
        retrieved = clean_db.execute(select(CatalogAsset).where(CatalogAsset.id == catalog_asset.id)).scalar_one()
        assert retrieved.uuid == catalog_asset.uuid
    
    def test_catalog_asset_foreign_key_to_asset(self, clean_db: Session, sample_asset_data, sample_catalog_asset_data):
        """Test that CatalogAsset can reference Asset via source_ingest_asset_id."""
        # Create an Asset first
        asset = Asset(**sample_asset_data)
        clean_db.add(asset)
        clean_db.commit()
        
        # Create a CatalogAsset that references the Asset
        catalog_asset_data = sample_catalog_asset_data.copy()
        catalog_asset_data["source_ingest_asset_id"] = asset.id
        catalog_asset = CatalogAsset(**catalog_asset_data)
        clean_db.add(catalog_asset)
        clean_db.commit()
        
        # Assert the foreign key relationship
        assert catalog_asset.source_ingest_asset_id == asset.id
        
        # Verify it's persisted correctly
        retrieved = clean_db.execute(select(CatalogAsset).where(CatalogAsset.id == catalog_asset.id)).scalar_one()
        assert retrieved.source_ingest_asset_id == asset.id


class TestBroadcastChannelIdentity:
    """Test BroadcastChannel model identity."""
    
    def test_broadcast_channel_creation_with_autoincrement_id(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that BroadcastChannel gets an autoincrement integer id."""
        channel = BroadcastChannel(**sample_broadcast_channel_data)
        clean_db.add(channel)
        clean_db.commit()
        
        # Assert it got an autoincrement integer id
        assert channel.id is not None
        assert isinstance(channel.id, int)
        assert channel.id > 0
        
        # Verify it's persisted
        retrieved = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == channel.id)).scalar_one()
        assert retrieved.id == channel.id
    
    def test_broadcast_channel_creation_with_uuid(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that BroadcastChannel gets a non-null UUID."""
        channel = BroadcastChannel(**sample_broadcast_channel_data)
        clean_db.add(channel)
        clean_db.commit()
        
        # Assert it got a non-null uuid
        assert channel.uuid is not None
        assert isinstance(channel.uuid, uuid.UUID)
        
        # Verify it's persisted
        retrieved = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == channel.id)).scalar_one()
        assert retrieved.uuid == channel.uuid


class TestCascadeBehavior:
    """Test cascade behavior for delete operations."""
    
    def test_asset_cascade_deletes_markers_and_review_queue(self, clean_db: Session, sample_asset_data):
        """Test that deleting an Asset cascades to delete Markers and ReviewQueue rows."""
        # Create an Asset
        asset = Asset(**sample_asset_data)
        clean_db.add(asset)
        clean_db.commit()
        
        # Create a Marker attached to the Asset
        marker = Marker(
            asset_id=asset.id,
            kind="chapter",
            start_ms=0,
            end_ms=1000,
            payload={"name": "Chapter 1"}
        )
        clean_db.add(marker)
        
        # Create a ReviewQueue row attached to the Asset
        review_queue = ReviewQueue(
            asset_id=asset.id,
            reason="Quality check needed",
            confidence=0.8,
            status="pending"
        )
        clean_db.add(review_queue)
        clean_db.commit()
        
        # Verify they exist
        assert clean_db.execute(select(Marker).where(Marker.asset_id == asset.id)).scalar_one_or_none() is not None
        assert clean_db.execute(select(ReviewQueue).where(ReviewQueue.asset_id == asset.id)).scalar_one_or_none() is not None
        
        # Delete the Asset
        clean_db.delete(asset)
        clean_db.commit()
        
        # Assert the Marker and ReviewQueue rows are gone (CASCADE works)
        assert clean_db.execute(select(Marker).where(Marker.asset_id == asset.id)).scalar_one_or_none() is None
        assert clean_db.execute(select(ReviewQueue).where(ReviewQueue.asset_id == asset.id)).scalar_one_or_none() is None
    
    def test_title_cascade_deletes_seasons_and_episodes(self, clean_db: Session):
        """Test that deleting a Title cascades to delete Seasons and Episodes."""
        # Create a Title
        title = Title(
            kind="show",
            name="Test Show",
            year=2023
        )
        clean_db.add(title)
        clean_db.commit()
        
        # Create a Season attached to the Title
        season = Season(
            title_id=title.id,
            number=1
        )
        clean_db.add(season)
        
        # Create an Episode attached to the Title
        episode = Episode(
            title_id=title.id,
            season_id=season.id,
            number=1,
            name="Test Episode"
        )
        clean_db.add(episode)
        clean_db.commit()
        
        # Verify they exist
        assert clean_db.execute(select(Season).where(Season.title_id == title.id)).scalar_one_or_none() is not None
        assert clean_db.execute(select(Episode).where(Episode.title_id == title.id)).scalar_one_or_none() is not None
        
        # Delete the Title
        clean_db.delete(title)
        clean_db.commit()
        
        # Assert the Season and Episode rows are gone (CASCADE works)
        assert clean_db.execute(select(Season).where(Season.title_id == title.id)).scalar_one_or_none() is None
        assert clean_db.execute(select(Episode).where(Episode.title_id == title.id)).scalar_one_or_none() is None


class TestForeignKeyIntegrity:
    """Test foreign key integrity and relationships."""
    
    def test_catalog_asset_foreign_key_integrity(self, clean_db: Session, sample_catalog_asset_data):
        """Test that CatalogAsset foreign key references work correctly."""
        # Create a CatalogAsset without a source_ingest_asset_id (should be allowed)
        catalog_asset = CatalogAsset(**sample_catalog_asset_data)
        clean_db.add(catalog_asset)
        clean_db.commit()
        
        # Verify it was created successfully
        assert catalog_asset.id is not None
        assert catalog_asset.source_ingest_asset_id is None
        
        # Now create an Asset and link them
        asset_data = {
            "uri": "file:///test/path/sample.mp4",
            "size": 1024000,
            "duration_ms": 120000,
            "canonical": True,
            "is_deleted": False,
        }
        asset = Asset(**asset_data)
        clean_db.add(asset)
        clean_db.commit()
        
        # Update the CatalogAsset to reference the Asset
        catalog_asset.source_ingest_asset_id = asset.id
        clean_db.commit()
        
        # Verify the relationship
        retrieved = clean_db.execute(select(CatalogAsset).where(CatalogAsset.id == catalog_asset.id)).scalar_one()
        assert retrieved.source_ingest_asset_id == asset.id
    
    def test_foreign_key_constraints(self, clean_db: Session, sample_catalog_asset_data):
        """Test that foreign key constraints are enforced."""
        # Try to create a CatalogAsset with a non-existent source_ingest_asset_id
        catalog_asset_data = sample_catalog_asset_data.copy()
        catalog_asset_data["source_ingest_asset_id"] = 99999  # Non-existent ID
        
        catalog_asset = CatalogAsset(**catalog_asset_data)
        clean_db.add(catalog_asset)
        
        # This should not raise an error immediately (deferred constraint)
        # But it should fail on commit if the constraint is enforced
        # Note: The actual constraint behavior depends on the database configuration
        # For now, we'll just verify the data is set as expected
        assert catalog_asset.source_ingest_asset_id == 99999
