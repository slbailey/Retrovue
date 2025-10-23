# Retrovue Playout System

This document describes the HLS-first output contract for Retrovue's playout system, including technical specifications, testing procedures, and implementation details.

## Overview

Retrovue generates HLS (HTTP Live Streaming) playlists for broadcast-style TV channels. The system is designed to provide:

- **As-run alignment** via PROGRAM-DATE-TIME headers
- **Seamless transitions** between content and commercials
- **Industry-standard compatibility** with Plex Live TV, smart TVs, and mobile devices
- **Real-time scheduling** with dynamic playlist updates

## HLS Configuration

### Target FFmpeg Flags

The playout system uses the following FFmpeg flags for HLS generation:

```bash
-f hls                    # HLS format output
-hls_time 2              # 2-second segments
-hls_list_size 5         # Keep 5 segments in playlist
-hls_flags delete_segments+program_date_time  # Auto-delete old segments + include program timestamps
```

### Key HLS Parameters

| Parameter           | Value       | Purpose                                       |
| ------------------- | ----------- | --------------------------------------------- |
| `-f hls`            | HLS format  | Standard HTTP Live Streaming output           |
| `-hls_time 2`       | 2 seconds   | Segment duration for responsive seeking       |
| `-hls_list_size 5`  | 5 segments  | Playlist window size (10 seconds total)       |
| `delete_segments`   | Auto-delete | Remove old segments to save disk space        |
| `program_date_time` | Timestamps  | Enable PROGRAM-DATE-TIME for as-run alignment |

## As-Run Alignment

### PROGRAM-DATE-TIME Headers

The `program_date_time` flag enables as-run alignment by including absolute timestamps in HLS segments:

```
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:00.000Z
#EXTINF:2.000,
segment_001.ts
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:02.000Z
#EXTINF:2.000,
segment_002.ts
```

This allows clients to:

- **Synchronize playback** across multiple devices
- **Resume from exact timestamps** after interruption
- **Align with broadcast schedules** for live TV integration

### Marker Integration

Retrovue's Marker system maps to HLS segments as follows:

#### Bumpers and Commercials

```python
# Marker types that affect HLS generation
Marker(kind="bumper")     # Station identification, transitions
Marker(kind="avail")      # Commercial breaks, ad slots
Marker(kind="intro")      # Show introductions
Marker(kind="outro")      # Show conclusions
```

#### Timeline Alignment

```
Content Timeline:
[Show Start] -> [Intro Marker] -> [Content] -> [Avail Marker] -> [Commercial] -> [Content] -> [Outro Marker] -> [Show End]

HLS Playlist:
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:00.000Z  # Show start
#EXTINF:2.000,
show_intro.ts
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:02.000Z  # Content begins
#EXTINF:2.000,
show_content_001.ts
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:32:00.000Z  # Commercial break
#EXTINF:2.000,
commercial_001.ts
```

## Channel Architecture

### Multi-Channel Support

Each channel generates its own HLS playlist:

```
/channel/1/playlist.m3u8    # Channel 1 playlist
/channel/1/segment_001.ts   # Channel 1 segments
/channel/1/segment_002.ts

/channel/2/playlist.m3u8    # Channel 2 playlist
/channel/2/segment_001.ts   # Channel 2 segments
/channel/2/segment_002.ts
```

### Playlist Structure

```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:2
#EXT-X-MEDIA-SEQUENCE:12345
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:00.000Z
#EXTINF:2.000,
segment_001.ts
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:02.000Z
#EXTINF:2.000,
segment_002.ts
#EXT-X-PROGRAM-DATE-TIME:2024-01-15T14:30:04.000Z
#EXTINF:2.000,
segment_003.ts
```

## Testing Procedures

### VLC Test Recipe

1. **Start Retrovue server:**

   ```bash
   python run_server.py
   ```

2. **Open VLC Media Player:**

   - Go to: Media → Open Network Stream
   - Enter: `http://localhost:8080/channel/1/playlist.m3u8`
   - Click Play

3. **Verify playback:**
   - ✅ Stream starts immediately
   - ✅ Segments load continuously
   - ✅ No buffering or stuttering
   - ✅ Timeline shows correct duration

### FFmpeg Test Stub

```bash
# Test HLS generation with sample content
ffmpeg -i sample_video.mp4 \
  -f hls \
  -hls_time 2 \
  -hls_list_size 5 \
  -hls_flags delete_segments+program_date_time \
  -hls_segment_filename "segment_%03d.ts" \
  playlist.m3u8

# Verify playlist structure
cat playlist.m3u8
```

### Automated Testing

