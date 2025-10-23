# MPEG-TS Streaming for Retrovue

Provides continuous MPEG-TS streaming for IPTV-style live playback with support for
segment-based commercial insertion. This module uses FFmpeg concat input format to
enable seamless insertion of interstitial content (commercials) into video streams.

## Architecture Overview

This streaming system is designed to mirror ErsatzTV's proven concat streaming approach:

1. **Concat Input Format**: Uses FFmpeg's `-f concat` input to concatenate multiple video files
2. **Initial Discontinuity**: Uses `-mpegts_flags +initial_discontinuity` for proper concat streaming
3. **Segment-Based Playback**: Enables breaking episodes into segments with commercial breaks

## Commercial Insertion Strategy

The system supports mid-roll commercial insertion by:

1. **Episode Segmentation**: Breaking long episodes into smaller segments
2. **Concat File Generation**: Creating FFmpeg concat files that list:

   - Episode segment 1
   - Commercial break
   - Episode segment 2
   - Commercial break
   - Episode segment 3
   - etc.

3. **Seamless Playback**: FFmpeg handles the transitions between segments automatically

## FFmpeg Command Structure

The generated FFmpeg command follows ErsatzTV's proven pattern:

```
ffmpeg -nostdin -hide_banner -nostats -loglevel error
       -fflags +genpts+discardcorrupt+igndts -readrate 1.0 -re -stream_loop -1
       -f concat -safe 0 -protocol_whitelist file,http,tcp,https,tcp,tls -probesize 32
       -i "concat_file.txt"
       -map 0:v:0 -map 0:a:0 -sn -dn
       -c:v libx264 -preset veryfast -tune zerolatency -profile:v main -pix_fmt yuv420p
       -g 60 -keyint_min 60 -sc_threshold 0
       -c:a aac -b:a 128k -ac 2 -ar 48000
       -movflags +faststart -flags cgop -bf 0
       -muxpreload 0 -muxdelay 0
       -f mpegts -mpegts_flags +initial_discontinuity
       pipe:1
```

## Key Components

### 1. Concat File Format

FFmpeg concat files are simple text files listing video files to concatenate:

```
file '/path/to/segment1.mp4'
file '/path/to/commercial1.mp4'
file '/path/to/segment2.mp4'
file '/path/to/commercial2.mp4'
```

### 2. Initial Discontinuity Flag

The `+initial_discontinuity` flag is crucial for concat streaming:

- **Required for**: Concatenating multiple files
- **Not needed for**: Single file streaming
- **Purpose**: Tells MPEG-TS muxer to expect discontinuities between files

### 3. Streaming Optimizations

- **`-movflags +faststart`**: Enables fast start for streaming
- **`-flags cgop`**: Closed GOP for better streaming compatibility
- **`-bf 0`**: No B-frames for lower latency
- **`-muxpreload 0 -muxdelay 0`**: Low mux latency

## Implementation for Commercial Insertion

To implement segment-based commercial insertion:

1. **Episode Analysis**: Analyze episode duration and identify natural break points
2. **Segment Creation**: Split episode into segments at break points
3. **Concat File Generation**: Create concat files with segments and commercials
4. **Dynamic Updates**: Update concat files as playback progresses

### Example Implementation:

```python
def create_segmented_concat_file(episode_path, commercial_paths, break_points):
    """
    Create a concat file with episode segments and commercial breaks.

    Args:
        episode_path: Path to the main episode file
        commercial_paths: List of commercial file paths
        break_points: List of timestamps where breaks should occur

    Returns:
        Path to the generated concat file
    """
    concat_content = []

    # Add episode segments with commercials
    for i, break_point in enumerate(break_points):
        # Add episode segment
        concat_content.append(f"file '{episode_path}'")

        # Add commercial if available
        if i < len(commercial_paths):
            concat_content.append(f"file '{commercial_paths[i]}'")

    # Write concat file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('\n'.join(concat_content))
        return f.name
```

## Error Handling

The system includes comprehensive error handling:

- **FFmpeg stderr monitoring**: Captures and logs FFmpeg errors
- **Process restart**: Automatically restarts FFmpeg if it crashes
- **Chunk debugging**: Logs first few chunks for debugging
- **Path validation**: Ensures input files exist before streaming

## Performance Considerations

- **Memory usage**: Concat files are temporary and cleaned up automatically
- **CPU usage**: Uses `-preset veryfast` for real-time encoding
- **Latency**: Optimized for low-latency streaming with `-muxdelay 0`
- **Bandwidth**: Configurable audio/video bitrates for different quality levels

## Future Enhancements

1. **Dynamic Commercial Insertion**: Real-time concat file updates
2. **A/B Testing**: Multiple commercial variants
3. **Analytics Integration**: Track commercial playback metrics
4. **Quality Adaptation**: Dynamic bitrate adjustment based on network conditions

## Usage Examples

### Basic Usage (Single File)

```python
from retrovue.streaming.mpegts_stream import MPEGTSStreamer

# Create streamer for single file
streamer = MPEGTSStreamer("R:/Media/TV/Episode.mp4", "channel1")

# Start streaming
for chunk in streamer.start_stream():
    # Send chunk to client
    yield chunk
```

### Commercial Insertion Example

