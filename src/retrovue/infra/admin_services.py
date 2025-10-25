"""
Admin services for RetroVue infrastructure management.
These services handle CRUD operations for channels, templates, schedules, and assets.
"""
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .db import get_session
from ..schedule_manager.models import BroadcastChannel, BroadcastTemplate, BroadcastTemplateBlock, BroadcastScheduleDay, CatalogAsset
from ..domain.entities import Asset


class ChannelAdminService:
    """Service for managing channels."""
    
    @staticmethod
    def create_channel(
        name: str,
        timezone: str,
        grid_size_minutes: int,
        grid_offset_minutes: int,
        rollover_minutes: int
    ) -> Dict[str, Any]:
        """Create a new channel."""
        session = get_session()()
        try:
            channel = BroadcastChannel(
                name=name,
                timezone=timezone,
                grid_size_minutes=grid_size_minutes,
                grid_offset_minutes=grid_offset_minutes,
                rollover_minutes=rollover_minutes
            )
            session.add(channel)
            session.commit()
            
            result = {
                "id": channel.id,
                "name": channel.name,
                "timezone": channel.timezone,
                "grid_size_minutes": channel.grid_size_minutes,
                "grid_offset_minutes": channel.grid_offset_minutes,
                "rollover_minutes": channel.rollover_minutes,
                "is_active": channel.is_active,
                "created_at": channel.created_at.isoformat()
            }
            return result
        except IntegrityError:
            session.rollback()
            raise ValueError(f"Channel with name '{name}' already exists")
        finally:
            session.close()


