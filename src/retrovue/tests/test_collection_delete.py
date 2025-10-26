"""
Test collection delete functionality and collection list command.

This module tests the collection delete command and collection list command
to ensure they work correctly with the database and follow the expected behavior.
"""

import pytest
import json
from sqlalchemy.orm import Session
from retrovue.domain.entities import (
    Source, SourceCollection, PathMapping, Asset, Episode, Season, Title, 
    EpisodeAsset, ReviewQueue
)
from retrovue.content_manager.source_service import SourceService
from retrovue.cli.commands.collection import wipe_collection
from unittest.mock import patch
import typer
from typer.testing import CliRunner


class TestCollectionDelete:
    """Test collection delete functionality."""
    
    def test_delete_collection_success(self, clean_db: Session):
        """Test successful collection deletion."""
        # Create a test source
        source = Source(
            external_id="test-source-1",
            name="Test Source",
            kind="plex",
            config={"base_url": "http://test", "token": "test"}
        )
        clean_db.add(source)
        clean_db.flush()
        
        # Create a test collection
        collection = SourceCollection(
            source_id=source.id,
            external_id="18",
            name="Test Collection",
            enabled=False,
            config={"type": "movie", "plex_section_ref": "plex://18"}
        )
        clean_db.add(collection)
        clean_db.flush()
        
        # Create test path mappings
        path_mapping1 = PathMapping(
            collection_id=collection.id,
            plex_path="/mnt/media/Movies",
            local_path=""
        )
        path_mapping2 = PathMapping(
            collection_id=collection.id,
            plex_path="/mnt/nas/VHS-Rips",
            local_path=""
        )
        clean_db.add(path_mapping1)
        clean_db.add(path_mapping2)
        clean_db.commit()
        
        # Test delete_collection method
        source_service = SourceService(clean_db)
        result = source_service.delete_collection("18")
        
        assert result is True
        
        # Verify collection is deleted
        deleted_collection = clean_db.query(SourceCollection).filter(
            SourceCollection.external_id == "18"
        ).first()
        assert deleted_collection is None
        
        # Verify path mappings are deleted (cascade)
        path_mappings = clean_db.query(PathMapping).filter(
            PathMapping.collection_id == collection.id
        ).all()
        assert len(path_mappings) == 0
        
        # Verify source still exists
        source_exists = clean_db.query(Source).filter(
            Source.external_id == "test-source-1"
        ).first()
        assert source_exists is not None


class TestCollectionList:
    """Test collection list functionality."""
    
    def test_list_collections_with_data(self, clean_db: Session):
        """Test listing collections with real database data."""
        # Create a test source
        source = Source(
            external_id="test-source-list",
            name="Test Source for List",
            kind="plex",
            config={"base_url": "http://test", "token": "test"}
        )
        clean_db.add(source)
        clean_db.flush()
        
        # Create test collections
        collection1 = SourceCollection(
            source_id=source.id,
            external_id="18",
            name="Movies",
            enabled=True,
            config={"type": "movie", "plex_section_ref": "plex://18"}
        )
        collection2 = SourceCollection(
            source_id=source.id,
            external_id="19",
            name="TV Shows",
            enabled=False,
            config={"type": "show", "plex_section_ref": "plex://19"}
        )
        clean_db.add(collection1)
        clean_db.add(collection2)
        clean_db.flush()
        
        # Create path mappings
        path_mapping1 = PathMapping(
            collection_id=collection1.id,
            plex_path="/mnt/media/Movies",
            local_path="/media/movies"
        )
        path_mapping2 = PathMapping(
            collection_id=collection2.id,
            plex_path="/mnt/media/TV",
            local_path=""
        )
        clean_db.add(path_mapping1)
        clean_db.add(path_mapping2)
        clean_db.commit()
        
        # Test that collections can be queried
        collections = clean_db.query(SourceCollection).filter(
            SourceCollection.source_id == source.id
        ).all()
        
        assert len(collections) == 2
        
        # Test collection data structure
        for collection in collections:
            path_mappings = clean_db.query(PathMapping).filter(
                PathMapping.collection_id == collection.id
            ).all()
            
            assert collection.external_id in ["18", "19"]
            assert collection.name in ["Movies", "TV Shows"]
            assert len(path_mappings) == 1
    
    def test_list_collections_empty_source(self, clean_db: Session):
        """Test listing collections for source with no collections."""
        # Create a test source with no collections
        source = Source(
            external_id="test-source-empty",
            name="Empty Source",
            kind="plex",
            config={"base_url": "http://test", "token": "test"}
        )
        clean_db.add(source)
        clean_db.commit()
        
        # Query collections for this source
        collections = clean_db.query(SourceCollection).filter(
            SourceCollection.source_id == source.id
        ).all()
        
        assert len(collections) == 0
    
    def test_delete_collection_not_found(self, clean_db: Session):
        """Test deletion of non-existent collection."""
        source_service = SourceService(clean_db)
        result = source_service.delete_collection("nonexistent")
        
        assert result is False
    
    def test_delete_collection_by_uuid(self, clean_db: Session):
        """Test deletion by UUID."""
        # Create a test source
        source = Source(
            external_id="test-source-2",
            name="Test Source 2",
            kind="plex",
            config={"base_url": "http://test", "token": "test"}
        )
        clean_db.add(source)
        clean_db.flush()
        
        # Create a test collection
        collection = SourceCollection(
            source_id=source.id,
            external_id="19",
            name="Test Collection 2",
            enabled=False,
            config={"type": "show", "plex_section_ref": "plex://19"}
        )
        clean_db.add(collection)
        clean_db.flush()
        
        # Test delete by UUID
        source_service = SourceService(clean_db)
        result = source_service.delete_collection(str(collection.id))
        
        assert result is True
        
        # Verify collection is deleted
        deleted_collection = clean_db.query(SourceCollection).filter(
            SourceCollection.id == collection.id
        ).first()
        assert deleted_collection is None


