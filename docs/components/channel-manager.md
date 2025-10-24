# 📡 Channel Manager

The Channel Manager is responsible for creating, configuring, and managing IPTV channels. It serves as the orchestration layer that brings together programming schedules, streaming infrastructure, and channel-specific configurations to deliver live IPTV channels.

## 🎯 Business Purpose

The Channel Manager transforms programming schedules into live IPTV channels:

- **Channel Creation**: Create and configure IPTV channels
- **Stream Management**: Manage live streaming processes for each channel
- **Resource Allocation**: Allocate system resources across multiple channels
- **Channel Switching**: Enable dynamic content switching and channel management
- **Monitoring**: Monitor channel health and performance

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Channel Manager                         │
├─────────────────────────────────────────────────────────────┤
│  Channel Controller  │  Stream Manager  │  Resource Monitor │
├─────────────────────────────────────────────────────────────┤
│                    Channel Services                         │
├─────────────────────────────────────────────────────────────┤
│  ChannelService  │  StreamService  │  ResourceService     │
├─────────────────────────────────────────────────────────────┤
│                    Domain Entities                          │
├─────────────────────────────────────────────────────────────┤
│  Channel  │  Stream  │  Resource  │  Configuration       │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Integration               │
├─────────────────────────────────────────────────────────────┤
│  FFmpeg Processes  │  MPEG-TS Streams  │  Network Layer   │
└─────────────────────────────────────────────────────────────┘
```

### Data Model Relationships

```
Channel
├── Configuration
│   ├── Stream Settings
│   ├── Quality Settings
│   └── Network Settings
├── Active Schedule
│   ├── Current Program
│   ├── Upcoming Programs
│   └── Transition Rules
├── Stream Process
│   ├── FFmpeg Process
│   ├── Stream Health
│   └── Performance Metrics
└── Resource Allocation
    ├── CPU Allocation
    ├── Memory Allocation
    └── Network Bandwidth
```

## 🔧 Technical Implementation

### 1. Core Services

#### ChannelService

**Purpose**: Manages channel lifecycle and configuration

```python
class ChannelService:
    def __init__(self, db: Session):
        self.db = db
        self.stream_service = StreamService()
        self.resource_service = ResourceService()

    def create_channel(self, name: str, config: ChannelConfig) -> Channel:
        """Create a new IPTV channel."""
        # Validate configuration
        # Check resource availability
        # Create channel entity
        # Initialize stream process
        pass

    def start_channel(self, channel_id: UUID) -> bool:
        """Start streaming for a channel."""
        # Get channel configuration
        # Allocate resources
        # Start FFmpeg process
        # Begin streaming
        pass

    def stop_channel(self, channel_id: UUID) -> bool:
        """Stop streaming for a channel."""
        # Stop FFmpeg process
        # Release resources
        # Update channel status
        pass
```

**Key Methods:**

- `create_channel()`: Create new channel
- `start_channel()`: Start channel streaming
- `stop_channel()`: Stop channel streaming
- `update_channel_config()`: Update channel settings

#### StreamService

**Purpose**: Manages streaming processes and FFmpeg integration

```python
class StreamService:
    def __init__(self):
        self.active_streams = {}
        self.ffmpeg_manager = FFmpegManager()

    def create_stream(self, channel: Channel, config: StreamConfig) -> Stream:
        """Create streaming process for channel."""
        # Build FFmpeg command
        # Start FFmpeg process
        # Monitor stream health
        # Return stream object
        pass

    def monitor_stream(self, stream_id: UUID) -> StreamHealth:
        """Monitor stream health and performance."""
        # Check process status
        # Monitor stream quality
        # Check network connectivity
        # Return health status
        pass
```

**Key Methods:**

- `create_stream()`: Create streaming process
- `monitor_stream()`: Monitor stream health
- `restart_stream()`: Restart failed stream
- `get_stream_status()`: Get stream status

#### ResourceService

**Purpose**: Manages system resource allocation across channels

```python
class ResourceService:
    def __init__(self):
        self.resource_monitor = ResourceMonitor()
        self.allocation_manager = AllocationManager()

    def allocate_resources(self, channel: Channel, requirements: ResourceRequirements) -> bool:
        """Allocate system resources for channel."""
        # Check available resources
        # Allocate CPU, memory, bandwidth
        # Reserve resources
        # Return allocation status
        pass

    def release_resources(self, channel_id: UUID) -> bool:
        """Release resources for channel."""
        # Release allocated resources
        # Update resource availability
        # Notify other services
        pass
```

### 2. Domain Entities

#### Channel Entity

```python
class Channel(Base):
    """Represents an IPTV channel."""

    id: UUID = Primary key
    name: str = Channel name
    number: int = Channel number
    description: Optional[str] = Channel description
    status: ChannelStatus = STOPPED | STARTING | RUNNING | ERROR
    config: ChannelConfig = Channel configuration
    current_schedule_id: Optional[UUID] = Current active schedule
    created_at: datetime = When channel was created
    updated_at: datetime = Last modification time
