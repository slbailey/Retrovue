# 🎛️ Streaming Engine

## 🎬 Core Technology

### **FFmpeg-Based Streaming**
Retrovue uses FFmpeg as the core technology for video processing, encoding, and HLS segment generation. This provides:
- **Industry Standard**: FFmpeg is the de facto standard for video processing
- **Format Support**: Handles virtually any input video format
- **HLS Output**: Generates industry-standard HTTP Live Streaming segments
- **Real-time Processing**: Can process and stream content in real-time

### **HLS (HTTP Live Streaming)**
- **Segments**: `.ts` or `fmp4` files with rotating `master.m3u8`
- **Compatibility**: Works with VLC, Plex, smart TVs, and mobile devices
- **Scalability**: Supports multiple quality levels and adaptive bitrates
- **Reliability**: Robust streaming protocol with automatic recovery

## 🏗️ Streaming Pipeline Architecture

### **Basic Pipeline**
```
Media Files → FFmpeg → HLS Segments → HTTP Server → Client Players
     ↑           ↑           ↑            ↑            ↑
  Database   Encoding    .ts/.m4s     .m3u8        VLC/Plex
```

### **Advanced Pipeline (Multi-Channel)**
```
Program Director → Channel Manager → FFmpeg Process → HLS Stream → Network
       ↑               ↑                ↑              ↑           ↑
   Schedules      Channel State    Video Processing   Segments   Clients
```

## 🔧 FFmpeg Configuration

### **Key FFmpeg Parameters**
```bash
# Basic HLS streaming command
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -c:a aac \
  -hls_time 10 \
  -hls_list_size 6 \
  -hls_delete_threshold 1 \
  -hls_start_number_source epoch \
  -f hls \
  output.m3u8
```

### **Critical Parameters Explained**

#### **`-hls_delete_threshold 1`**
- **Purpose**: Prevents segments from being deleted too aggressively
- **Problem**: VLC fails if segments are deleted while playing
- **Solution**: Keep at least 1 segment in the playlist at all times

#### **`-hls_start_number_source epoch`**
- **Purpose**: Uses timestamp-based segment numbering
- **Problem**: Index reuse causes playback issues
- **Solution**: Each segment gets a unique timestamp-based number

#### **`-hls_time 10`**
- **Purpose**: Sets segment duration to 10 seconds
- **Benefit**: Good balance between latency and efficiency
- **Flexibility**: Can be adjusted based on content type

#### **`-hls_list_size 6`**
- **Purpose**: Keeps 6 segments in the playlist
- **Benefit**: Provides buffer for smooth playback
- **Optimization**: Reduces storage requirements

## 🎯 Streaming Modes

### **Phase 1: Simple Loop Mode** ✅ **IMPLEMENTED**
```bash
# Single channel with simple content looping
python main.py
```
- **Use Case**: Proof of concept and testing
- **Features**: Basic HLS streaming with content looping
- **Limitations**: Single channel, no scheduling, simple transitions

### **Phase 2: Concat Mode** ✅ **IMPLEMENTED**
```bash
# ErsatzTV-style concatenation mode
python main.py --mode concat
```
- **Use Case**: More sophisticated content playback
- **Features**: Better content transitions, improved timing
- **Limitations**: Still single channel, limited scheduling

### **Phase 3: Multi-Channel Mode** 🔄 **PLANNED**
```bash
# Multiple simultaneous channels
python main.py --channels 3 --port 8080
```
- **Use Case**: Full broadcast TV simulation
- **Features**: Multiple channels, scheduling, emergency overrides
- **Benefits**: Professional broadcast TV experience

## 🎬 Content Processing

### **Media Splitting During Playback**
Retrovue can split media during playback using several approaches:

#### **Option 1: FFmpeg Real-Time Splitting**
```bash
# Split stream at specific timestamps
ffmpeg -i input.mp4 -ss 00:02:15 -t 00:09:25 -c copy segment1.ts
```
- **Benefits**: No file modification, real-time processing, multiple output formats
- **Use Case**: Live streaming with commercial insertion
- **Performance**: Moderate CPU usage, flexible timing

#### **Option 2: Pre-Generated Segments**
```bash
# Generate segments during off-peak hours
ffmpeg -i input.mp4 -ss 00:02:15 -t 00:09:25 -c:v libx264 -c:a aac segment1.ts
```
- **Benefits**: Faster playback, reduced server load, better quality control
- **Use Case**: Scheduled programming with known commercial breaks
- **Performance**: High CPU usage during generation, low during playback

#### **Option 3: Dynamic Playlist Generation**
```bash
# Generate .m3u8 playlists that skip commercial segments
# Uses database chapter markers to determine segment boundaries
```
- **Benefits**: Standard HLS compatibility, flexible commercial insertion
- **Use Case**: IPTV streaming with commercial management
- **Performance**: Low CPU usage, high flexibility

### **Chapter Marker Integration**
```sql
-- Chapter markers linked to media files
chapter_markers (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    chapter_title TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL,     -- Timestamp in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
)
```

