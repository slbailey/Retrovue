#!/usr/bin/env python3
"""
Retrovue - Main Server

A clean, unified server implementation using the Retrovue framework.
Supports multiple streaming modes through command-line arguments.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from retrovue.core import (
    ConcatDemuxerStreamer, 
    SimpleLoopStreamer, 
    StreamHandler, 
    GracefulHTTPServer
)


class RetrovueStreamHandler(StreamHandler):
    """Main HTTP handler for Retrovue streaming."""
    
    def __init__(self, *args, **kwargs):
        self.streamer = kwargs.pop('streamer')
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle streaming requests."""
        if self.path == "/channel/1.ts":
            self.serve_stream()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_stream(self):
        """Serve stream using the configured streamer."""
        concat_file_path = None
        ffmpeg_process = None
        
        try:
            # Get FFmpeg command based on streamer type
            if isinstance(self.streamer, ConcatDemuxerStreamer):
                concat_file_path = self.streamer.create_concat_file()
                ffmpeg_cmd = self.streamer.build_ffmpeg_command(concat_file_path)
                print(f"🚀 Starting ErsatzTV-style concat demuxer stream...")
                print(f"📄 Concat file: {concat_file_path}")
            else:  # SimpleLoopStreamer
                ffmpeg_cmd = self.streamer.build_ffmpeg_command()
                print(f"🚀 Starting simple loop stream...")
            
            # Send response headers
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp2t')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            print(f"🔧 FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # Start FFmpeg process
            import subprocess
            import threading
            ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=4096
            )
            
            print(f"✅ FFmpeg process started with PID: {ffmpeg_process.pid}")
            
            # Start a thread to read stderr for debugging
            def read_stderr():
                while True:
                    line = ffmpeg_process.stderr.readline()
                    if not line:
                        break
                    print(f"FFmpeg stderr: {line.decode().strip()}")
            
            stderr_thread = threading.Thread(target=read_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()
            
            # Stream output to client
            bytes_sent = 0
            while True:
                chunk = ffmpeg_process.stdout.read(4096)
                if not chunk:
                    print("❌ FFmpeg stdout ended")
                    break
                
                bytes_sent += len(chunk)
                try:
                    self.wfile.write(chunk)
                    if bytes_sent % (1024 * 1024) == 0:  # Log every MB
                        print(f"📊 Sent {bytes_sent // (1024 * 1024)} MB")
                except (ConnectionResetError, BrokenPipeError, OSError):
                    print("Client disconnected.")
                    break
            
            print(f"✅ FFmpeg process completed. Total bytes sent: {bytes_sent}")
            ffmpeg_process.terminate()
            
        except Exception as e:
            print(f"❌ Error serving stream: {e}")
        finally:
            # Clean up FFmpeg process
            if ffmpeg_process and ffmpeg_process.poll() is None:
                print("🔪 Killing FFmpeg process...")
                ffmpeg_process.kill()
                ffmpeg_process.wait()
            
            # Clean up concat file
            if concat_file_path:
                try:
                    os.unlink(concat_file_path)
                    print(f"🗑️ Cleaned up concat file: {concat_file_path}")
                except:
                    pass


def create_handler_factory(streamer):
    """Create a handler factory with the configured streamer."""
    def handler_factory(*args, **kwargs):
        return RetrovueStreamHandler(*args, streamer=streamer, **kwargs)
    return handler_factory


def main():
    """Main server function."""
    parser = argparse.ArgumentParser(description="Retrovue - IPTV Simulation Server")
    parser.add_argument(
        "--mode", 
        choices=["simple", "concat"], 
        default="simple",
        help="Streaming mode: 'simple' for -stream_loop, 'concat' for ErsatzTV-style"
    )
    parser.add_argument(
        "--media-file", 
        default=r"C:\Users\slbai\dwhelper\Showtime - After Hours Bumper.mp4",
        help="Path to media file to stream"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--loops", 
        type=int, 
        default=5,
        help="Number of loops for concat mode (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Validate media file
    media_file = Path(args.media_file)
    if not media_file.exists():
        print(f"❌ Media file not found: {media_file}")
        return 1
    
    # Create streamer based on mode
    if args.mode == "concat":
        # Create multiple copies of the same file for looping
        media_files = [str(media_file)] * args.loops
        streamer = ConcatDemuxerStreamer(media_files)
        mode_description = f"ErsatzTV-style concat demuxer ({args.loops} loops)"
    else:  # simple
        streamer = SimpleLoopStreamer(str(media_file))
        mode_description = "Simple loop with -stream_loop -1"
    
    # Print server info
    print("🌐 Retrovue - Main Server")
    print("=" * 50)
    print(f"✅ Mode: {mode_description}")
    print(f"✅ Media file: {media_file}")
    print(f"✅ Port: {args.port}")
    print(f"✅ File size: {media_file.stat().st_size:,} bytes")
    print("🌐 HTTP Server started")
    print(f"📺 TS Stream URL: http://localhost:{args.port}/channel/1.ts")
    print("🎬 To test in VLC:")
    print("   1. Open VLC Media Player")
    print("   2. Go to: Media → Open Network Stream")
    print(f"   3. Enter: http://localhost:{args.port}/channel/1.ts")
    print("   4. Click Play")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Create handler factory with streamer
        handler_factory = create_handler_factory(streamer)
        
        # Start server
        server = GracefulHTTPServer(('localhost', args.port), handler_factory)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
