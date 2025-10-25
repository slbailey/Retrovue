# Retrovue Playout System

This document describes the MPEG-TS output contract for Retrovue's playout system, including technical specifications, testing procedures, and implementation details.

## Overview

Retrovue generates MPEG-TS transport streams for broadcast-style TV channels. The system is designed to provide:

- **As-run alignment** via precise timing synchronization
- **Seamless transitions** between content and commercials
- **Industry-standard compatibility** with IPTV clients, smart TVs, and mobile devices
- **Real-time scheduling** with dynamic stream updates

## MPEG-TS Configuration

### Target FFmpeg Flags

The playout system uses the following FFmpeg flags for MPEG-TS generation:

```bash
-f mpegts                # MPEG-TS format output
-mpegts_flags +initial_discontinuity  # Handle content transitions
-muxpreload 0            # Low latency muxing
-muxdelay 0              # Minimal delay
```

### Key MPEG-TS Parameters

| Parameter               | Value              | Purpose                                   |
| ----------------------- | ------------------ | ----------------------------------------- |
| `-f mpegts`             | MPEG-TS format     | Standard transport stream output          |
| `initial_discontinuity` | Handle transitions | Proper handling of content changes        |
| `muxpreload 0`          | Low latency        | Minimal buffering for real-time streaming |
| `muxdelay 0`            | Minimal delay      | Immediate output for live streaming       |

## As-Run Alignment

### Timing Synchronization

The system enables as-run alignment by maintaining precise timing synchronization in MPEG-TS streams:

```
MPEG-TS Stream with precise timing:
- Content starts at 2024-01-15T14:30:00.000Z
- Seamless transitions between content pieces
- Continuous transport stream output
```

This allows clients to:

- **Synchronize playback** across multiple devices
- **Resume from exact timestamps** after interruption
- **Align with broadcast schedules** for live TV integration

### Marker Integration

Retrovue's Marker system maps to MPEG-TS content as follows:

#### Bumpers and Commercials

```python
# Marker types that affect MPEG-TS generation
Marker(kind="bumper")     # Station identification, transitions
Marker(kind="avail")      # Commercial breaks, ad slots
Marker(kind="intro")      # Show introductions
Marker(kind="outro")      # Show conclusions
```

#### Timeline Alignment

```
Content Timeline:
[Show Start] -> [Intro Marker] -> [Content] -> [Avail Marker] -> [Commercial] -> [Content] -> [Outro Marker] -> [Show End]

MPEG-TS Stream:
- Show start: 2024-01-15T14:30:00.000Z
- Intro content with seamless transition
- Main content with precise timing
- Commercial break at 2024-01-15T14:32:00.000Z
- Continuous transport stream output
```

## Channel Architecture

### Multi-Channel Support

Each channel generates its own MPEG-TS stream:

```
/channel/1/stream.ts         # Channel 1 transport stream
/channel/1/stream.ts         # Continuous MPEG-TS output

/channel/2/stream.ts         # Channel 2 transport stream
/channel/2/stream.ts         # Continuous MPEG-TS output
```

### Stream Structure

```
MPEG-TS Transport Stream:
- Continuous transport stream output
- Precise timing synchronization
- Seamless content transitions
- Real-time stream generation
```

## Testing Procedures

### VLC Test Recipe

1. **Start Retrovue server:**

   ```bash
   python run_server.py
   ```

2. **Open VLC Media Player:**

   - Go to: Media → Open Network Stream
   - Enter: `http://localhost:8080/channel/1/stream.ts`
   - Click Play

3. **Verify playback:**
   - ✅ Stream starts immediately
   - ✅ Transport stream loads continuously
   - ✅ No buffering or stuttering
   - ✅ Timeline shows correct duration

### FFmpeg Test Stub

```bash
# Test MPEG-TS generation with sample content
ffmpeg -i sample_video.mp4 \
  -f mpegts \
  -mpegts_flags +initial_discontinuity \
  -muxpreload 0 \
  -muxdelay 0 \
  stream.ts

# Verify stream structure
ffprobe stream.ts
```

### Automated Testing

