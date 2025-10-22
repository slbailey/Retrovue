"""
Content validation system for ensuring media files are playable and accessible.

Validates file existence, codec support, metadata integrity, and path resolution.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("retrovue.plex")


class ValidationStatus(Enum):
    """Validation status for content items."""
    VALID = "valid"
    FILE_NOT_FOUND = "file_not_found"
    FILE_NOT_ACCESSIBLE = "file_not_accessible"
    INVALID_CODEC = "invalid_codec"
    INVALID_METADATA = "invalid_metadata"
    PATH_MAPPING_FAILED = "path_mapping_failed"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ValidationResult:
    """Result of content validation."""
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    duration_ms: Optional[int] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    resolution: Optional[Tuple[int, int]] = None


class ContentValidator:
    """Validates content items for playability and accessibility."""
    
    def __init__(self, path_mapper, ffprobe_path: Optional[str] = None):
        """
        Initialize content validator.
        
        Args:
            path_mapper: PathMapper instance for resolving paths
            ffprobe_path: Optional path to ffprobe executable
        """
        self.path_mapper = path_mapper
        self.ffprobe_path = ffprobe_path or "ffprobe"
        
        # Supported codecs for streaming
        self.supported_video_codecs = {
            'h264', 'h265', 'hevc', 'avc1', 'x264', 'x265',
            'mpeg2video', 'mpeg4', 'vp8', 'vp9', 'av1'
        }
        
        self.supported_audio_codecs = {
            'aac', 'mp3', 'ac3', 'eac3', 'dts', 'flac', 'pcm',
            'opus', 'vorbis', 'mp2', 'wma'
        }
    
    def validate_media_file(self, server_id: int, library_id: int, 
                           plex_path: str, media_info: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate a media file for playability.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex file path
            media_info: Optional media information from Plex
            
        Returns:
            ValidationResult with validation status and details
        """
        try:
            # Step 1: Resolve path mapping
            local_path = self.path_mapper.resolve(server_id, library_id, plex_path)
            if not local_path:
                return ValidationResult(
                    status=ValidationStatus.PATH_MAPPING_FAILED,
                    message=f"Could not resolve path mapping for: {plex_path}",
                    local_path=None
                )
            
            # Step 2: Check file existence and accessibility
            file_path = Path(local_path)
            if not file_path.exists():
                return ValidationResult(
                    status=ValidationStatus.FILE_NOT_FOUND,
                    message=f"File does not exist: {local_path}",
                    local_path=local_path
                )
            
            if not file_path.is_file():
                return ValidationResult(
                    status=ValidationStatus.FILE_NOT_ACCESSIBLE,
                    message=f"Path is not a file: {local_path}",
                    local_path=local_path
                )
            
            # Step 3: Get file information
            file_size = file_path.stat().st_size
            if file_size == 0:
                return ValidationResult(
                    status=ValidationStatus.FILE_NOT_ACCESSIBLE,
                    message=f"File is empty: {local_path}",
                    local_path=local_path,
                    file_size=file_size
                )
            
            # Step 4: Validate codecs and metadata
            validation_result = self._validate_media_properties(local_path, media_info)
            validation_result.local_path = local_path
            validation_result.file_size = file_size
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation error for {plex_path}: {e}")
            return ValidationResult(
                status=ValidationStatus.UNKNOWN_ERROR,
                message=f"Validation failed: {str(e)}",
                local_path=local_path if 'local_path' in locals() else None
            )
    
    def _validate_media_properties(self, file_path: str, media_info: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate media properties using ffprobe.
        
        Args:
            file_path: Local file path
            media_info: Optional media information from Plex
            
        Returns:
            ValidationResult with validation status
        """
        try:
            # Use ffprobe to get media information
            media_data = self._get_media_info(file_path)
            if not media_data:
                return ValidationResult(
                    status=ValidationStatus.INVALID_METADATA,
                    message="Could not extract media information"
                )
            
            # Validate video codec
            video_codec = media_data.get('video_codec', '').lower()
            if video_codec and video_codec not in self.supported_video_codecs:
                return ValidationResult(
                    status=ValidationStatus.INVALID_CODEC,
                    message=f"Unsupported video codec: {video_codec}",
                    video_codec=video_codec,
                    duration_ms=media_data.get('duration_ms'),
                    resolution=media_data.get('resolution')
                )
            
            # Validate audio codec
            audio_codec = media_data.get('audio_codec', '').lower()
            if audio_codec and audio_codec not in self.supported_audio_codecs:
                return ValidationResult(
                    status=ValidationStatus.INVALID_CODEC,
                    message=f"Unsupported audio codec: {audio_codec}",
                    audio_codec=audio_codec,
                    duration_ms=media_data.get('duration_ms'),
                    resolution=media_data.get('resolution')
                )
            
            # Validate duration
            duration_ms = media_data.get('duration_ms', 0)
            if duration_ms <= 0:
                return ValidationResult(
                    status=ValidationStatus.INVALID_METADATA,
                    message="Invalid or zero duration",
                    duration_ms=duration_ms
                )
            
            # All validations passed
            return ValidationResult(
                status=ValidationStatus.VALID,
                message="File is valid and playable",
                duration_ms=duration_ms,
                video_codec=video_codec,
                audio_codec=audio_codec,
                resolution=media_data.get('resolution'),
                details=media_data
            )
            
        except Exception as e:
            logger.error(f"Media validation error for {file_path}: {e}")
            return ValidationResult(
                status=ValidationStatus.UNKNOWN_ERROR,
                message=f"Media validation failed: {str(e)}"
            )
    
    def _get_media_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get media information using ffprobe.
        
        Args:
            file_path: Local file path
            
        Returns:
            Dictionary with media information or None if failed
        """
        try:
            import subprocess
            import json
            
            # Run ffprobe to get media information
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.warning(f"ffprobe failed for {file_path}: {result.stderr}")
                return None
            
            data = json.loads(result.stdout)
            
            # Extract relevant information
            format_info = data.get('format', {})
            streams = data.get('streams', [])
            
            # Find video and audio streams
            video_stream = None
            audio_stream = None
            
            for stream in streams:
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            # Extract information
            duration_ms = int(float(format_info.get('duration', 0)) * 1000)
            
            video_codec = None
            resolution = None
            if video_stream:
                video_codec = video_stream.get('codec_name', '')
                width = video_stream.get('width')
                height = video_stream.get('height')
                if width and height:
                    resolution = (int(width), int(height))
            
            audio_codec = None
            if audio_stream:
                audio_codec = audio_stream.get('codec_name', '')
            
            return {
                'duration_ms': duration_ms,
                'video_codec': video_codec,
                'audio_codec': audio_codec,
                'resolution': resolution,
                'file_size': format_info.get('size'),
                'bitrate': format_info.get('bit_rate')
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"ffprobe timeout for {file_path}")
            return None
        except Exception as e:
            logger.error(f"ffprobe error for {file_path}: {e}")
            return None
    
    def validate_batch(self, items: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate a batch of media files.
        
        Args:
            items: List of items with server_id, library_id, plex_path, and optional media_info
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for item in items:
            result = self.validate_media_file(
                server_id=item['server_id'],
                library_id=item['library_id'],
                plex_path=item['plex_path'],
                media_info=item.get('media_info')
            )
            results.append(result)
        
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get a summary of validation results.
        
        Args:
            results: List of ValidationResult objects
            
        Returns:
            Dictionary with validation summary
        """
        summary = {
            'total': len(results),
            'valid': 0,
            'invalid': 0,
            'by_status': {},
            'errors': []
        }
        
        for result in results:
            if result.status == ValidationStatus.VALID:
                summary['valid'] += 1
            else:
                summary['invalid'] += 1
                summary['errors'].append({
                    'status': result.status.value,
                    'message': result.message,
                    'local_path': result.local_path
                })
            
            status_key = result.status.value
            if status_key not in summary['by_status']:
                summary['by_status'][status_key] = 0
            summary['by_status'][status_key] += 1
        
        return summary

