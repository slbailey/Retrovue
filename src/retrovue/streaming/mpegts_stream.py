"""
MPEG-TS Streaming for Retrovue.

Provides continuous MPEG-TS streaming for IPTV-style live playback.
This module will replace the HLS-based streaming system.
"""

from __future__ import annotations
import logging
import pathlib
import subprocess
import threading
import time
from typing import Generator, Optional

logger = logging.getLogger(__name__)


class MPEGTSStreamer:
    """
    MPEG-TS streamer for continuous IPTV-style streaming.
    
    This class generates endless MPEG-TS streams that can be served
    via HTTP for IPTV clients.
    """
    
    def __init__(self, source_path: str, channel_id: str):
        """
        Initialize the MPEG-TS streamer.
        
        Args:
            source_path: Path to the source video file
            channel_id: Channel identifier for this stream
        """
        self.source_path = source_path
        self.channel_id = channel_id
        self.proc: Optional[subprocess.Popen] = None
        self._running = False
        self._lock = threading.Lock()
    
    def start_stream(self) -> Generator[bytes, None, None]:
        """
        Start the MPEG-TS stream and yield video data.
        
        Yields:
            bytes: MPEG-TS video data chunks
        """
        print(f"DEBUG: start_stream called for channel {self.channel_id}")
        with self._lock:
            if self._running:
                logger.warning(f"Stream for channel {self.channel_id} is already running")
                return
            
            # Clean up any existing process first
            self._cleanup()
            self._running = True
        
        try:
            logger.info(f"Starting MPEG-TS stream for channel {self.channel_id} from {self.source_path}")
            
            # Build FFmpeg command for continuous MPEG-TS streaming
            cmd = [
                "ffmpeg",
                "-nostats", "-hide_banner", "-loglevel", "warning",
                "-fflags", "+genpts",
                "-muxpreload", "0", "-muxdelay", "0",
                "-re",  # Real-time pacing
                "-stream_loop", "-1",  # Infinite loop
                "-i", str(self.source_path),
                "-map", "0:v:0", "-map", "0:a:0", "-sn", "-dn",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-tune", "zerolatency",
                "-profile:v", "main",
                "-pix_fmt", "yuv420p",
                "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
                "-c:a", "aac",
                "-b:a", "128k",  # Audio bitrate
                "-ac", "2",  # Stereo audio
                "-ar", "48000",  # Sample rate
                "-f", "mpegts",
                "pipe:1"  # Output to stdout
            ]
            
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Start FFmpeg process
            print(f"DEBUG: Starting FFmpeg process with command: {' '.join(cmd)}")
            logger.info(f"Starting FFmpeg process with command: {' '.join(cmd)}")
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout to prevent blocking
                bufsize=0  # Unbuffered output
            )
            print(f"DEBUG: FFmpeg process started with PID: {self.proc.pid}")
            logger.info(f"FFmpeg process started with PID: {self.proc.pid}")
            
            # Stream data from FFmpeg stdout
            try:
                TS_CHUNK = 188 * 40  # 7,520 bytes, multiple of TS packet size
                for chunk in iter(lambda: self.proc.stdout.read(TS_CHUNK), b""):
                    if not self._running or self.proc.poll() is not None:
                        break
                    yield chunk
                
                # Check if process exited unexpectedly
                if self.proc.poll() is not None:
                    logger.error(f"FFmpeg process exited unexpectedly for channel {self.channel_id}")
                    
                    # Restart the stream if it was supposed to be running
                    if self._running:
                        logger.info(f"Restarting stream for channel {self.channel_id}")
                        self._restart_stream()
                        
            except Exception as e:
                logger.error(f"Error reading from FFmpeg stdout for channel {self.channel_id}: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to start stream for channel {self.channel_id}: {e}")
            raise
        finally:
            self._cleanup()
    
    def _restart_stream(self) -> None:
        """Restart the FFmpeg process if it crashes."""
        if not self._running:
            return
            
        try:
            # Clean up existing process
            if self.proc:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            
            # Start new process
            cmd = [
                "ffmpeg",
                "-nostats", "-hide_banner", "-loglevel", "warning",
                "-fflags", "+genpts",
                "-muxpreload", "0", "-muxdelay", "0",
                "-re",
                "-stream_loop", "-1",
                "-i", str(self.source_path),
                "-map", "0:v:0", "-map", "0:a:0", "-sn", "-dn",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-tune", "zerolatency",
                "-profile:v", "main",
                "-pix_fmt", "yuv420p",
                "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
                "-c:a", "aac",
                "-b:a", "128k",  # Audio bitrate
                "-ac", "2",  # Stereo audio
                "-ar", "48000",  # Sample rate
                "-f", "mpegts",
                "pipe:1"
            ]
            
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout to prevent blocking
                bufsize=0
            )
            
            logger.info(f"Successfully restarted stream for channel {self.channel_id}")
            
        except Exception as e:
            logger.error(f"Failed to restart stream for channel {self.channel_id}: {e}")
            self._running = False
    
    def stop_stream(self) -> None:
        """Stop the MPEG-TS stream safely."""
        with self._lock:
            if not self._running:
                return
                
            self._running = False
            logger.info(f"Stopping stream for channel {self.channel_id}")
        
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up the FFmpeg process."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing FFmpeg process for channel {self.channel_id}")
                self.proc.kill()
            except Exception as e:
                logger.error(f"Error cleaning up FFmpeg process for channel {self.channel_id}: {e}")
            finally:
                self.proc = None