```python
# test_mpegts_generation.py
import requests
import time

def test_mpegts_stream():
    """Test MPEG-TS stream generation and accessibility."""
    base_url = "http://localhost:8080"
    channel_id = 1

    # Test stream accessibility
    stream_url = f"{base_url}/channel/{channel_id}/stream.ts"
    response = requests.get(stream_url, stream=True)

    assert response.status_code == 200
    assert response.headers['content-type'] == 'video/mp2t'

    # Test stream content
    chunk = next(response.iter_content(chunk_size=1024))
    assert len(chunk) > 0

if __name__ == "__main__":
    test_mpegts_stream()
    print("✅ MPEG-TS tests passed")
```

## Implementation Details

### FFmpeg Command Generation

```python
def generate_ffmpeg_command(input_file: str, output_dir: str, channel_id: int) -> str:
    """Generate FFmpeg command for MPEG-TS output."""
    return f"""
    ffmpeg -i "{input_file}" \
      -f mpegts \
      -mpegts_flags +initial_discontinuity \
      -muxpreload 0 \
      -muxdelay 0 \
      "{output_dir}/channel_{channel_id}/stream.ts"
    """
```

### Stream Management

```python
class MPEGTSStreamManager:
    """Manages MPEG-TS stream lifecycle and output."""

    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.stream_active = False
        self.current_content = None

    def start_stream(self, content_path: str, timestamp: datetime):
        """Start MPEG-TS stream for content."""
        self.current_content = {
            'path': content_path,
            'timestamp': timestamp
        }
        self.stream_active = True

    def stop_stream(self):
        """Stop MPEG-TS stream."""
        self.stream_active = False
        self.current_content = None

    def get_stream_status(self) -> dict:
        """Get current stream status."""
        return {
            'active': self.stream_active,
            'content': self.current_content,
            'channel_id': self.channel_id
        }
```

## Performance Considerations

### Stream Optimization

- **Continuous output**: Real-time MPEG-TS stream generation
- **Low latency**: Minimal buffering for live streaming
- **Efficient encoding**: Optimized for real-time performance

### Network Efficiency

- **HTTP streaming**: Direct MPEG-TS stream delivery
- **Real-time output**: Continuous transport stream
- **Compression**: H.264 video with AAC audio for broad compatibility

## Integration Points

### Plex Live TV

```xml
<!-- Plex Live TV channel configuration -->
<Channel>
  <Name>Retrovue Channel 1</Name>
  <URL>http://retrovue-server:8080/channel/1/stream.ts</URL>
  <Protocol>mpegts</Protocol>
  <Quality>HD</Quality>
</Channel>
```

### Smart TV Apps

- **Samsung Tizen**: Native MPEG-TS support
- **LG webOS**: MPEG-TS compatibility
- **Roku**: Direct MPEG-TS playback
- **Apple TV**: Native MPEG-TS support

## Monitoring and Debugging

### Log Analysis

```bash
# Monitor MPEG-TS generation
tail -f /var/log/retrovue/playout.log | grep "mpegts_stream"

# Check stream generation rate
grep "stream_created" /var/log/retrovue/playout.log | wc -l
```

### Health Checks

```python
def check_mpegts_health(channel_id: int) -> dict:
    """Check MPEG-TS channel health."""
    stream_url = f"http://localhost:8080/channel/{channel_id}/stream.ts"

    try:
        response = requests.get(stream_url, timeout=5, stream=True)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "stream_accessible": True,
                "content_type": response.headers.get('content-type', 'unknown')
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "stream_accessible": False
        }
```

## Future Enhancements

### Advanced Features

- **Adaptive bitrate**: Multiple quality streams
- **DRM integration**: Content protection
- **Analytics**: Viewership tracking
- **CDN integration**: Global content delivery

### Scalability

- **Horizontal scaling**: Multiple playout servers
- **Load balancing**: Distribute channel load
- **Edge caching**: Reduce origin server load
- **Auto-scaling**: Dynamic resource allocation

---

_This document serves as the technical specification for Retrovue's MPEG-TS playout system. For implementation details, see the source code in `src/retrovue/core/streaming.py`._
