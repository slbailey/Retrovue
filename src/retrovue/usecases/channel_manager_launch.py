"""
Channel Manager usecase: Air process management.

Functions for launching and terminating Retrovue Air processes per channel.
Per ChannelManagerContract.md (Phase 8).
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

# Type alias for subprocess.Process
ProcessHandle = subprocess.Popen[bytes]


def launch_air(
    *,
    playout_request: dict[str, Any],
    stdin: Any = subprocess.PIPE,
    stdout: Any = subprocess.PIPE,
    stderr: Any = subprocess.PIPE,
) -> ProcessHandle:
    """
    Launch a Retrovue Air process for a channel.
    
    Per ChannelManagerContract.md (Phase 8):
    - Launches Air as child process
    - Sends PlayoutRequest JSON via stdin
    - Closes stdin immediately after sending
    
    Args:
        playout_request: PlayoutRequest dictionary (asset_path, start_pts, mode, channel_id, metadata)
        channel_id: Channel identifier
        stdin: stdin pipe (default: subprocess.PIPE)
        stdout: stdout pipe (default: subprocess.PIPE)
        stderr: stderr pipe (default: subprocess.PIPE)
    
    Returns:
        Process handle (subprocess.Popen) for the launched Air process
    
    Example:
        ```python
        playout_request = {
            "asset_path": "/path/to/video.mp4",
            "start_pts": 0,
            "mode": "LIVE",
            "channel_id": "retro1",
            "metadata": {}
        }
        process = launch_air(playout_request=playout_request, channel_id="retro1")
        ```
    """
    # Build Air CLI command
    # Per PlayoutRequest.md: --channel-id <id> --mode live --request-json-stdin
    channel_id = playout_request.get("channel_id", "unknown")
    cmd = [
        "retrovue_air",  # TODO: Get actual Air command path from config
        "--channel-id", channel_id,
        "--mode", "live",
        "--request-json-stdin",
    ]
    
    # Launch process
    process = subprocess.Popen(
        cmd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        text=False,  # Binary mode for stdin/stdout/stderr
        bufsize=0,  # Unbuffered
    )
    
    # Send PlayoutRequest JSON via stdin
    # Per ChannelManagerContract.md: Send exactly one PlayoutRequest JSON, then close stdin
    if stdin == subprocess.PIPE and process.stdin:
        try:
            json_bytes = json.dumps(playout_request).encode("utf-8")
            process.stdin.write(json_bytes)
            process.stdin.flush()
            process.stdin.close()
        except Exception as e:
            # If stdin write fails, terminate process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise RuntimeError(f"Failed to send PlayoutRequest to Air: {e}") from e
    
    return process


def terminate_air(process: ProcessHandle) -> None:
    """
    Terminate a Retrovue Air process.
    
    Per ChannelManagerContract.md (Phase 8):
    - Terminates Air process when client_count drops to 0
    
    Args:
        process: Process handle from launch_air()
    
    Example:
        ```python
        process = launch_air(...)
        # ... later ...
        terminate_air(process)
        ```
    """
    if process.poll() is None:  # Process still running
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


__all__ = ["launch_air", "terminate_air", "ProcessHandle"]

