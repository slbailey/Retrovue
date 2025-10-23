"""
Play command for Retrovue CLI.

Provides the ability to play episodes as live MPEG-TS streams for IPTV-style playback.
"""

from __future__ import annotations
import pathlib
import typer
from typing import Optional

from retrovue.web.server import run_server, set_active_stream
from .uow import session
from ..app.library_service import LibraryService
from ..domain.entities import ProviderRef, EntityType

def resolve_asset_by_series_season_episode(series: str, season: int, episode: int) -> dict | None:
    """
    Resolve an asset by series, season, and episode number.
    
    Args:
        series: Series title
        season: Season number
        episode: Episode number
        
    Returns:
        Dict with asset information: { "uuid": str, "uri": str, "duration_ms": int }
        or None if not found
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            # Get all episodes for the series
            assets = library_service.list_episodes_by_series(series)
            
            if not assets:
                return None
            
            # Find the specific episode by season and episode number
            for asset in assets:
                # Get provider reference for metadata
                provider_ref = db.query(ProviderRef).filter(
                    ProviderRef.asset_id == asset.id,
                    ProviderRef.entity_type == EntityType.ASSET
                ).first()
                
                if provider_ref and provider_ref.raw:
                    raw = provider_ref.raw
                    asset_season = raw.get('parentIndex')
                    asset_episode = raw.get('index')
                    
                    # Convert to integers for comparison
                    try:
                        asset_season = int(asset_season) if asset_season else 0
                        asset_episode = int(asset_episode) if asset_episode else 0
                    except (ValueError, TypeError):
                        continue
                    
                    # Check if this matches our target season/episode
                    if asset_season == season and asset_episode == episode:
                        return {
                            "uuid": str(asset.uuid),
                            "uri": asset.uri,
                            "duration_ms": asset.duration_ms or 0
                        }
            
            return None
            
        except Exception as e:
            # Log error but don't raise - let caller handle
            print(f"Error resolving asset: {e}")
            return None

def resolve_asset_by_channel_id(channel_id: str) -> dict | None:
    """
    Resolve an asset by channel ID.
    
    Args:
        channel_id: Channel identifier
        
    Returns:
        Dict with asset information: {"path": str}
        or None if not found
    """
    # TODO: Map channel_id to episode/asset UUID from Retrovue database
    # For now, return a test asset path for local playback
    return {
        "path": "R:/Media/TV/The Big Bang Theory/Season 01/The Big Bang Theory (2007) - S01E02 - The Big Bran Hypothesis [WEBDL-720p][AC3 5.1][h265].mkv"
    }


def play(
    series: str = typer.Argument(..., help="Series title, e.g. 'Cheers'"),
    season: int = typer.Option(..., "--season", "-s", help="Season number"),
    episode: int = typer.Option(..., "--episode", "-e", help="Episode number"),
    channel_id: int = typer.Option(1, "--channel-id", "-c", help="Channel ID for IPTV streaming"),
    port: int = typer.Option(8000, "--port", "-p", help="HTTP port to serve MPEG-TS streams"),
    transcode: bool = typer.Option(False, "--transcode", help="Transcode to H.264/AAC for broader compatibility"),
):
    """
    Resolve an episode from the content library and expose it as a live MPEG-TS stream for IPTV playback.
    """
    # 1) Resolve asset via your content library
    asset = resolve_asset_by_series_season_episode(series, season, episode)
    if not asset:
        typer.echo(f"[error] Could not resolve asset for {series} S{season:02d}E{episode:02d}", err=True)
        raise typer.Exit(code=1)

    # Normalize path: handle 'file://R:\\...'
    uri = asset["uri"]
    if uri.startswith("file://"):
        # Strip scheme; pathlib can handle Windows paths once scheme removed
        src_path = pathlib.Path(uri.replace("file://", "", 1))
    else:
        src_path = pathlib.Path(uri)

    if not src_path.exists():
        typer.echo(f"[error] Source path does not exist: {src_path}", err=True)
        raise typer.Exit(code=2)

    typer.echo(f"Starting MPEG-TS stream for {series} S{season:02d}E{episode:02d} on channel {channel_id}")
    typer.echo(f"Source file: {src_path}")
    typer.echo(f"Stream will be available at: http://localhost:{port}/iptv/channel/{channel_id}.ts")
    
    # Create active streams dict for the server
    active_streams = {str(channel_id): {"path": str(src_path)}}
    
    try:
        # Start the IPTV server with the resolved asset
        run_server(port=port, active_streams=active_streams)
    except KeyboardInterrupt:
        typer.echo("\nShutting down...")


def play_channel(
    channel_id: int = typer.Argument(..., help="Channel ID to stream"),
    port: int = typer.Option(8000, "--port", "-p", help="HTTP port to serve MPEG-TS streams"),
):
    """
    Start a channel stream directly from CLI.
    
    This command starts the IPTV server and makes the specified channel available
    as a continuous MPEG-TS stream.
    """
    typer.echo(f"Starting IPTV server for channel {channel_id}")
    typer.echo(f"Stream will be available at: http://localhost:{port}/iptv/channel/{channel_id}.ts")
    typer.echo("Press Ctrl+C to stop the server")
    
    try:
        # Start the IPTV server
        run_server(port=port)
    except KeyboardInterrupt:
        typer.echo("\nShutting down...")

if __name__ == "__main__":
    # This module should not be run directly
    # Use: python -m retrovue.cli.main play
    import sys
    print("Error: This module should not be run directly.")
    print("Use: python -m retrovue.cli.main play")
    sys.exit(1)