```python
# test_hls_generation.py
import requests
import time

def test_hls_playlist():
    """Test HLS playlist generation and accessibility."""
    base_url = "http://localhost:8080"
    channel_id = 1

    # Test playlist accessibility
    playlist_url = f"{base_url}/channel/{channel_id}/playlist.m3u8"
    response = requests.get(playlist_url)

    assert response.status_code == 200
    assert "EXTM3U" in response.text
    assert "EXT-X-VERSION" in response.text
    assert "EXT-X-PROGRAM-DATE-TIME" in response.text

    # Test segment accessibility
    playlist_content = response.text
    segment_lines = [line for line in playlist_content.split('\n') if line.endswith('.ts')]

    for segment in segment_lines[:3]:  # Test first 3 segments
        segment_url = f"{base_url}/channel/{channel_id}/{segment}"
        seg_response = requests.get(segment_url)
        assert seg_response.status_code == 200
        assert len(seg_response.content) > 0

if __name__ == "__main__":
    test_hls_playlist()
    print("✅ HLS tests passed")
```

## Implementation Details

### FFmpeg Command Generation

```python
def generate_ffmpeg_command(input_file: str, output_dir: str, channel_id: int) -> str:
    """Generate FFmpeg command for HLS output."""
    return f"""
    ffmpeg -i "{input_file}" \
      -f hls \
      -hls_time 2 \
      -hls_list_size 5 \
      -hls_flags delete_segments+program_date_time \
      -hls_segment_filename "{output_dir}/channel_{channel_id}/segment_%03d.ts" \
      -hls_playlist_type event \
      -hls_allow_cache 0 \
      "{output_dir}/channel_{channel_id}/playlist.m3u8"
    """
```

### Segment Management

```python
class HLSSegmentManager:
    """Manages HLS segment lifecycle and cleanup."""

    def __init__(self, channel_id: int, segment_duration: int = 2):
        self.channel_id = channel_id
        self.segment_duration = segment_duration
        self.segments = []
        self.max_segments = 5

    def add_segment(self, segment_path: str, timestamp: datetime):
        """Add new segment to playlist."""
        self.segments.append({
            'path': segment_path,
            'timestamp': timestamp,
            'duration': self.segment_duration
        })

        # Maintain sliding window
        if len(self.segments) > self.max_segments:
            old_segment = self.segments.pop(0)
            self._cleanup_segment(old_segment['path'])

    def generate_playlist(self) -> str:
        """Generate M3U8 playlist content."""
        playlist = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{self.segment_duration}",
            f"#EXT-X-MEDIA-SEQUENCE:{len(self.segments)}"
        ]

        for segment in self.segments:
            playlist.append(f"#EXT-X-PROGRAM-DATE-TIME:{segment['timestamp'].isoformat()}Z")
            playlist.append(f"#EXTINF:{segment['duration']:.3f},")
            playlist.append(segment['path'])

        return "\n".join(playlist)
```

## Performance Considerations

### Segment Size Optimization

- **2-second segments**: Balance between responsiveness and overhead
- **5-segment window**: 10 seconds of content always available
- **Auto-deletion**: Prevents disk space accumulation

### Network Efficiency

- **HTTP caching**: Segments can be cached by CDNs
- **Range requests**: Support for partial content delivery
- **Compression**: H.264 video with AAC audio for broad compatibility

## Integration Points

### Plex Live TV

```xml
<!-- Plex Live TV channel configuration -->
<Channel>
  <Name>Retrovue Channel 1</Name>
  <URL>http://retrovue-server:8080/channel/1/playlist.m3u8</URL>
  <Protocol>hls</Protocol>
  <Quality>HD</Quality>
</Channel>
```

### Smart TV Apps

- **Samsung Tizen**: Native HLS support
- **LG webOS**: HLS.js compatibility
- **Roku**: Direct HLS playback
- **Apple TV**: Native HLS support

## Monitoring and Debugging

### Log Analysis

```bash
# Monitor HLS generation
tail -f /var/log/retrovue/playout.log | grep "hls_segment"

# Check segment generation rate
grep "segment_created" /var/log/retrovue/playout.log | wc -l
```

### Health Checks

```python
def check_hls_health(channel_id: int) -> dict:
    """Check HLS channel health."""
    playlist_url = f"http://localhost:8080/channel/{channel_id}/playlist.m3u8"

    try:
        response = requests.get(playlist_url, timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "playlist_accessible": True,
                "segment_count": len([line for line in response.text.split('\n') if line.endswith('.ts')])
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "playlist_accessible": False
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

_This document serves as the technical specification for Retrovue's HLS playout system. For implementation details, see the source code in `src/retrovue/core/streaming.py`._
