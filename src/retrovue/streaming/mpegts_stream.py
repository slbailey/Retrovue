"""
MPEG-TS Streaming for Retrovue.

Provides continuous MPEG-TS streaming for IPTV-style live playback with support for
segment-based commercial insertion. This module uses FFmpeg concat input format to
enable seamless insertion of interstitial content (commercials) into video streams.

For detailed documentation, see docs/streaming/mpegts-streaming.md
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
        self._stderr_thread: Optional[threading.Thread] = None
    
    def _process_source_path(self) -> str:
        """
        Process the source path for FFmpeg compatibility.
        
        Returns:
            Processed path with file:// prefix stripped, no additional quoting
        """
        src = self.source_path
        if src.startswith("file://"):
            src = src[7:]
        
        # Return the path as-is, let subprocess handle the quoting
        return src
    
    def _process_concat_file(self) -> str:
        """
        Create a concat file for FFmpeg concat input.
        
        This method creates a temporary FFmpeg concat file that lists the video files
        to be concatenated. For commercial insertion, this would be extended to include
        multiple segments and commercial breaks.
        
        Current implementation creates a simple concat file with a single video file.
        For commercial insertion, this would be enhanced to include:
        - Episode segments
        - Commercial breaks
        - Transition effects
        
        Returns:
            Path to the temporary concat file
            
        Example concat file content:
        ```
        file 'R:\Media\TV\Episode\segment1.mp4'
        file 'R:\Media\Commercials\commercial1.mp4'
        file 'R:\Media\TV\Episode\segment2.mp4'
        ```
        """
        import tempfile
        import os
        
        # Create a temporary concat file
        # TODO: For commercial insertion, this should be enhanced to include
        # multiple segments and commercial breaks
        concat_content = f"file '{self._process_source_path()}'\n"
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(concat_content)
            concat_file_path = f.name
        
        return concat_file_path
    
    def create_segmented_concat_file(self, episode_path: str, commercial_paths: list[str], break_points: list[float]) -> str:
        """
        Create a concat file with episode segments and commercial breaks.
        
        This method implements the core commercial insertion functionality by creating
        a concat file that alternates between episode segments and commercial breaks.
        
        Args:
            episode_path: Path to the main episode file
            commercial_paths: List of commercial file paths to insert
            break_points: List of timestamps (in seconds) where breaks should occur
            
        Returns:
            Path to the generated concat file
            
        Example:
            episode_path = "R:/Media/TV/Episode.mp4"
            commercial_paths = ["R:/Media/Commercials/ad1.mp4", "R:/Media/Commercials/ad2.mp4"]
            break_points = [300.0, 600.0]  # 5 minutes and 10 minutes
            
            This creates a concat file with:
            - Episode segment 1 (0-5 minutes)
            - Commercial 1
            - Episode segment 2 (5-10 minutes) 
            - Commercial 2
            - Episode segment 3 (10+ minutes)
        """
        import tempfile
        import subprocess
        
        concat_content = []
        
        # For each break point, we need to create segments
        # This is a simplified implementation - in practice, you'd need to:
        # 1. Analyze the episode to find natural break points
        # 2. Split the episode into segments at those points
        # 3. Create concat file with segments and commercials
        
        # Current implementation assumes the episode is already segmented
        # TODO: Implement actual episode segmentation using FFmpeg
        
        for i, break_point in enumerate(break_points):
            # Add episode segment (this would be a pre-segmented file)
            segment_path = f"{episode_path}_segment_{i+1}.mp4"
            concat_content.append(f"file '{segment_path}'")
            
            # Add commercial if available
            if i < len(commercial_paths):
                concat_content.append(f"file '{commercial_paths[i]}'")
        
        # Add final segment if there are remaining break points
        if len(break_points) < len(commercial_paths):
            final_segment = f"{episode_path}_segment_{len(break_points)+1}.mp4"
            concat_content.append(f"file '{final_segment}'")
        
        # Write concat file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(concat_content))
            return f.name
    
    def segment_episode(self, episode_path: str, break_points: list[float]) -> list[str]:
        """
        Segment an episode into multiple files at specified break points.
        
        This method uses FFmpeg to split an episode into segments at natural break points.
        This is essential for commercial insertion as it allows precise control over
        where commercials are inserted.
        
        Args:
            episode_path: Path to the episode file to segment
            break_points: List of timestamps where to create breaks
            
        Returns:
            List of paths to the created segment files
            
        Example:
            episode_path = "R:/Media/TV/Episode.mp4"
            break_points = [300.0, 600.0]  # 5 minutes and 10 minutes
            
            This creates:
            - Episode_segment_1.mp4 (0-5 minutes)
            - Episode_segment_2.mp4 (5-10 minutes)
            - Episode_segment_3.mp4 (10+ minutes)
        """
        import tempfile
        import subprocess
        import os
        
        segment_paths = []
        base_name = os.path.splitext(episode_path)[0]
        
        # Create segments using FFmpeg
        for i, break_point in enumerate(break_points):
            start_time = break_points[i-1] if i > 0 else 0
            duration = break_point - start_time
            
            segment_path = f"{base_name}_segment_{i+1}.mp4"
            
            # FFmpeg command to extract segment
            cmd = [
                "ffmpeg",
                "-i", episode_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-c", "copy",  # Copy streams without re-encoding
                "-avoid_negative_ts", "make_zero",
                segment_path
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                segment_paths.append(segment_path)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create segment {i+1}: {e}")
                raise
        
        # Create final segment (from last break point to end)
        if break_points:
            start_time = break_points[-1]
            final_segment = f"{base_name}_segment_{len(break_points)+1}.mp4"
            
            cmd = [
                "ffmpeg",
                "-i", episode_path,
                "-ss", str(start_time),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                final_segment
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                segment_paths.append(final_segment)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create final segment: {e}")
                raise
        
        return segment_paths
    
    def _drain_stderr(self):
        """
        Drain stderr in a background thread to prevent blocking.
        """
        try:
            if self.proc and hasattr(self.proc, 'stderr') and self.proc.stderr:
                stderr_pipe = self.proc.stderr
                for chunk in iter(lambda: stderr_pipe.read(4096), b""):
                    if chunk:
                        # Log FFmpeg stderr output for debugging
                        stderr_text = chunk.decode('utf-8', errors='ignore').strip()
                        if stderr_text:
                            logger.error(f"FFmpeg stderr: {stderr_text}")
                            print(f"DEBUG: FFmpeg stderr: {stderr_text}")
        except Exception as e:
            logger.error(f"Error reading FFmpeg stderr: {e}")
            print(f"DEBUG: Error reading FFmpeg stderr: {e}")
    
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
                # Global options
                "-nostdin", "-hide_banner", "-nostats", "-loglevel", "error",
                # Input options for concat streaming
                "-fflags", "+genpts+discardcorrupt+igndts", "-readrate", "1.0", "-re", "-stream_loop", "-1",
                "-f", "concat", "-safe", "0", "-protocol_whitelist", "file,http,tcp,https,tcp,tls", "-probesize", "32",
                "-i", self._process_concat_file(),
                # Map video and audio
                "-map", "0:v:0", "-map", "0:a:0", "-sn", "-dn",
                # Video encoding
                "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-profile:v", "main", "-pix_fmt", "yuv420p",
                "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
                # Audio encoding
                "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
                # Streaming optimizations
                "-movflags", "+faststart", "-flags", "cgop", "-bf", "0",
                # Output options (mux latency settings)
                "-muxpreload", "0", "-muxdelay", "0",
                # Output format (with initial_discontinuity for concat streams)
                "-f", "mpegts", "-mpegts_flags", "+initial_discontinuity",
                "pipe:1"
            ]
            
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Start FFmpeg process
            print(f"DEBUG: Starting FFmpeg process with command: {' '.join(cmd)}")
            logger.info(f"Starting FFmpeg process with command: {' '.join(cmd)}")
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Separate stderr pipe
                bufsize=0  # Unbuffered output
            )
            print(f"DEBUG: FFmpeg process started with PID: {self.proc.pid}")
            logger.info(f"FFmpeg process started with PID: {self.proc.pid}")
            
            # Start stderr drainer thread
            self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
            self._stderr_thread.start()
            
            # Stream data from FFmpeg stdout
            try:
                if self.proc and hasattr(self.proc, 'stdout') and self.proc.stdout:
                    TS_CHUNK = 188 * 40  # 7,520 bytes, multiple of TS packet size
                    chunk_count = 0
                    stdout_pipe = self.proc.stdout
                    for chunk in iter(lambda: stdout_pipe.read(TS_CHUNK), b""):
                        if not self._running or self.proc.poll() is not None:
                            break
                        chunk_count += 1
                        if chunk_count <= 5:  # Log first few chunks for debugging
                            print(f"DEBUG: Yielding chunk {chunk_count}, size: {len(chunk)} bytes")
                        yield chunk
                
                print(f"DEBUG: Total chunks yielded: {chunk_count}")
                
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
                # Global options
                "-nostdin", "-hide_banner", "-nostats", "-loglevel", "error",
                # Input options for concat streaming
                "-fflags", "+genpts+discardcorrupt+igndts", "-readrate", "1.0", "-re", "-stream_loop", "-1",
                "-f", "concat", "-safe", "0", "-protocol_whitelist", "file,http,tcp,https,tcp,tls", "-probesize", "32",
                "-i", self._process_concat_file(),
                # Map video and audio
                "-map", "0:v:0", "-map", "0:a:0", "-sn", "-dn",
                # Video encoding
                "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-profile:v", "main", "-pix_fmt", "yuv420p",
                "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
                # Audio encoding
                "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
                # Streaming optimizations
                "-movflags", "+faststart", "-flags", "cgop", "-bf", "0",
                # Output options (mux latency settings)
                "-muxpreload", "0", "-muxdelay", "0",
                # Output format (with initial_discontinuity for concat streams)
                "-f", "mpegts", "-mpegts_flags", "+initial_discontinuity",
                "pipe:1"
            ]
            
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Separate stderr pipe
                bufsize=0
            )
            
            # Start stderr drainer thread
            self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
            self._stderr_thread.start()
            
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
        # Join stderr thread if it exists
        if self._stderr_thread and self._stderr_thread.is_alive():
            try:
                self._stderr_thread.join(timeout=1.0)
            except Exception:
                pass  # Best effort cleanup
        
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
                self._stderr_thread = None

