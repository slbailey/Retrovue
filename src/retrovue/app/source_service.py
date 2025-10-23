"""
Source service for managing content sources and collections.

This service handles the configuration and management of content sources
like Plex servers and filesystem collections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from sqlalchemy.orm import Session

from ..domain.entities import Source, SourceCollection, PathMapping


@dataclass
class ContentSourceDTO:
    """
    Data Transfer Object for content sources.
    
    Represents a content source like a Plex server or filesystem.
    """
    
    id: str
    """Unique identifier for the source"""
    
    kind: str
    """Type of source (e.g., 'plex', 'filesystem')"""
    
    name: str
    """Human-readable name of the source"""
    
    status: str
    """Status of the source (e.g., 'connected', 'disconnected')"""
    
    base_url: str | None
    """Base URL for the source (if applicable)"""
    
    config: dict[str, Any] | None = None
    """Additional configuration for the source"""


@dataclass
class CollectionUpdateDTO:
    """
    Data Transfer Object for collection updates.
    
    Represents updates to a collection's configuration.
    """
    
    external_id: str
    """External identifier for the collection"""
    
    enabled: bool
    """Whether the collection is enabled"""
    
    mapping_pairs: list[tuple[str, str]]
    """Path mapping pairs [(source_prefix, local_prefix), ...]"""


@dataclass
class SourceCollectionDTO:
    """
    Data Transfer Object for source collections.
    
    Represents a collection (e.g., Plex library, filesystem directory)
    within a content source.
    """
    
    external_id: str
    """External identifier (e.g., Plex library key)"""
    
    name: str
    """Human-readable name of the collection"""
    
    enabled: bool
    """Whether this collection is enabled for ingestion"""
    
    mapping_pairs: list[tuple[str, str]]
    """Path mapping pairs [(source_prefix, local_prefix), ...]"""
    
    source_type: str
    """Type of source (e.g., 'plex', 'filesystem')"""
    
    config: dict[str, Any] | None = None
    """Additional configuration for the collection"""


class SourceService:
    """
    Service for managing content sources and collections.
    
    This service provides methods to list and manage collections
    for different content sources.
    """
    
    def __init__(self, db: Session):
        """Initialize the source service with a database session."""
        self.db = db
    
    def get_source_by_external_id(self, external_id: str) -> Source | None:
        """Get a content source by its external ID."""
        return self.db.query(Source).filter(Source.external_id == external_id).first()
    
    def list_enabled_collections(self, source_id: str) -> list[SourceCollectionDTO]:
        """
        List enabled collections for a specific source.
        
        Args:
            source_id: Identifier for the content source
            
        Returns:
            List of enabled collections for the source
        """
        # Query the database for enabled collections
        source = self.db.query(Source).filter(Source.external_id == source_id).first()
        if not source:
            return []
        
        collections = self.db.query(SourceCollection).filter(
            SourceCollection.source_id == source.id,
            SourceCollection.enabled == True
        ).all()
        
        result = []
        for collection in collections:
            # Get path mappings for this collection
            mappings = self.db.query(PathMapping).filter(
                PathMapping.collection_id == collection.id
            ).all()
            
            mapping_pairs = [(m.plex_path, m.local_path) for m in mappings]
            
            result.append(SourceCollectionDTO(
                external_id=collection.external_id,
                name=collection.name,
                enabled=collection.enabled,
                mapping_pairs=mapping_pairs,
                source_type=source.kind,
                config=collection.config
            ))
        
        return result
    
    def get_collection(self, source_id: str, external_id: str) -> SourceCollectionDTO | None:
        """
        Get a specific collection by source and external ID.
        
        Args:
            source_id: Identifier for the content source
            external_id: External identifier for the collection
            
        Returns:
            Collection DTO or None if not found
        """
        collections = self.list_enabled_collections(source_id)
        for collection in collections:
            if collection.external_id == external_id:
                return collection
        return None
    
    def update_collection_mapping(
        self, 
        source_id: str, 
        external_id: str, 
        mapping_pairs: list[tuple[str, str]]
    ) -> bool:
        """
        Update path mapping pairs for a collection.
        
        Args:
            source_id: Identifier for the content source
            external_id: External identifier for the collection
            mapping_pairs: New mapping pairs
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Find the source and collection
            source = self.db.query(Source).filter(Source.external_id == source_id).first()
            if not source:
                return False
                
            collection = self.db.query(SourceCollection).filter(
                SourceCollection.source_id == source.id,
                SourceCollection.external_id == external_id
            ).first()
            if not collection:
                return False
            
            # Delete existing mappings
            self.db.query(PathMapping).filter(
                PathMapping.collection_id == collection.id
            ).delete()
            
            # Add new mappings
            for plex_path, local_path in mapping_pairs:
                mapping = PathMapping(
                    collection_id=collection.id,
                    plex_path=plex_path,
                    local_path=local_path
                )
                self.db.add(mapping)
            
            self.db.flush()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def update_collection_enabled(
        self, 
        source_id: str, 
        external_id: str, 
        enabled: bool
    ) -> bool:
        """
        Update the enabled status of a collection.
        
        Args:
            source_id: Identifier for the content source
            external_id: External identifier for the collection
            enabled: New enabled status
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Find the source and collection
            source = self.db.query(Source).filter(Source.external_id == source_id).first()
            if not source:
                return False
                
            collection = self.db.query(SourceCollection).filter(
                SourceCollection.source_id == source.id,
                SourceCollection.external_id == external_id
            ).first()
            if not collection:
                return False
            
            # Update enabled status
            collection.enabled = enabled
            self.db.flush()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def create_plex_source(self, name: str, base_url: str, token: str) -> "ContentSourceDTO":
        """
        Create a new Plex source.
        
        Args:
            name: Friendly name for the source
            base_url: Plex server base URL
            token: Plex authentication token
            
        Returns:
            ContentSourceDTO for the created source
        """
        import uuid
        
        # Create external ID
        external_id = f"plex-{uuid.uuid4().hex[:8]}"
        
        # Create the source entity
        source = Source(
            external_id=external_id,
            kind="plex",
            name=name,
            config={"base_url": base_url, "token": token}
        )
        
        self.db.add(source)
        self.db.flush()
        self.db.refresh(source)
        
        return ContentSourceDTO(
            id=source.external_id,
            kind=source.kind,
            name=source.name,
            status="connected",
            base_url=base_url,
            config=source.config
        )
    
    def discover_collections(self, source_id: str) -> list[SourceCollectionDTO]:
        """
        Discover collections from a source without persisting.
        
        Args:
            source_id: Identifier for the content source
            
        Returns:
            List of discovered collections
        """
        try:
            # Get the source from database
            source = self.db.query(Source).filter(Source.external_id == source_id).first()
            if not source:
                print(f"DEBUG: Source {source_id} not found in database")
                return []
            
            print(f"DEBUG: Found source {source.name} with config: {source.config}")
            
            # Import Plex importer
            from ..adapters.importers.plex_importer import PlexImporter
            
            # Create importer with source config
            importer = PlexImporter(
                servers=[{
                    "base_url": source.config.get("base_url"),
                    "token": source.config.get("token")
                }],
                include_metadata=True
            )
            
            print(f"DEBUG: Created importer with servers: {importer.servers}")
            
            # Discover libraries
            libraries = importer.discover_libraries()
            print(f"DEBUG: Discovered {len(libraries)} libraries: {libraries}")
            
            # Convert to DTOs
            collections = []
            for lib in libraries:
                collections.append(SourceCollectionDTO(
                    external_id=lib.get("key", ""),
                    name=lib.get("title", ""),
                    enabled=False,  # Newly discovered collections start disabled
                    mapping_pairs=[],  # No mappings by default
                    source_type=source.kind,
                    config={
                        "plex_path": f"/plex/{lib.get('title', '').lower().replace(' ', '_')}",
                        "type": lib.get("type", "movie")
                    }
                ))
            
            print(f"DEBUG: Returning {len(collections)} collections")
            return collections
            
        except Exception as e:
            print(f"DEBUG: Error in discover_collections: {e}")
            import traceback
            traceback.print_exc()
            # Return empty list on error
            return []
    
    def save_collections(self, source_id: str, updates: list["CollectionUpdateDTO"]) -> bool:
        """
        Save collection updates (enabled status and mapping pairs).
        
        Args:
            source_id: Identifier for the content source
            updates: List of collection updates
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Find the source
            source = self.db.query(Source).filter(Source.external_id == source_id).first()
            if not source:
                return False
            
            for update in updates:
                # Find or create the collection
                collection = self.db.query(SourceCollection).filter(
                    SourceCollection.source_id == source.id,
                    SourceCollection.external_id == update.external_id
                ).first()
                
                if not collection:
                    # Create new collection
                    collection = SourceCollection(
                        source_id=source.id,
                        external_id=update.external_id,
                        name=update.external_id,  # Use external_id as name if not provided
                        enabled=update.enabled
                    )
                    self.db.add(collection)
                    self.db.flush()
                    self.db.refresh(collection)
                else:
                    # Update existing collection
                    collection.enabled = update.enabled
                
                # Update path mappings
                # Delete existing mappings
                self.db.query(PathMapping).filter(
                    PathMapping.collection_id == collection.id
                ).delete()
                
                # Add new mappings
                for plex_path, local_path in update.mapping_pairs:
                    mapping = PathMapping(
                        collection_id=collection.id,
                        plex_path=plex_path,
                        local_path=local_path
                    )
                    self.db.add(mapping)
            
            self.db.flush()
            return True
            
        except Exception as e:
            self.db.rollback()
            return False