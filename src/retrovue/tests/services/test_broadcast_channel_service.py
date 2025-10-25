"""
Tests for BroadcastChannelService to ensure service contract coherence.

These tests validate that:
- Service methods work correctly with the ORM
- Business logic is enforced
- Data integrity is maintained
- Public API contracts are respected
"""

import pytest
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from retrovue.schedule_manager.broadcast_channel_service import BroadcastChannelService
from retrovue.schedule_manager.models import BroadcastChannel


class TestBroadcastChannelServiceCreation:
    """Test BroadcastChannelService channel creation."""
    
    def test_create_channel_success(self, clean_db: Session, sample_broadcast_channel_data):
        """Test successful channel creation."""
        # Create a channel using the service
        result = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        
        # Assert the result contains expected fields
        assert "id" in result
        assert "name" in result
        assert "timezone" in result
        assert "grid_size_minutes" in result
        assert "grid_offset_minutes" in result
        assert "rollover_minutes" in result
        assert "is_active" in result
        assert "created_at" in result
        
        # Assert values match input
        assert result["name"] == sample_broadcast_channel_data["name"]
        assert result["timezone"] == sample_broadcast_channel_data["timezone"]
        assert result["grid_size_minutes"] == sample_broadcast_channel_data["grid_size_minutes"]
        assert result["grid_offset_minutes"] == sample_broadcast_channel_data["grid_offset_minutes"]
        assert result["rollover_minutes"] == sample_broadcast_channel_data["rollover_minutes"]
        assert result["is_active"] == sample_broadcast_channel_data["is_active"]
        
        # Assert ID is an integer
        assert isinstance(result["id"], int)
        assert result["id"] > 0
        
        # Verify it was actually created in the database
        channel = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == result["id"])).scalar_one()
        assert channel.name == sample_broadcast_channel_data["name"]
        assert channel.timezone == sample_broadcast_channel_data["timezone"]
    
    def test_create_channel_duplicate_name_raises_error(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that creating a channel with duplicate name raises ValueError."""
        # Create first channel
        BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        
        # Try to create second channel with same name
        with pytest.raises(ValueError, match="Channel with name 'Test Channel' already exists"):
            BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
    
    def test_create_channel_validation_errors(self, clean_db: Session):
        """Test that channel creation validates required fields."""
        # Test empty name
        with pytest.raises(ValueError, match="Channel name is required"):
            BroadcastChannelService.create_channel(
                name="",
                timezone="America/New_York",
                grid_size_minutes=30,
                grid_offset_minutes=0,
                rollover_minutes=360
            )
        
        # Test empty timezone
        with pytest.raises(ValueError, match="Timezone is required"):
            BroadcastChannelService.create_channel(
                name="Test Channel",
                timezone="",
                grid_size_minutes=30,
                grid_offset_minutes=0,
                rollover_minutes=360
            )
        
        # Test negative grid_size_minutes
        with pytest.raises(ValueError, match="grid_size_minutes must be non-negative"):
            BroadcastChannelService.create_channel(
                name="Test Channel",
                timezone="America/New_York",
                grid_size_minutes=-1,
                grid_offset_minutes=0,
                rollover_minutes=360
            )
        
        # Test negative grid_offset_minutes
        with pytest.raises(ValueError, match="grid_offset_minutes must be non-negative"):
            BroadcastChannelService.create_channel(
                name="Test Channel",
                timezone="America/New_York",
                grid_size_minutes=30,
                grid_offset_minutes=-1,
                rollover_minutes=360
            )
        
        # Test negative rollover_minutes
        with pytest.raises(ValueError, match="rollover_minutes must be non-negative"):
            BroadcastChannelService.create_channel(
                name="Test Channel",
                timezone="America/New_York",
                grid_size_minutes=30,
                grid_offset_minutes=0,
                rollover_minutes=-1
            )
        
        # Test invalid is_active type
        with pytest.raises(ValueError, match="is_active must be a boolean"):
            BroadcastChannelService.create_channel(
                name="Test Channel",
                timezone="America/New_York",
                grid_size_minutes=30,
                grid_offset_minutes=0,
                rollover_minutes=360,
                is_active="true"  # Should be boolean
            )


class TestBroadcastChannelServiceRetrieval:
    """Test BroadcastChannelService channel retrieval methods."""
    
    def test_get_channel_by_id_success(self, clean_db: Session, sample_broadcast_channel_data):
        """Test successful channel retrieval by ID."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Retrieve the channel
        result = BroadcastChannelService.get_channel(channel_id)
        
        # Assert the result contains all expected fields
        assert result is not None
        assert result["id"] == channel_id
        assert result["name"] == sample_broadcast_channel_data["name"]
        assert result["timezone"] == sample_broadcast_channel_data["timezone"]
        assert result["grid_size_minutes"] == sample_broadcast_channel_data["grid_size_minutes"]
        assert result["grid_offset_minutes"] == sample_broadcast_channel_data["grid_offset_minutes"]
        assert result["rollover_minutes"] == sample_broadcast_channel_data["rollover_minutes"]
        assert result["is_active"] == sample_broadcast_channel_data["is_active"]
        assert "created_at" in result
    
    def test_get_channel_by_id_not_found(self, clean_db: Session):
        """Test channel retrieval by non-existent ID returns None."""
        result = BroadcastChannelService.get_channel(99999)
        assert result is None
    
    def test_get_channel_by_uuid_success(self, clean_db: Session, sample_broadcast_channel_data):
        """Test successful channel retrieval by UUID."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Get the UUID from the database
        channel = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == channel_id)).scalar_one()
        channel_uuid = channel.uuid
        
        # Retrieve the channel by UUID
        result = BroadcastChannelService.get_channel_by_uuid(channel_uuid)
        
        # Assert the result contains all expected fields
        assert result is not None
        assert result["uuid"] == str(channel_uuid)
        assert result["name"] == sample_broadcast_channel_data["name"]
        assert result["timezone"] == sample_broadcast_channel_data["timezone"]
        assert result["grid_size_minutes"] == sample_broadcast_channel_data["grid_size_minutes"]
        assert result["grid_offset_minutes"] == sample_broadcast_channel_data["grid_offset_minutes"]
        assert result["rollover_minutes"] == sample_broadcast_channel_data["rollover_minutes"]
        assert result["is_active"] == sample_broadcast_channel_data["is_active"]
        assert "created_at" in result
    
    def test_get_channel_by_uuid_not_found(self, clean_db: Session):
        """Test channel retrieval by non-existent UUID returns None."""
        fake_uuid = uuid.uuid4()
        result = BroadcastChannelService.get_channel_by_uuid(fake_uuid)
        assert result is None


class TestBroadcastChannelServiceListing:
    """Test BroadcastChannelService channel listing methods."""
    
    def test_list_channels_public_success(self, clean_db: Session, sample_broadcast_channel_data):
        """Test successful public channel listing."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        
        # List channels
        result = BroadcastChannelService.list_channels_public()
        
        # Assert the result is a list
        assert isinstance(result, list)
        assert len(result) == 1
        
        # Assert the channel data
        channel_data = result[0]
        assert "uuid" in channel_data
        assert "name" in channel_data
        assert "timezone" in channel_data
        assert "grid_size_minutes" in channel_data
        assert "grid_offset_minutes" in channel_data
        assert "rollover_minutes" in channel_data
        assert "is_active" in channel_data
        assert "created_at" in channel_data
        
        # Assert no raw integer ID is exposed (UUID is the external identity)
        assert "id" not in channel_data
        
        # Assert values match
        assert channel_data["name"] == sample_broadcast_channel_data["name"]
        assert channel_data["timezone"] == sample_broadcast_channel_data["timezone"]
        assert channel_data["grid_size_minutes"] == sample_broadcast_channel_data["grid_size_minutes"]
        assert channel_data["grid_offset_minutes"] == sample_broadcast_channel_data["grid_offset_minutes"]
        assert channel_data["rollover_minutes"] == sample_broadcast_channel_data["rollover_minutes"]
        assert channel_data["is_active"] == sample_broadcast_channel_data["is_active"]
        
        # Assert UUID is present and valid
        assert isinstance(uuid.UUID(channel_data["uuid"]), uuid.UUID)
    
    def test_list_channels_public_multiple_channels(self, clean_db: Session):
        """Test public channel listing with multiple channels."""
        # Create multiple channels
        channel1_data = {
            "name": "Channel 1",
            "timezone": "America/New_York",
            "grid_size_minutes": 30,
            "grid_offset_minutes": 0,
            "rollover_minutes": 360,
            "is_active": True,
        }
        channel2_data = {
            "name": "Channel 2",
            "timezone": "America/Los_Angeles",
            "grid_size_minutes": 60,
            "grid_offset_minutes": 15,
            "rollover_minutes": 420,
            "is_active": False,
        }
        
        BroadcastChannelService.create_channel(**channel1_data)
        BroadcastChannelService.create_channel(**channel2_data)
        
        # List channels
        result = BroadcastChannelService.list_channels_public()
        
        # Assert we got both channels
        assert len(result) == 2
        
        # Assert both channels have UUIDs and no raw IDs
        for channel_data in result:
            assert "uuid" in channel_data
            assert "id" not in channel_data
            assert isinstance(uuid.UUID(channel_data["uuid"]), uuid.UUID)
    
    def test_list_channels_public_empty(self, clean_db: Session):
        """Test public channel listing with no channels."""
        result = BroadcastChannelService.list_channels_public()
        assert result == []


class TestBroadcastChannelServiceUpdate:
    """Test BroadcastChannelService channel update operations."""
    
    def test_update_channel_success(self, clean_db: Session, sample_broadcast_channel_data):
        """Test successful channel update."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Update the channel
        update_data = {
            "name": "Updated Channel",
            "timezone": "America/Los_Angeles",
            "grid_size_minutes": 60,
            "grid_offset_minutes": 15,
            "rollover_minutes": 420,
            "is_active": False,
        }
        
        result = BroadcastChannelService.update_channel(channel_id, **update_data)
        
        # Assert the result contains updated values
        assert result["id"] == channel_id
        assert result["name"] == "Updated Channel"
        assert result["timezone"] == "America/Los_Angeles"
        assert result["grid_size_minutes"] == 60
        assert result["grid_offset_minutes"] == 15
        assert result["rollover_minutes"] == 420
        assert result["is_active"] is False
        
        # Verify it was actually updated in the database
        channel = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == channel_id)).scalar_one()
        assert channel.name == "Updated Channel"
        assert channel.timezone == "America/Los_Angeles"
        assert channel.grid_size_minutes == 60
        assert channel.grid_offset_minutes == 15
        assert channel.rollover_minutes == 420
        assert channel.is_active is False
    
    def test_update_channel_partial_update(self, clean_db: Session, sample_broadcast_channel_data):
        """Test partial channel update."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Update only the name
        result = BroadcastChannelService.update_channel(channel_id, name="Updated Name")
        
        # Assert only the name was updated
        assert result["name"] == "Updated Name"
        assert result["timezone"] == sample_broadcast_channel_data["timezone"]  # Unchanged
        assert result["grid_size_minutes"] == sample_broadcast_channel_data["grid_size_minutes"]  # Unchanged
    
    def test_update_channel_not_found(self, clean_db: Session):
        """Test updating non-existent channel raises error."""
        with pytest.raises(ValueError, match="Channel with ID 99999 not found"):
            BroadcastChannelService.update_channel(99999, name="Updated Name")
    
    def test_update_channel_validation_errors(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that channel update validates fields."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Test empty name
        with pytest.raises(ValueError, match="Channel name cannot be empty"):
            BroadcastChannelService.update_channel(channel_id, name="")
        
        # Test empty timezone
        with pytest.raises(ValueError, match="Timezone cannot be empty"):
            BroadcastChannelService.update_channel(channel_id, timezone="")
        
        # Test negative grid_size_minutes
        with pytest.raises(ValueError, match="grid_size_minutes must be non-negative"):
            BroadcastChannelService.update_channel(channel_id, grid_size_minutes=-1)
        
        # Test negative grid_offset_minutes
        with pytest.raises(ValueError, match="grid_offset_minutes must be non-negative"):
            BroadcastChannelService.update_channel(channel_id, grid_offset_minutes=-1)
        
        # Test negative rollover_minutes
        with pytest.raises(ValueError, match="rollover_minutes must be non-negative"):
            BroadcastChannelService.update_channel(channel_id, rollover_minutes=-1)
        
        # Test invalid is_active type
        with pytest.raises(ValueError, match="is_active must be a boolean"):
            BroadcastChannelService.update_channel(channel_id, is_active="true")


class TestBroadcastChannelServiceDeletion:
    """Test BroadcastChannelService channel deletion."""
    
    def test_delete_channel_success(self, clean_db: Session, sample_broadcast_channel_data):
        """Test successful channel deletion."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Delete the channel
        BroadcastChannelService.delete_channel(channel_id)
        
        # Verify it was deleted
        channel = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == channel_id)).scalar_one_or_none()
        assert channel is None
    
    def test_delete_channel_not_found(self, clean_db: Session):
        """Test deleting non-existent channel raises error."""
        with pytest.raises(ValueError, match="Channel with ID 99999 not found"):
            BroadcastChannelService.delete_channel(99999)


class TestBroadcastChannelServiceBusinessLogic:
    """Test BroadcastChannelService business logic and data integrity."""
    
    def test_channel_name_uniqueness_enforcement(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that channel name uniqueness is enforced."""
        # Create first channel
        BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        
        # Try to create second channel with same name
        with pytest.raises(ValueError, match="Channel with name 'Test Channel' already exists"):
            BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
    
    def test_channel_name_uniqueness_on_update(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that channel name uniqueness is enforced on update."""
        # Create two channels with different names
        channel1_data = sample_broadcast_channel_data.copy()
        channel1_data["name"] = "Channel 1"
        created1 = BroadcastChannelService.create_channel(**channel1_data)
        
        channel2_data = sample_broadcast_channel_data.copy()
        channel2_data["name"] = "Channel 2"
        created2 = BroadcastChannelService.create_channel(**channel2_data)
        
        # Try to update channel2 to have the same name as channel1
        with pytest.raises(ValueError, match="Channel with name 'Channel 1' already exists"):
            BroadcastChannelService.update_channel(created2["id"], name="Channel 1")
    
    def test_channel_parameter_preservation(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that channel parameters are preserved correctly."""
        # Create a channel with specific parameters
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        
        # Retrieve the channel
        retrieved = BroadcastChannelService.get_channel(created["id"])
        
        # Assert all parameters are preserved
        assert retrieved["rollover_minutes"] == sample_broadcast_channel_data["rollover_minutes"]
        assert retrieved["grid_size_minutes"] == sample_broadcast_channel_data["grid_size_minutes"]
        assert retrieved["grid_offset_minutes"] == sample_broadcast_channel_data["grid_offset_minutes"]
        assert retrieved["timezone"] == sample_broadcast_channel_data["timezone"]
        assert retrieved["is_active"] == sample_broadcast_channel_data["is_active"]
    
    def test_channel_uuid_consistency(self, clean_db: Session, sample_broadcast_channel_data):
        """Test that channel UUIDs are consistent across operations."""
        # Create a channel
        created = BroadcastChannelService.create_channel(**sample_broadcast_channel_data)
        channel_id = created["id"]
        
        # Get the UUID from the database
        channel = clean_db.execute(select(BroadcastChannel).where(BroadcastChannel.id == channel_id)).scalar_one()
        channel_uuid = channel.uuid
        
        # Retrieve by UUID
        retrieved_by_uuid = BroadcastChannelService.get_channel_by_uuid(channel_uuid)
        
        # Assert the data is consistent
        assert retrieved_by_uuid["uuid"] == str(channel_uuid)
        assert retrieved_by_uuid["name"] == created["name"]
        assert retrieved_by_uuid["timezone"] == created["timezone"]
        assert retrieved_by_uuid["grid_size_minutes"] == created["grid_size_minutes"]
        assert retrieved_by_uuid["grid_offset_minutes"] == created["grid_offset_minutes"]
        assert retrieved_by_uuid["rollover_minutes"] == created["rollover_minutes"]
        assert retrieved_by_uuid["is_active"] == created["is_active"]
