"""
Retrovue Core Streaming Components

Professional streaming implementations for IPTV simulation.
"""

import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler


class ConcatDemuxerStreamer:
    """
    ErsatzTV-style streaming using FFmpeg's concat demuxer.
    
    This implementation uses the same approach as ErsatzTV for seamless
    transitions between media files using FFmpeg's -f concat demuxer.
    """
    
    def __init__(self, media_files: List[str], output_format: str = "mpegts"):
        """
        Initialize the concat demuxer streamer.
        
        Args:
            media_files: List of media file paths to concatenate
            output_format: Output format (default: mpegts)
        """
        self.media_files = [Path(f) for f in media_files]
        self.output_format = output_format
        self._validate_files()
    
    def _validate_files(self):
        """Validate that all media files exist."""
        for file_path in self.media_files:
            if not file_path.exists():
                raise FileNotFoundError(f"Media file not found: {file_path}")
    
    def create_concat_file(self) -> str:
        """
        Create a temporary concat file for FFmpeg.
        
        Returns:
            Path to the temporary concat file
        """
        concat_content = "\n".join(f"file '{file_path}'" for file_path in self.media_files)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as concat_file:
            concat_file.write(concat_content)
            return concat_file.name
    
    def build_ffmpeg_command(self, concat_file_path: str) -> List[str]:
        """
        Build the FFmpeg command for concat demuxer streaming.
        
        Args:
            concat_file_path: Path to the concat file
            
        Returns:
            List of FFmpeg command arguments
        """
        return [
            "ffmpeg",
            "-re",  # Real-time input
            "-f", "concat",  # Use concat demuxer (ErsatzTV's approach)
            "-safe", "0",  # Allow unsafe file paths
            "-protocol_whitelist", "file,http,tcp,https,tcp,tls",
            "-probesize", "32",  # Small probe size for faster startup
            "-i", concat_file_path,  # Input concat file
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:v", "1M",
            "-b:a", "128k",
            "-g", "30",  # Keyframe every 30 frames
            "-keyint_min", "30",  # Minimum keyframe interval
            "-sc_threshold", "0",  # Disable scene change detection
            "-avoid_negative_ts", "make_zero",  # Handle timestamp issues
            "-fflags", "+genpts",  # Generate presentation timestamps
            "-f", self.output_format,
            "-mpegts_flags", "+initial_discontinuity",
            "pipe:1"
        ]


class SimpleLoopStreamer:
    """
    Simple streaming using FFmpeg's stream_loop parameter.
    
    This implementation uses -stream_loop -1 for infinite looping
    of a single media file.
    """
    
    def __init__(self, media_file: str, output_format: str = "mpegts"):
        """
        Initialize the simple loop streamer.
        
        Args:
            media_file: Path to the media file to loop
            output_format: Output format (default: mpegts)
        """
        self.media_file = Path(media_file)
        self.output_format = output_format
        self._validate_file()
    
    def _validate_file(self):
        """Validate that the media file exists."""
        if not self.media_file.exists():
            raise FileNotFoundError(f"Media file not found: {self.media_file}")
    
    def build_ffmpeg_command(self) -> List[str]:
        """
        Build the FFmpeg command for simple loop streaming.
        
        Returns:
            List of FFmpeg command arguments
        """
        return [
            "ffmpeg",
            "-re",  # Read input at native frame rate
            "-stream_loop", "-1",  # Loop input forever
            "-i", str(self.media_file),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:v", "1M",
            "-b:a", "128k",
            "-g", "30",  # Keyframe every 30 frames
            "-keyint_min", "30",  # Minimum keyframe interval
            "-sc_threshold", "0",  # Disable scene change detection
            "-avoid_negative_ts", "make_zero",  # Handle timestamp issues
            "-fflags", "+genpts",  # Generate presentation timestamps
            "-f", self.output_format,
            "-mpegts_flags", "+initial_discontinuity",
            "pipe:1"
        ]


class StreamHandler(BaseHTTPRequestHandler):
    """
    Base HTTP request handler for streaming endpoints.
    
    Provides common functionality for streaming HTTP handlers.
    """
    
    def log_message(self, format, *args):
        """Override to reduce log noise for streaming requests."""
        if "GET /channel/" in format % args:
            print(f"📺 Stream request: {format % args}")
        else:
            super().log_message(format, *args)


class GracefulHTTPServer(HTTPServer):
    """
    HTTP Server that handles client disconnections gracefully.
    
    Suppresses tracebacks for common connection errors like
    ConnectionResetError when clients disconnect.
    """
    
    def handle_error(self, request, client_address):
        """Override to handle connection errors gracefully."""
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        if exc_type and issubclass(exc_type, (ConnectionResetError, BrokenPipeError, OSError)):
            print(f"✅ Client {client_address} disconnected gracefully")
            return
        
        # For other errors, show the full traceback
        super().handle_error(request, client_address)