class TestCollectionWipe:
    """Test collection wipe functionality."""
    
    def create_test_collection_with_hierarchy(self, clean_db: Session):
        """Create a test collection with full TV show hierarchy."""
        # Create source
        source = Source(
            external_id="test-source-wipe",
            name="Test Source for Wipe",
            kind="plex",
            config={"base_url": "http://test", "token": "test"}
        )
        clean_db.add(source)
        clean_db.flush()
        
        # Create collection
        collection = SourceCollection(
            source_id=source.id,
            external_id="20",
            name="TV Shows",
            enabled=True,
            config={"type": "show", "plex_section_ref": "plex://20"}
        )
        clean_db.add(collection)
        clean_db.flush()
        
        # Create path mapping
        path_mapping = PathMapping(
            collection_id=collection.id,
            plex_path="/mnt/media/TV",
            local_path="/media/tv"
        )
        clean_db.add(path_mapping)
        
        # Create TV show hierarchy
        title = Title(
            name="Test Show",
            kind="show",
            year=2020
        )
        clean_db.add(title)
        clean_db.flush()
        
        season = Season(
            title_id=title.id,
            number=1
        )
        clean_db.add(season)
        clean_db.flush()
        
        episode = Episode(
            title_id=title.id,
            season_id=season.id,
            number=1,
            name="Pilot Episode"
        )
        clean_db.add(episode)
        clean_db.flush()
        
        # Create assets
        asset1 = Asset(
            uri="/media/tv/Test Show/Season 01/Test Show - S01E01.mkv",
            size=1024*1024*1024,  # 1GB
            canonical=False
        )
        asset2 = Asset(
            uri="/media/tv/Test Show/Season 01/Test Show - S01E02.mkv",
            size=1024*1024*1024,  # 1GB
            canonical=True
        )
        clean_db.add_all([asset1, asset2])
        clean_db.flush()
        
        # Create episode-asset links
        episode_asset1 = EpisodeAsset(
            episode_id=episode.id,
            asset_id=asset1.id
        )
        episode_asset2 = EpisodeAsset(
            episode_id=episode.id,
            asset_id=asset2.id
        )
        clean_db.add_all([episode_asset1, episode_asset2])
        
        # Create review queue entry
        review_entry = ReviewQueue(
            asset_id=asset1.id,
            reason="Low confidence",
            confidence=0.3
        )
        clean_db.add(review_entry)
        
        # Note: Not creating catalog assets - focusing only on ingest domain
        
        clean_db.commit()
        
        return collection, {
            "source": source,
            "collection": collection,
            "path_mapping": path_mapping,
            "title": title,
            "season": season,
            "episode": episode,
            "assets": [asset1, asset2],
            "episode_assets": [episode_asset1, episode_asset2],
            "review_entry": review_entry
        }
    
    def test_wipe_collection_dry_run(self, clean_db: Session):
        """Test wipe collection dry run shows correct statistics."""
        collection, entities = self.create_test_collection_with_hierarchy(clean_db)
        
        # Mock the CLI runner to capture output
        runner = CliRunner()
        
        # Test dry run
        result = runner.invoke(wipe_collection, [
            "TV Shows",
            "--dry-run"
        ], input="n\n")  # Don't confirm
        
        assert result.exit_code == 0
        assert "Collection wipe analysis for: TV Shows" in result.output
        assert "🔍 Review queue entries: 1" in result.output
        assert "🔗 Episode-asset links: 2" in result.output
        assert "🎬 Assets: 2" in result.output
        assert "📺 Episodes: 1" in result.output
        assert "📅 Seasons: 1" in result.output
        assert "🎭 TV Shows/Titles: 1" in result.output
        assert "🗂️ Path mappings: 1" in result.output
        assert "DRY RUN - No changes made" in result.output
        
        # Verify nothing was actually deleted
        assert clean_db.query(SourceCollection).filter(SourceCollection.name == "TV Shows").first() is not None
        assert clean_db.query(Asset).count() == 2
        assert clean_db.query(Title).count() == 1
    
    def test_wipe_collection_dry_run_json(self, clean_db: Session):
        """Test wipe collection dry run with JSON output."""
        collection, entities = self.create_test_collection_with_hierarchy(clean_db)
        
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            "TV Shows",
            "--dry-run",
            "--json"
        ])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        output_data = json.loads(result.output)
        
        assert output_data["collection"]["name"] == "TV Shows"
        assert output_data["dry_run"] is True
        assert output_data["deletion_stats"]["review_queue_entries"] == 1
        assert output_data["deletion_stats"]["episode_assets"] == 2
        assert output_data["deletion_stats"]["assets"] == 2
        assert output_data["deletion_stats"]["episodes"] == 1
        assert output_data["deletion_stats"]["seasons"] == 1
        assert output_data["deletion_stats"]["titles"] == 1
        assert output_data["deletion_stats"]["path_mappings"] == 1
    
    def test_wipe_collection_cancelled(self, clean_db: Session):
        """Test wipe collection when user cancels confirmation."""
        collection, entities = self.create_test_collection_with_hierarchy(clean_db)
        
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            "TV Shows"
        ], input="CANCEL\n")  # Don't type DELETE
        
        assert result.exit_code == 0
        assert "Operation cancelled" in result.output
        
        # Verify nothing was deleted
        assert clean_db.query(SourceCollection).filter(SourceCollection.name == "TV Shows").first() is not None
        assert clean_db.query(Asset).count() == 2
    
    def test_wipe_collection_success(self, clean_db: Session):
        """Test successful collection wipe."""
        collection, entities = self.create_test_collection_with_hierarchy(clean_db)
        
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            "TV Shows",
            "--force"  # Skip confirmation
        ])
        
        assert result.exit_code == 0
        assert "Starting collection wipe..." in result.output
        assert "✅ Collection wipe completed successfully!" in result.output
        
        # Verify everything was deleted
        assert clean_db.query(SourceCollection).filter(SourceCollection.name == "TV Shows").first() is None
        assert clean_db.query(Asset).count() == 0
        assert clean_db.query(Episode).count() == 0
        assert clean_db.query(Season).count() == 0
        assert clean_db.query(Title).count() == 0
        assert clean_db.query(EpisodeAsset).count() == 0
        assert clean_db.query(ReviewQueue).count() == 0
        assert clean_db.query(PathMapping).filter(PathMapping.collection_id == collection.id).count() == 0
        
        # Verify source still exists
        assert clean_db.query(Source).filter(Source.external_id == "test-source-wipe").first() is not None
    
    def test_wipe_collection_not_found(self, clean_db: Session):
        """Test wipe collection when collection doesn't exist."""
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            "Nonexistent Collection"
        ])
        
        assert result.exit_code == 1
        assert "Error: Collection 'Nonexistent Collection' not found" in result.output
    
    def test_wipe_collection_multiple_matches(self, clean_db: Session):
        """Test wipe collection when multiple collections have same name."""
        # Create two collections with same name
        source1 = Source(
            external_id="test-source-1",
            name="Test Source 1",
            kind="plex",
            config={"base_url": "http://test1", "token": "test1"}
        )
        source2 = Source(
            external_id="test-source-2", 
            name="Test Source 2",
            kind="plex",
            config={"base_url": "http://test2", "token": "test2"}
        )
        clean_db.add_all([source1, source2])
        clean_db.flush()
        
        collection1 = SourceCollection(
            source_id=source1.id,
            external_id="21",
            name="Movies",
            enabled=False,
            config={"type": "movie"}
        )
        collection2 = SourceCollection(
            source_id=source2.id,
            external_id="22", 
            name="Movies",
            enabled=False,
            config={"type": "movie"}
        )
        clean_db.add_all([collection1, collection2])
        clean_db.commit()
        
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            "Movies"
        ])
        
        assert result.exit_code == 1
        assert "Error: Multiple collections found with name 'Movies'. Use full UUID to specify." in result.output
    
    def test_wipe_collection_by_uuid(self, clean_db: Session):
        """Test wipe collection by UUID."""
        collection, entities = self.create_test_collection_with_hierarchy(clean_db)
        
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            str(collection.id),
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "✅ Collection wipe completed successfully!" in result.output
        
        # Verify collection was deleted
        assert clean_db.query(SourceCollection).filter(SourceCollection.id == collection.id).first() is None
    
    def test_wipe_collection_by_external_id(self, clean_db: Session):
        """Test wipe collection by external ID."""
        collection, entities = self.create_test_collection_with_hierarchy(clean_db)
        
        runner = CliRunner()
        
        result = runner.invoke(wipe_collection, [
            "20",  # external_id
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "✅ Collection wipe completed successfully!" in result.output
        
        # Verify collection was deleted
        assert clean_db.query(SourceCollection).filter(SourceCollection.external_id == "20").first() is None