## 🌐 Network Streaming

### **HTTP Server**
- **Lightweight**: Python-based HTTP server for HLS delivery
- **Efficient**: Serves static files with proper MIME types
- **Scalable**: Can handle multiple concurrent streams
- **Compatible**: Works with all HLS-compatible clients

### **Client Compatibility**
- **VLC Media Player**: Direct network stream playback
- **Plex Live TV**: Native integration with Plex
- **Smart TVs**: Works with any IPTV-capable device
- **Mobile Apps**: Stream to phones and tablets
- **Web Browsers**: HTML5 video with HLS.js

### **Testing the Stream**
1. **Start the streaming server**:
   ```bash
   python main.py
   ```

2. **Open VLC Media Player**
3. **Go to**: Media → Open Network Stream
4. **Enter**: `http://localhost:8080/channel/1.ts`
5. **Click Play**

The stream will loop seamlessly forever with proper timestamp handling.

## 🎛️ Program Director Architecture

### **Channel Management**
```python
class Channel:
    def __init__(self, channel_id, name):
        self.channel_id = channel_id
        self.name = name
        self.schedule_manager = ScheduleManager()
        self.pipeline_manager = PipelineManager()
        self.graphics_manager = GraphicsManager()
        self.playback_pipeline = PlaybackPipeline()
```

### **Schedule Manager**
- **Coarse Scheduling**: Show-level scheduling (what plays when)
- **Fine Scheduling**: Break-level scheduling (commercial timing)
- **Timeline Management**: Drag-and-drop interface for schedule creation
- **Conflict Resolution**: Handles scheduling conflicts and overlaps

### **Pipeline Manager**
- **Playback Control**: Manages video playback and transitions
- **Timing Management**: Ensures proper timing and synchronization
- **Quality Control**: Monitors stream quality and performance
- **Error Handling**: Manages playback errors and recovery

### **Graphics Manager**
- **Bug Overlays**: Station logos and branding
- **Lower Thirds**: Show titles and information
- **Emergency Graphics**: Alert overlays and emergency information
- **Branding**: Consistent visual identity across channels

## 🚨 Emergency System

### **Priority Alert Injection**
```python
class EmergencySystem:
    def inject_alert(self, message, priority, channels):
        # Break into programming on specified channels
        # Override current content with emergency message
        # Return to normal programming after alert period
```

### **Alert Types**
- **Weather Alerts**: Severe weather warnings
- **Emergency Broadcasts**: Public safety announcements
- **System Alerts**: Technical issues and maintenance
- **Custom Alerts**: User-defined emergency messages

### **Channel Override**
- **Priority Levels**: Higher priority overrides lower priority
- **Channel Selection**: Can target specific channels or all channels
- **Duration Control**: Set alert duration and return timing
- **Visual Overlay**: Emergency graphics and text overlays

## 📊 Performance Optimization

### **Streaming Performance**
- **CPU Usage**: Optimized FFmpeg parameters for efficiency
- **Memory Management**: Efficient buffer management
- **Network Bandwidth**: Adaptive bitrate streaming
- **Storage**: Efficient segment management and cleanup

### **Multi-Channel Scaling**
- **Process Isolation**: Each channel runs in its own process
- **Resource Management**: CPU and memory allocation per channel
- **Load Balancing**: Distribute processing across available resources
- **Monitoring**: Real-time performance monitoring and alerting

### **Quality Control**
- **Video Quality**: Consistent encoding parameters
- **Audio Sync**: Proper audio-video synchronization
- **Stream Stability**: Reliable streaming without dropouts
- **Error Recovery**: Automatic recovery from streaming errors

## 🔧 Configuration Options

### **Command Line Options**
```bash
# Basic options
python main.py --mode loop --port 8080 --loops 10

# Advanced options
python main.py --mode concat --channels 3 --port 8080 --quality high

# Custom configuration
python main.py --config custom_config.json
```

### **Configuration File**
```json
{
  "streaming": {
    "mode": "concat",
    "port": 8080,
    "channels": 3,
    "quality": "high",
    "segment_duration": 10,
    "playlist_size": 6
  },
  "ffmpeg": {
    "video_codec": "libx264",
    "audio_codec": "aac",
    "bitrate": "2000k",
    "resolution": "1920x1080"
  }
}
```

## 🎯 Future Enhancements

### **Advanced Features**
- **Adaptive Bitrate**: Multiple quality levels for different devices
- **Closed Captions**: Subtitle support and overlay
- **Multiple Audio Tracks**: Language selection and audio options
- **Live Events**: Support for live programming and events

### **Professional Features**
- **Graphics Overlays**: Advanced graphics and animation support
- **Audio Processing**: Audio enhancement and mixing
- **Color Correction**: Professional color grading
- **Multi-Camera**: Support for multiple camera angles

### **Integration Features**
- **Plex Live TV**: Native Plex channel integration
- **EPG Support**: Electronic Program Guide integration
- **Remote Control**: Web-based remote control interface
- **API Access**: REST API for external control and monitoring
