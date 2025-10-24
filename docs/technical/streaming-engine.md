# 🎛️ Streaming Engine

## 🎬 Core Technology

### **FFmpeg-Based MPEG-TS Streaming**

Retrovue uses FFmpeg as the core technology for video processing, encoding, and MPEG-TS stream generation. This provides:

- **Industry Standard**: FFmpeg is the de facto standard for video processing
- **Format Support**: Handles virtually any input video format
- **MPEG-TS Output**: Generates industry-standard MPEG Transport Streams
- **Real-time Processing**: Can process and stream content in real-time

### **MPEG-TS (Transport Stream)**

- **Continuous Stream**: Single continuous MPEG-TS stream for IPTV playback
- **Compatibility**: Works with VLC, Plex Live TV, smart TVs, and IPTV clients
- **Low Latency**: Direct streaming without segment generation
- **Reliability**: Robust streaming protocol with automatic recovery

## 🏗️ Streaming Pipeline Architecture

### **Current Pipeline**

```
Media Files → FFmpeg Concat → MPEG-TS Stream → HTTP Server → IPTV Clients
     ↑              ↑              ↑              ↑            ↑
  Database    Concat Demuxer   Transport Stream   FastAPI    VLC/Plex
```

### **Multi-Channel Pipeline (Future)**

```
Content Library → Channel Manager → FFmpeg Process → MPEG-TS Stream → Network
       ↑              ↑                ↑              ↑           ↑
   Schedules      Channel State    Video Processing   Streams   Clients
```

## 🔧 FFmpeg Configuration

### **Key FFmpeg Parameters**

```bash
# Basic MPEG-TS streaming command
ffmpeg -f concat -safe 0 -i concat.txt \
  -map 0:v:0 -map 0:a:0? \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -c:a aac -b:a 128k \
  -f mpegts -mpegts_flags +initial_discontinuity+resend_headers \
  pipe:1
```

### **Critical Parameters Explained**

#### **`-f concat -safe 0`**

- **Purpose**: Uses FFmpeg's concat demuxer for seamless file concatenation
- **Benefit**: Enables commercial insertion and content transitions
- **Use Case**: IPTV streaming with interstitial content

#### **`-map 0:v:0 -map 0:a:0?`**

- **Purpose**: Maps video stream and optional audio stream
- **Benefit**: Handles content with or without audio gracefully
- **Flexibility**: `?` makes audio optional, preventing stream failures

#### **`-c:v libx264 -preset veryfast -tune zerolatency`**

- **Purpose**: H.264 encoding optimized for live streaming
- **Benefit**: Low latency encoding suitable for real-time streaming
- **Performance**: Veryfast preset balances quality and speed

#### **`-f mpegts -mpegts_flags +initial_discontinuity+resend_headers`**

- **Purpose**: Outputs MPEG-TS format with proper flags
- **Benefit**: Ensures proper stream initialization and header handling
- **Compatibility**: Works with IPTV clients and set-top boxes

## 🎯 Streaming Modes

### **Transcode Mode** ✅ **IMPLEMENTED**

```bash
# Re-encode content for consistent output
ffmpeg -f concat -i concat.txt -c:v libx264 -c:a aac -f mpegts pipe:1
```

- **Use Case**: Content with varying codecs and quality
- **Features**: Consistent H.264/AAC output, quality control
- **Performance**: Higher CPU usage, better compatibility

### **Copy Mode** ✅ **IMPLEMENTED**

```bash
# Pass-through content without re-encoding
ffmpeg -f concat -i concat.txt -c:v copy -c:a copy -f mpegts pipe:1
```

- **Use Case**: Content already in compatible formats
- **Features**: Minimal CPU usage, preserves original quality
- **Performance**: Low CPU usage, requires compatible input

### **Multi-Channel Mode** 🔄 **PLANNED**

```bash
# Multiple simultaneous channels
python -m retrovue.cli.main play-channel --channels 3 --port 8080
```

- **Use Case**: Full broadcast TV simulation
- **Features**: Multiple channels, scheduling, emergency overrides
- **Benefits**: Professional broadcast TV experience

## 🎛️ Streaming Engine Components

### **MPEGTSStreamer Class**

```python
class MPEGTSStreamer:
    """Async MPEG-TS streamer for continuous IPTV-style streaming."""

    async def stream(self) -> AsyncIterator[bytes]:
        """Start the MPEG-TS stream and yield video data asynchronously."""
        # Yields 1316-byte chunks (7×188 bytes) for proper TS packet alignment
```

### **FFmpeg Command Builder**

```python
def build_cmd(concat_path: str, mode: str = "transcode") -> list[str]:
    """Build FFmpeg command for MPEG-TS live streaming using concat demuxer."""
    # Returns optimized FFmpeg command for streaming
```

### **Web Server Integration**