```python
# Step 1: Segment the episode
streamer = MPEGTSStreamer("R:/Media/TV/Episode.mp4", "channel1")
break_points = [300.0, 600.0, 900.0]  # 5, 10, 15 minutes
segment_paths = streamer.segment_episode("R:/Media/TV/Episode.mp4", break_points)

# Step 2: Prepare commercials
commercial_paths = [
    "R:/Media/Commercials/ad1.mp4",
    "R:/Media/Commercials/ad2.mp4",
    "R:/Media/Commercials/ad3.mp4"
]

# Step 3: Create concat file with segments and commercials
concat_file = streamer.create_segmented_concat_file(
    "R:/Media/TV/Episode.mp4",
    commercial_paths,
    break_points
)

# Step 4: Update streamer to use concat file
streamer.source_path = concat_file

# Step 5: Start streaming with commercials
for chunk in streamer.start_stream():
    yield chunk
```

### Advanced: Dynamic Commercial Insertion

```python
class CommercialStreamer:
    def __init__(self, episode_path: str, channel_id: str):
        self.episode_path = episode_path
        self.channel_id = channel_id
        self.streamer = MPEGTSStreamer(episode_path, channel_id)
        self.current_concat_file = None

    def update_commercials(self, commercial_paths: list[str], break_points: list[float]):
        '''Dynamically update commercials during playback'''
        # Create new concat file
        new_concat_file = self.streamer.create_segmented_concat_file(
            self.episode_path,
            commercial_paths,
            break_points
        )

        # Update streamer source
        self.streamer.source_path = new_concat_file
        self.current_concat_file = new_concat_file

    def start_stream(self):
        '''Start streaming with current commercial configuration'''
        return self.streamer.start_stream()
```

### Integration with Web Server

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/iptv/channel/{channel_id}.ts")
async def stream_with_commercials(channel_id: str):
    # Get commercial configuration for this channel
    commercial_config = get_commercial_config(channel_id)

    # Create streamer with commercials
    streamer = MPEGTSStreamer(
        commercial_config['episode_path'],
        channel_id
    )

    # Add commercials
    if commercial_config['commercials']:
        concat_file = streamer.create_segmented_concat_file(
            commercial_config['episode_path'],
            commercial_config['commercial_paths'],
            commercial_config['break_points']
        )
        streamer.source_path = concat_file

    def generate():
        for chunk in streamer.start_stream():
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="video/mp2t",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )
```

### Error Handling and Monitoring

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_stream_health(streamer: MPEGTSStreamer):
    '''Monitor stream health and restart if needed'''
    try:
        chunk_count = 0
        for chunk in streamer.start_stream():
            chunk_count += 1

            # Log progress every 100 chunks
            if chunk_count % 100 == 0:
                logger.info(f"Streamed {chunk_count} chunks")

            yield chunk

    except Exception as e:
        logger.error(f"Stream error: {e}")
        # Implement restart logic here
        raise
```

### Performance Optimization

```python
# For high-performance streaming, consider:

# 1. Pre-segment episodes during off-peak hours
def preprocess_episodes():
    episodes = get_all_episodes()
    for episode in episodes:
        break_points = analyze_natural_breaks(episode)
        segment_episode(episode, break_points)

# 2. Cache concat files for popular content
def get_cached_concat_file(episode_id: str, commercial_set: str):
    cache_key = f"{episode_id}_{commercial_set}"
    if cache_key in concat_cache:
        return concat_cache[cache_key]

    # Generate new concat file
    concat_file = create_concat_file(episode_id, commercial_set)
    concat_cache[cache_key] = concat_file
    return concat_file

# 3. Use multiple streamers for different quality levels
def create_quality_streamers(episode_path: str):
    return {
        '720p': MPEGTSStreamer(episode_path, 'channel_720p'),
        '1080p': MPEGTSStreamer(episode_path, 'channel_1080p'),
        '4k': MPEGTSStreamer(episode_path, 'channel_4k')
    }
```

## API Reference

### MPEGTSStreamer Class

#### `__init__(source_path: str, channel_id: str)`

Initialize the MPEG-TS streamer.

**Parameters:**

- `source_path`: Path to the source video file
- `channel_id`: Channel identifier for this stream

#### `start_stream() -> Generator[bytes, None, None]`

Start the MPEG-TS stream and yield video data.

**Returns:**

- `Generator[bytes, None, None]`: MPEG-TS video data chunks

#### `stop_stream() -> None`

Stop the MPEG-TS stream safely.

#### `create_segmented_concat_file(episode_path: str, commercial_paths: list[str], break_points: list[float]) -> str`

Create a concat file with episode segments and commercial breaks.

**Parameters:**

- `episode_path`: Path to the main episode file
- `commercial_paths`: List of commercial file paths to insert
- `break_points`: List of timestamps (in seconds) where breaks should occur

**Returns:**

- `str`: Path to the generated concat file

#### `segment_episode(episode_path: str, break_points: list[float]) -> list[str]`

Segment an episode into multiple files at specified break points.

**Parameters:**

- `episode_path`: Path to the episode file to segment
- `break_points`: List of timestamps where to create breaks

**Returns:**

- `list[str]`: List of paths to the created segment files