```

#### Stream Entity

```python
class Stream(Base):
    """Represents an active streaming process."""

    id: UUID = Primary key
    channel_id: UUID = Foreign key to channel
    process_id: int = FFmpeg process ID
    status: StreamStatus = STARTING | RUNNING | STOPPING | ERROR
    start_time: datetime = When stream started
    end_time: Optional[datetime] = When stream ended
    health_metrics: dict = Stream health data
```

#### ChannelConfig Entity

```python
class ChannelConfig(Base):
    """Configuration for a channel."""

    id: UUID = Primary key
    channel_id: UUID = Foreign key to channel
    stream_settings: dict = Stream configuration
    quality_settings: dict = Quality settings
    network_settings: dict = Network configuration
    resource_limits: dict = Resource allocation limits
```

### 3. Streaming Infrastructure

#### FFmpeg Integration

```python
class FFmpegManager:
    """Manages FFmpeg processes for streaming."""

    def create_stream_command(self, channel: Channel, config: StreamConfig) -> str:
        """Build FFmpeg command for channel streaming."""
        cmd = [
            "ffmpeg",
            "-re",  # Real-time streaming
            "-i", "concat:input_list.txt",  # Input source
            "-c:v", config.video_codec,
            "-c:a", config.audio_codec,
            "-f", "mpegts",  # Output format
            "-muxrate", str(config.bitrate),
            "udp://239.0.0.1:1234"  # Output destination
        ]
        return " ".join(cmd)

    def start_stream_process(self, command: str) -> subprocess.Popen:
        """Start FFmpeg process for streaming."""
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
```

#### Stream Health Monitoring

```python
class StreamHealthMonitor:
    """Monitors stream health and performance."""

    def check_stream_health(self, stream: Stream) -> StreamHealth:
        """Check health of streaming process."""
        health = StreamHealth()

        # Check process status
        health.process_running = self.is_process_running(stream.process_id)

        # Check stream quality
        health.bitrate = self.get_current_bitrate(stream)
        health.frame_rate = self.get_frame_rate(stream)

        # Check for errors
        health.errors = self.get_recent_errors(stream)

        return health
```

## 🎮 User Interfaces

### 1. CLI Interface

#### Channel Management Commands

```bash
# Create new channel
retrovue channel create "Channel 1" --number 1 --quality 1080p

# Start channel
retrovue channel start <channel_id>

# Stop channel
retrovue channel stop <channel_id>

# List channels
retrovue channel list

# Get channel status
retrovue channel status <channel_id>
```

#### Stream Management Commands

```bash
# Monitor stream health
retrovue stream health <channel_id>

# Restart stream
retrovue stream restart <channel_id>

# Get stream metrics
retrovue stream metrics <channel_id>
```

#### Resource Management Commands

```bash
# Check resource usage
retrovue resources status

# Allocate resources
retrovue resources allocate <channel_id> --cpu 2 --memory 4g

# Release resources
retrovue resources release <channel_id>
```

### 2. Web Interface

#### Channel Dashboard

- **URL**: `/channels`
- **Features**:
  - Channel status overview
  - Real-time health monitoring
  - Resource usage display
  - Channel configuration

#### Stream Monitor

- **URL**: `/streams`
- **Features**:
  - Live stream monitoring
  - Health metrics display
  - Error log viewing
  - Performance analytics

#### Resource Manager

- **URL**: `/resources`
- **Features**:
  - System resource overview
  - Allocation management
  - Performance monitoring
  - Capacity planning

### 3. API Endpoints

#### Channel Endpoints

```python
# Create channel
POST /api/channels
# Get channel details
GET /api/channels/{channel_id}
# Start channel
POST /api/channels/{channel_id}/start
# Stop channel
POST /api/channels/{channel_id}/stop
# Update channel config
PUT /api/channels/{channel_id}/config
```

#### Stream Endpoints

```python
# Get stream status
GET /api/streams/{channel_id}/status
# Get stream health
GET /api/streams/{channel_id}/health
# Restart stream
POST /api/streams/{channel_id}/restart
# Get stream metrics
GET /api/streams/{channel_id}/metrics
```

#### Resource Endpoints

```python
# Get resource status
GET /api/resources/status
# Allocate resources
POST /api/resources/allocate
# Release resources
POST /api/resources/release
```

## 📡 Multi-Channel Management

### Channel Orchestration

#### Channel Controller

```python
class ChannelController:
    """Orchestrates multiple channels and manages resources."""

    def __init__(self):
        self.channels = {}
        self.resource_manager = ResourceManager()
        self.schedule_manager = ScheduleManager()

    def start_all_channels(self):
        """Start all configured channels."""
        for channel in self.get_active_channels():
            self.start_channel(channel)

    def stop_all_channels(self):
        """Stop all active channels."""
        for channel in self.get_active_channels():
            self.stop_channel(channel)

    def restart_failed_channels(self):
        """Restart channels that have failed."""
        failed_channels = self.get_failed_channels()
        for channel in failed_channels:
            self.restart_channel(channel)