```python
@app.get("/iptv/channel/{channel_id}.ts")
async def stream_channel(channel_id: str):
    """Streams a continuous MPEG-TS feed for the requested channel."""
    # Returns StreamingResponse with MPEG-TS data
```

## 🎬 Content Processing

### **Concat File Format**

```
file '/path/to/video1.mp4'
file '/path/to/video2.mp4'
file '/path/to/commercial.mp4'
```

### **Commercial Insertion**

- **Seamless Transitions**: FFmpeg concat demuxer handles smooth transitions
- **Content Mixing**: Combine shows, commercials, and interstitials
- **Timing Control**: Precise control over content timing and placement

### **Input Validation**

```python
def validate_input_files(concat_path: str) -> dict[str, any]:
    """Validate input files for FFmpeg streaming."""
    # Checks file existence, accessibility, and format compatibility
```

## 🌐 Network Streaming

### **HTTP Server**

- **FastAPI**: Modern async web framework for streaming
- **StreamingResponse**: Efficient streaming of MPEG-TS data
- **Headers**: Proper cache control and content type headers

### **Client Compatibility**

- **VLC Media Player**: Direct network stream playback
- **Plex Live TV**: Native integration with Plex
- **Smart TVs**: Works with any IPTV-capable device
- **Mobile Apps**: Stream to phones and tablets
- **Set-top Boxes**: Compatible with IPTV set-top boxes

### **Testing the Stream**

1. **Start the streaming server**:

   ```bash
   python -m retrovue.cli.main play "Cheers" --season 1 --episode 1
   ```

2. **Open VLC Media Player**
3. **Go to**: Media → Open Network Stream
4. **Enter**: `http://localhost:8000/iptv/channel/1.ts`
5. **Click Play**

The stream will play continuously with proper MPEG-TS formatting.

## 🎛️ CLI Interface

### **Play Command**

```bash
# Play specific episode
python -m retrovue.cli.main play "Cheers" --season 1 --episode 1

# Play with custom port
python -m retrovue.cli.main play "Cheers" --season 1 --episode 1 --port 8080

# Play with transcoding
python -m retrovue.cli.main play "Cheers" --season 1 --episode 1 --transcode

# Play with debug mode
python -m retrovue.cli.main play "Cheers" --season 1 --episode 1 --debug
```

### **Channel Command**

```bash
# Start channel stream
python -m retrovue.cli.main play-channel 1 --port 8000

# Kill existing processes
python -m retrovue.cli.main play-channel 1 --kill-existing
```

## 🔧 Configuration Options

### **Command Line Options**

```bash
# Basic options
python -m retrovue.cli.main play "Series" --season 1 --episode 1 --port 8000

# Advanced options
python -m retrovue.cli.main play "Series" --season 1 --episode 1 --transcode --debug

# Channel options
python -m retrovue.cli.main play-channel 1 --port 8000 --kill-existing
```

### **FFmpeg Parameters**

- **Video Preset**: `veryfast`, `fast`, `medium`, `slow`
- **GOP Size**: Group of Pictures size for video encoding
- **Audio Bitrate**: Audio bitrate (e.g., "128k", "256k")
- **Audio Channels**: Stereo or mono audio output

## 🎯 Future Enhancements

### **Advanced Features**

- **Multi-Channel Support**: Multiple simultaneous channels
- **Scheduling System**: Automated content scheduling
- **Commercial Management**: Advanced commercial insertion
- **EPG Support**: Electronic Program Guide integration

### **Professional Features**

- **Graphics Overlays**: Station logos and branding
- **Audio Processing**: Audio enhancement and mixing
- **Color Correction**: Professional color grading
- **Multi-Camera**: Support for multiple camera angles

### **Integration Features**

- **Plex Live TV**: Native Plex channel integration
- **XMLTV Guide**: Standard EPG format support
- **Remote Control**: Web-based remote control interface
- **API Access**: REST API for external control and monitoring

## 🚨 Troubleshooting

### **Common Issues**

#### **Stream Not Playing**

- Verify FFmpeg is installed and in PATH
- Check input file accessibility
- Ensure port is not blocked by firewall
- Try different VLC version or IPTV client

#### **Audio Issues**

- Check if source has audio track
- Verify audio codec compatibility
- Try transcoding mode for audio re-encoding

#### **Performance Issues**

- Use copy mode for compatible content
- Adjust video preset for CPU usage
- Monitor system resources during streaming

### **Debug Mode**

```bash
# Enable debug mode for verbose logging
python -m retrovue.cli.main play "Series" --season 1 --episode 1 --debug
```

Debug mode provides:

- Verbose FFmpeg logging
- Input file validation
- Stream analysis and diagnostics
- Performance monitoring

---

_This streaming engine provides robust MPEG-TS streaming capabilities optimized for IPTV-style content delivery with commercial insertion support._
