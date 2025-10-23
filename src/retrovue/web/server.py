"""
Web server for Retrovue IPTV streaming.

Provides FastAPI-based HTTP serving for MPEG-TS streams and IPTV playlists.
"""

from __future__ import annotations
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import uvicorn
import logging

from retrovue.streaming.mpegts_stream import MPEGTSStreamer

logger = logging.getLogger(__name__)

# Global storage for active streams - maps channel_id to asset info
_active_streams: dict[str, dict] = {}


def resolve_asset_by_channel_id(channel_id: str, active_streams: dict = None) -> dict:
    """
    Resolve an asset by channel ID.
    
    Args:
        channel_id: Channel identifier
        active_streams: Dictionary of active streams
        
    Returns:
        Dict with asset information: {"path": str}
    """
    # Use passed-in streams or global fallback
    streams = active_streams or _active_streams
    
    # Check if we have an active stream for this channel
    if channel_id in streams:
        logger.info(f"Found active stream for channel {channel_id}: {streams[channel_id]}")
        return streams[channel_id]
    
    # Fallback to a default asset if no active stream
    logger.warning(f"No active stream found for channel {channel_id}, using fallback")
    return {
        "path": "R:/Media/TV/The Big Bang Theory/Season 01/The Big Bang Theory (2007) - S01E02 - The Big Bran Hypothesis [WEBDL-720p][AC3 5.1][h265].mkv"
    }


def set_active_stream(channel_id: str, asset_info: dict) -> None:
    """
    Set the active stream asset for a channel.
    
    Args:
        channel_id: Channel identifier
        asset_info: Asset information dict with 'path' key
    """
    logger.info(f"Setting active stream for channel {channel_id}: {asset_info}")
    _active_streams[channel_id] = asset_info


def run_server(port: int = 8000, active_streams: dict = None):
    app = FastAPI(title="Retrovue IPTV Server")

    @app.middleware("http")
    async def streaming_headers(request: Request, call_next):
        resp: Response = await call_next(request)
        # Set appropriate headers for streaming content
        if request.url.path.endswith('.ts'):
            # MPEG-TS streams should not be cached
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            resp.headers["Content-Type"] = "video/mp2t"
        elif request.url.path.endswith('.m3u'):
            # IPTV playlists should not be cached
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            resp.headers["Content-Type"] = "application/vnd.apple.mpegurl"
        return resp

    @app.get("/iptv/channel/{channel_id}.ts")
    async def stream_channel(channel_id: str):
        """
        Streams a continuous MPEG-TS feed for the requested channel.
        """
        try:
            print(f"DEBUG: stream_channel called for channel {channel_id}")
            # Resolve asset for this channel
            asset = resolve_asset_by_channel_id(channel_id, active_streams)
            source_path = asset["path"]
            print(f"DEBUG: Resolved asset path: {source_path}")
            
            # Always create a new streamer for each request to avoid state issues
            logger.info(f"Creating new streamer for channel {channel_id} with source: {source_path}")
            streamer = MPEGTSStreamer(source_path, channel_id)
            print(f"DEBUG: Created streamer, calling start_stream()")
            
            # Return streaming response
            return StreamingResponse(
                streamer.start_stream(),
                media_type="video/mp2t",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
            
        except Exception as e:
            print(f"DEBUG: Exception in stream_channel: {e}")
            logger.error(f"Error streaming channel {channel_id}: {e}")
            return {"error": f"Failed to stream channel {channel_id}: {str(e)}"}
    
    @app.get("/iptv/channels.m3u")
    async def get_channels_playlist():
        """
        Serve IPTV channels playlist.
        TODO: Implement M3U playlist generation
        """
        # TODO: Generate M3U playlist from active channels
        return {"message": "M3U playlist endpoint - TODO"}
    
    @app.get("/iptv/guide.xml")
    async def get_guide():
        """
        Serve XMLTV guide.
        TODO: Implement XMLTV guide generation
        """
        # TODO: Generate XMLTV guide from channel schedule
        return {"message": "XMLTV guide endpoint - TODO"}

    @app.get("/")
    async def root():
        return {"message": "Retrovue IPTV Server", "status": "ready"}

    uvicorn.run(app, host="0.0.0.0", port=port)