class TemplateAdminService:
    """Service for managing templates and template blocks."""
    
    @staticmethod
    def create_template(name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new template."""
        session = get_session()()
        try:
            template = BroadcastTemplate(
                name=name,
                description=description
            )
            session.add(template)
            session.commit()
            
            result = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "is_active": template.is_active,
                "created_at": template.created_at.isoformat()
            }
            return result
        except IntegrityError:
            session.rollback()
            raise ValueError(f"Template with name '{name}' already exists")
        finally:
            session.close()
    
    @staticmethod
    def add_block(
        template_id: int,
        start_time: str,
        end_time: str,
        tags: List[str],
        episode_policy: str
    ) -> Dict[str, Any]:
        """Add a block to a template."""
        session = get_session()()
        try:
            # Build rule_json from tags and episode_policy
            rule_json = {
                "tags": tags,
                "episode_policy": episode_policy
            }
            
            template_block = BroadcastTemplateBlock(
                template_id=template_id,
                start_time=start_time,
                end_time=end_time,
                rule_json=json.dumps(rule_json)
            )
            session.add(template_block)
            session.commit()
            
            result = {
                "id": template_block.id,
                "template_id": template_block.template_id,
                "start_time": template_block.start_time,
                "end_time": template_block.end_time,
                "rule_json": template_block.rule_json,
                "created_at": template_block.created_at.isoformat()
            }
            return result
        finally:
            session.close()


class ScheduleAdminService:
    """Service for managing schedule assignments."""
    
    @staticmethod
    def assign_template_for_day(
        channel_name: str,
        template_name: str,
        schedule_date: str
    ) -> Dict[str, Any]:
        """Assign a template to a channel for a specific day."""
        session = get_session()()
        try:
            # Look up channel by name
            channel = session.query(BroadcastChannel).filter(BroadcastChannel.name == channel_name).first()
            if not channel:
                raise ValueError(f"Channel '{channel_name}' not found")
            
            # Look up template by name
            template = session.query(BroadcastTemplate).filter(BroadcastTemplate.name == template_name).first()
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Check if assignment already exists
            existing = session.query(BroadcastScheduleDay).filter(
                BroadcastScheduleDay.channel_id == channel.id,
                BroadcastScheduleDay.schedule_date == schedule_date
            ).first()
            
            if existing:
                raise ValueError(f"Channel '{channel_name}' already has a template assigned for {schedule_date}")
            
            schedule_day = BroadcastScheduleDay(
                channel_id=channel.id,
                template_id=template.id,
                schedule_date=schedule_date
            )
            session.add(schedule_day)
            session.commit()
            
            result = {
                "id": schedule_day.id,
                "channel_id": schedule_day.channel_id,
                "template_id": schedule_day.template_id,
                "schedule_date": schedule_day.schedule_date,
                "created_at": schedule_day.created_at.isoformat()
            }
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class AssetAdminService:
    """Service for managing assets."""
    
    @staticmethod
    def add_asset(
        title: str,
        duration_seconds: int,
        tags: List[str],
        file_path: str,
        canonical: bool = False
    ) -> Dict[str, Any]:
        """Add a new asset."""
        session = get_session()()
        try:
            # Convert duration from seconds to milliseconds
            duration_ms = duration_seconds * 1000
            
            # Convert tags list to comma-separated string
            tags_str = ",".join(tags) if tags else ""
            
            asset = CatalogAsset(
                title=title,
                duration_ms=duration_ms,
                tags=tags_str,
                file_path=file_path,
                canonical=canonical
            )
            session.add(asset)
            session.commit()
            
            result = {
                "id": asset.id,
                "title": asset.title,
                "duration_ms": asset.duration_ms,
                "tags": asset.tags,
                "file_path": asset.file_path,
                "canonical": asset.canonical,
                "created_at": asset.created_at.isoformat()
            }
            return result
        finally:
            session.close()
    
    @staticmethod
    def update_asset(
        asset_id: int,
        title: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        canonical: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing asset."""
        session = get_session()()
        try:
            asset = session.query(CatalogAsset).filter(CatalogAsset.id == asset_id).first()
            if not asset:
                raise ValueError(f"Asset with ID {asset_id} not found")
            
            if title is not None:
                asset.title = title
            if duration_seconds is not None:
                asset.duration_ms = duration_seconds * 1000
            if tags is not None:
                asset.tags = ",".join(tags) if tags else ""
            if file_path is not None:
                asset.file_path = file_path
            if canonical is not None:
                asset.canonical = canonical
            
            session.commit()
            
            result = {
                "id": asset.id,
                "title": asset.title,
                "duration_ms": asset.duration_ms,
                "tags": asset.tags,
                "file_path": asset.file_path,
                "canonical": asset.canonical,
                "created_at": asset.created_at.isoformat()
            }
            return result
        finally:
            session.close()
    
    @staticmethod
    def promote_from_library(
        source_asset_uuid: str,
        title: str,
        tags: list[str],
        canonical: bool,
    ) -> Dict[str, Any]:
        """
        Promote a library asset to the broadcast catalog.
        
        This is the ONLY approved path for promoting content from the Library Domain 
        into the Broadcast Domain. This method will REFUSE promotion if the library 
        asset is not technically playout-ready. This protects ScheduleService and 
        ChannelManager from impossible-to-air catalog entries.
        
        Args:
            source_asset_uuid: UUID of the library asset to promote
            title: Guide-facing title for the broadcast catalog
            tags: List of tags for the broadcast catalog
            canonical: Whether this asset is canonical (approved for broadcast)
            
        Returns:
            Dict containing the new catalog asset ID and metadata
            
        Raises:
            ValueError: If the library asset cannot be found or is not eligible for promotion
        """
        session = get_session()()
        try:
            # Look up the library asset by UUID
            library_asset = session.query(Asset).filter(Asset.uuid == source_asset_uuid).first()
            if not library_asset:
                raise ValueError(f"Asset not found: {source_asset_uuid}")
            
            # Validate that the library asset is eligible for promotion
            if library_asset.is_deleted:
                raise ValueError(f"Asset {source_asset_uuid} cannot be promoted: asset is not active")
            
            # Broadcast Catalog must be clean. Bad assets are rejected at promotion time.
            # Validate duration_ms is present and valid
            if library_asset.duration_ms is None or library_asset.duration_ms <= 0:
                raise ValueError(f"Asset {source_asset_uuid} cannot be promoted: missing duration_ms")
            
            # Validate file_path is present and not empty
            if not library_asset.uri or library_asset.uri.strip() == "":
                raise ValueError(f"Asset {source_asset_uuid} cannot be promoted: missing file_path")
            
            # Create new CatalogAsset in the Broadcast Domain
            catalog_asset = CatalogAsset(
                title=title,
                duration_ms=library_asset.duration_ms,
                tags=",".join(tags) if tags else "",
                file_path=library_asset.uri,  # Use URI as the playable path
                canonical=canonical,
                source_ingest_asset_id=library_asset.id  # Track source for traceability
            )
            session.add(catalog_asset)
            session.commit()
            
            result = {
                "catalog_id": catalog_asset.id,
                "title": catalog_asset.title,
                "canonical": catalog_asset.canonical,
                "duration_ms": catalog_asset.duration_ms,
                "file_path": catalog_asset.file_path,
                "source_ingest_asset_id": catalog_asset.source_ingest_asset_id
            }
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @staticmethod
    def list_assets(
        canonical_only: Optional[bool] = None,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List assets with optional filtering."""
        session = get_session()()
        try:
            query = session.query(CatalogAsset)
            
            if canonical_only is not None:
                query = query.filter(CatalogAsset.canonical == canonical_only)
            
            if tag:
                query = query.filter(CatalogAsset.tags.contains(tag))
            
            assets = query.all()
            
            result = []
            for asset in assets:
                result.append({
                    "id": asset.id,
                    "title": asset.title,
                    "duration_ms": asset.duration_ms,
                    "tags": asset.tags,
                    "file_path": asset.file_path,
                    "canonical": asset.canonical,
                    "created_at": asset.created_at.isoformat()
                })
            
            return result
        finally:
            session.close()