```

#### Resource Allocation

```python
class ResourceAllocator:
    """Manages resource allocation across multiple channels."""

    def __init__(self):
        self.total_cpu = psutil.cpu_count()
        self.total_memory = psutil.virtual_memory().total
        self.allocated_resources = {}

    def allocate_for_channel(self, channel: Channel, requirements: ResourceRequirements) -> bool:
        """Allocate resources for a specific channel."""
        if self.can_allocate(requirements):
            self.allocated_resources[channel.id] = requirements
            return True
        return False

    def can_allocate(self, requirements: ResourceRequirements) -> bool:
        """Check if resources can be allocated."""
        available_cpu = self.get_available_cpu()
        available_memory = self.get_available_memory()

        return (requirements.cpu <= available_cpu and
                requirements.memory <= available_memory)
```

### Channel Switching

#### Dynamic Content Switching

```python
class ContentSwitcher:
    """Handles dynamic content switching for channels."""

    def switch_to_program(self, channel: Channel, program: Program):
        """Switch channel to new program."""
        # Stop current content
        self.stop_current_content(channel)

        # Prepare new content
        self.prepare_content(program)

        # Switch to new content
        self.switch_content(channel, program)

    def handle_schedule_transition(self, channel: Channel, new_schedule: Schedule):
        """Handle transition to new schedule."""
        current_program = channel.get_current_program()
        next_program = new_schedule.get_next_program()

        if current_program and next_program:
            self.transition_between_programs(channel, current_program, next_program)
```

## 🔧 Configuration

### Channel Configuration

```python
# Channel configuration template
channel_config = {
    "name": "Channel 1",
    "number": 1,
    "description": "Primary entertainment channel",
    "stream_settings": {
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate": "5000k",
        "resolution": "1920x1080",
        "frame_rate": 30
    },
    "quality_settings": {
        "preset": "medium",
        "crf": 23,
        "max_bitrate": "6000k",
        "buffer_size": "12000k"
    },
    "network_settings": {
        "multicast_address": "239.0.0.1",
        "port": 1234,
        "protocol": "udp"
    },
    "resource_limits": {
        "max_cpu_percent": 25,
        "max_memory_mb": 2048,
        "max_bandwidth_mbps": 10
    }
}
```

### Multi-Channel Configuration

```python
# Multi-channel system configuration
multi_channel_config = {
    "max_channels": 8,
    "resource_allocation": {
        "cpu_per_channel": 25,  # 25% CPU per channel
        "memory_per_channel": 2048,  # 2GB memory per channel
        "bandwidth_per_channel": 10  # 10 Mbps per channel
    },
    "failover_settings": {
        "auto_restart": True,
        "max_restart_attempts": 3,
        "restart_delay_seconds": 30
    },
    "monitoring": {
        "health_check_interval": 30,  # seconds
        "metrics_collection": True,
        "alert_thresholds": {
            "cpu_usage": 80,
            "memory_usage": 85,
            "error_rate": 5
        }
    }
}
```

## 📊 Monitoring and Analytics

### Key Metrics

- **Channel status**: Running, stopped, error states
- **Stream health**: Bitrate, frame rate, error rates
- **Resource usage**: CPU, memory, bandwidth per channel
- **Performance**: Latency, throughput, quality metrics
- **Availability**: Uptime, downtime, failure rates

### Health Monitoring

```python
def monitor_channel_health():
    return {
        "active_channels": count_active_channels(),
        "failed_channels": count_failed_channels(),
        "resource_usage": get_resource_usage(),
        "stream_quality": get_stream_quality_metrics(),
        "error_rates": get_error_rates()
    }
```

### Performance Analytics

```python
def analyze_channel_performance():
    return {
        "average_bitrate": calculate_average_bitrate(),
        "frame_drops": count_frame_drops(),
        "latency": measure_stream_latency(),
        "throughput": calculate_throughput(),
        "quality_score": calculate_quality_score()
    }
```

## 🚀 Future Enhancements

### Planned Features

- **Auto-scaling**: Automatic resource scaling based on demand
- **Load balancing**: Distribute load across multiple servers
- **Advanced monitoring**: Real-time performance dashboards
- **Predictive analytics**: Predict and prevent failures
- **Cloud integration**: Deploy channels to cloud infrastructure

### Integration Opportunities

- **CDN Integration**: Distribute streams through CDN
- **Analytics Integration**: Connect with viewing analytics
- **EPG Integration**: Provide channel information to EPG systems
- **Remote Management**: Remote channel management and monitoring

---

_The Channel Manager provides the infrastructure and orchestration needed to deliver reliable, high-quality IPTV channels at scale._
