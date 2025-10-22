"""
Ingest orchestrator for processing Plex items into the database.

Coordinates the full ingest pipeline: fetch → map → upsert.
"""

import logging
from typing import Dict, Any, List, Optional
from .mapper import Mapper, ContentItemData, MediaFileData, EditorialData, TagRow
from .pathmap import PathMapper
from .validation import ContentValidator, ValidationStatus
from .error_handling import ErrorHandler, ErrorContext, ErrorType

logger = logging.getLogger("retrovue.plex")


class IngestOrchestrator:
    """Orchestrates the ingest process from Plex to database."""
    
    def __init__(self, db, plex_client, path_mapper: PathMapper, validator: Optional[ContentValidator] = None, 
                 error_handler: Optional[ErrorHandler] = None, logger_instance=None):
        """
        Initialize ingest orchestrator.
        
        Args:
            db: Database connection
            plex_client: Plex client instance
            path_mapper: Path mapper instance
            validator: Optional content validator instance
            error_handler: Optional error handler instance
            logger_instance: Optional logger instance
        """
        self.db = db
        self.plex_client = plex_client
        self.path_mapper = path_mapper
        self.validator = validator or ContentValidator(path_mapper)
        self.error_handler = error_handler or ErrorHandler(logger_instance)
        self.mapper = Mapper()
        self.logger = logger_instance or logger
    
    def ingest_library(self, server: Dict[str, Any], library_key: int, kind: str, 
                      mode: str = 'full', since_epoch: Optional[int] = None, limit: Optional[int] = None, 
                      dry_run: bool = False, verbose: bool = False, batch_size: int = 50) -> Dict[str, int]:
        """
        Ingest items from a Plex library.
        
        Args:
            server: Server information dict
            library_key: Library key
            kind: Content kind (movie, episode)
            mode: Ingest mode ('full' or 'incremental')
            since_epoch: For incremental mode, only process items updated since this epoch
            limit: Maximum number of items to process
            dry_run: If True, don't write to database
            verbose: If True, log detailed information
            batch_size: Number of items to process before committing (for non-dry-run)
            
        Returns:
            Stats dictionary with counts
        """
        server_id = server['id']
        server_name = server['name']
        
        self.logger.info(f"Starting {mode} ingest for {server_name} library {library_key} ({kind})")
        if dry_run:
            self.logger.info("DRY RUN MODE - No database writes will be performed")
        
        # Initialize stats
        stats = {
            "scanned": 0,
            "mapped": 0,
            "inserted_items": 0,
            "updated_items": 0,
            "inserted_files": 0,
            "updated_files": 0,
            "linked": 0,
            "skipped": 0,
            "errors": 0
        }
        
        try:
            # Get section types from Plex to determine proper library type
            sections = self.plex_client.get_sections()
            section_type = sections.get(str(library_key), 'movie')  # Default to movie if not found
            
            if section_type not in ['movie', 'show']:
                self.logger.warning(f"Unknown section type '{section_type}' for library {library_key}, defaulting to 'movie'")
                section_type = 'movie'
            
            # Get or create library with proper section type
            library_id = self.db.get_or_create_library(
                server_id, str(library_key), f"Library {library_key}", section_type
            )
            
            # Determine since_epoch for incremental mode
            if mode == 'incremental' and since_epoch is None:
                library_info = self.db.get_library_by_key(server_id, str(library_key))
                if library_info and library_info.get('last_incremental_sync_epoch'):
                    since_epoch = library_info['last_incremental_sync_epoch']
                    self.logger.info(f"Using stored incremental sync epoch: {since_epoch}")
                else:
                    self.logger.warning("No stored incremental sync epoch found, treating as full sync")
                    mode = 'full'
            
            if mode == 'incremental' and since_epoch:
                self.logger.info(f"Incremental mode: processing items updated since epoch {since_epoch}")
            
            # Process items with batching
            batch_count = 0
            items_in_batch = []
            
            for plex_item in self.plex_client.iter_items(library_key, kind, limit, since_epoch=since_epoch):
                stats["scanned"] += 1
                
                try:
                    # Map Plex item to domain models
                    content_item, media_files, editorial, tags = self.mapper.map_plex_item(
                        plex_item, server_id, library_id
                    )
                    stats["mapped"] += 1
                    
                    if verbose:
                        self.logger.info(f"  Mapped: {content_item.title} ({content_item.kind})")
                    
                    if dry_run:
                        self._log_dry_run_actions(content_item, media_files, editorial, tags, verbose)
                        continue
                    
                    # Add to batch
                    items_in_batch.append((content_item, media_files, editorial, tags))
                    batch_count += 1
                    
                    # Process batch if we've hit the batch size
                    if batch_count >= batch_size:
                        self._process_batch(items_in_batch, server_id, library_id, stats, verbose)
                        items_in_batch = []
                        batch_count = 0
                        
                except Exception as e:
                    # Enhanced error handling
                    context = ErrorContext(
                        operation="map_plex_item",
                        item_id=plex_item.get('ratingKey'),
                        item_title=plex_item.get('title', 'Unknown'),
                        server_id=server_id,
                        library_id=library_id
                    )
                    
                    error_record = self.error_handler.handle_error(e, context)
                    stats["errors"] += 1
                    
                    # Log error with context
                    self.logger.error(f"Error processing item {plex_item.get('title', 'Unknown')}: {e}")
                    if error_record.severity.value == 'critical':
                        self.logger.critical(f"Critical error in ingest process: {error_record.message}")
                    if verbose:
                        import traceback
                        self.logger.debug(traceback.format_exc())
            
            # Process remaining items in the last batch
            if items_in_batch and not dry_run:
                self._process_batch(items_in_batch, server_id, library_id, stats, verbose)
            
            # Update sync timestamps
            if not dry_run and stats["errors"] == 0:
                import time
                current_epoch = int(time.time())
                
                if mode == 'full':
                    self.db.set_library_last_full(library_id, current_epoch)
                    self.logger.info(f"Updated last_full_sync_epoch to {current_epoch}")
                elif mode == 'incremental':
                    self.db.set_library_last_incremental(library_id, current_epoch)
                    self.logger.info(f"Updated last_incremental_sync_epoch to {current_epoch}")
            
            self.logger.info(f"Completed {mode} ingest: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Fatal error during ingest: {e}")
            stats["errors"] += 1
            return stats
    
    def _process_batch(self, items_batch: List, server_id: int, library_id: int, 
                      stats: Dict[str, int], verbose: bool):
        """Process a batch of items in a transaction."""
        try:
            for content_item, media_files, editorial, tags in items_batch:
                try:
                    self._process_item(content_item, media_files, editorial, tags, 
                                     server_id, library_id, stats, verbose)
                except Exception as e:
                    # Handle individual item errors within batch
                    context = ErrorContext(
                        operation="process_item",
                        item_id=content_item.title,
                        item_title=content_item.title,
                        server_id=server_id,
                        library_id=library_id
                    )
                    
                    error_record = self.error_handler.handle_error(e, context)
                    stats["errors"] += 1
                    
                    self.logger.error(f"Error processing item {content_item.title}: {e}")
                    if error_record.severity.value == 'critical':
                        self.logger.critical(f"Critical error processing item: {error_record.message}")
            
            # Commit the batch
            self.db.commit()
            
            if verbose:
                self.logger.info(f"  Committed batch of {len(items_batch)} items")
                
        except Exception as e:
            # Handle batch-level errors
            context = ErrorContext(
                operation="process_batch",
                server_id=server_id,
                library_id=library_id,
                additional_data={"batch_size": len(items_batch)}
            )
            
            error_record = self.error_handler.handle_error(e, context)
            self.logger.error(f"Error processing batch: {e}")
            self.db.rollback()
            stats["errors"] += len(items_batch)
            
            if error_record.severity.value == 'critical':
                self.logger.critical(f"Critical batch processing error: {error_record.message}")
    
    def _process_item(self, content_item: ContentItemData, media_files: List[MediaFileData],
                     editorial: EditorialData, tags: List[TagRow], server_id: int, 
                     library_id: int, stats: Dict[str, int], verbose: bool):
        """Process a single item (non-dry-run)."""
        show_id = None
        season_id = None
        
        # Handle episodes - create show and season
        if content_item.kind == 'episode' and content_item.show_title:
            self.logger.info(f"Creating show: {content_item.show_title} for episode: {content_item.title}")
            try:
                show_id = self.db.get_or_create_show(
                    server_id, library_id, f"show_{content_item.show_title}", 
                    content_item.show_title
                )
                self.logger.info(f"Created show with ID: {show_id}")
            except Exception as e:
                self.logger.error(f"Failed to create show {content_item.show_title}: {e}")
                raise
            
            if content_item.season_number:
                season_id = self.db.get_or_create_season(
                    show_id, content_item.season_number
                )
        
        # Upsert content item
        content_item_id = self.db.upsert_content_item(content_item, show_id, season_id, media_files)
        stats["inserted_items"] += 1  # Simplified - could track updates vs inserts
        
        # Process media files
        for media_file in media_files:
            # Validate media file before processing
            validation_result = self.validator.validate_media_file(
                server_id, library_id, media_file.file_path
            )
            
            if validation_result.status != ValidationStatus.VALID:
                self.logger.warning(f"Media file validation failed for {media_file.file_path}: {validation_result.message}")
                stats["errors"] += 1
                continue
            
            # Update media file with validated information
            if validation_result.local_path:
                media_file.file_path = validation_result.local_path
            if validation_result.duration_ms:
                media_file.duration_ms = validation_result.duration_ms
            if validation_result.video_codec:
                media_file.video_codec = validation_result.video_codec
            if validation_result.audio_codec:
                media_file.audio_codec = validation_result.audio_codec
            if validation_result.resolution:
                media_file.width, media_file.height = validation_result.resolution
            
            # Upsert media file
            media_file_id = self.db.upsert_media_file(
                media_file, server_id, library_id, content_item_id, content_item.kind
            )
            stats["inserted_files"] += 1  # Simplified
            
            # Link content item to media file
            self.db.link_content_item_file(content_item_id, media_file_id, 'primary')
            stats["linked"] += 1
        
        # Upsert editorial data
        self.db.upsert_editorial(content_item_id, editorial)
        
        # Upsert tags
        for tag in tags:
            self.db.upsert_tag(content_item_id, tag)
        
        if verbose:
            self.logger.info(f"    Processed: {content_item.title} -> ID {content_item_id}")
    
    def _log_dry_run_actions(self, content_item: ContentItemData, media_files: List[MediaFileData],
                            editorial: EditorialData, tags: List[TagRow], verbose: bool):
        """Log planned actions for dry run."""
        if verbose:
            self.logger.info(f"    Would create content item: {content_item.title}")
            for media_file in media_files:
                self.logger.info(f"      Would create media file: {media_file.file_path}")
            self.logger.info(f"      Would create {len(tags)} tags")