# 📺 Retrovue - Retro IPTV Simulation Project

## 🎬 What is Retrovue?

Retrovue is a **retro-inspired IPTV simulation system** designed to recreate the authentic experience of scheduled broadcast television. It is built on a **media-first foundation** where everything begins with a physical media file, and rich metadata is layered on top to create a comprehensive broadcast TV experience.

### **Media-First Architecture**
Retrovue's core philosophy centers around the **media-first approach**:
- **Physical Foundation**: Every piece of content must have an actual playable media file as its foundation
- **Logical Wrappers**: Content items (movies, episodes, bumpers, commercials, etc.) are logical wrappers around media files
- **Metadata Layering**: Rich metadata is layered on top of the media file without modifying the original
- **Playback Guarantee**: Every scheduled item can be played because it has a verified media file

### **Plex-First Integration**
Retrovue is designed with **Plex Media Server integration** as the primary content source:
- **Seamless Import**: Automatically syncs your existing Plex library with episode-level granularity
- **Smart Synchronization**: Only updates content that has actually changed for optimal performance
- **Path Mapping**: Translates Plex internal paths to accessible local file paths
- **Multi-Server Support**: Manage multiple Plex servers from one Retrovue installation

### **Network-Grade IPTV System**
Retrovue functions as a **network-grade IPTV system** that simulates a realistic broadcast TV station experience. Think of it as your own personal cable TV network that can serve multiple viewers simultaneously with professional-grade features and reliability.

### The Big Picture

Instead of just watching your media files one at a time, Retrovue creates **24/7 TV channels** that:
- Play your movies and TV shows on a schedule
- Insert commercials and station bumpers
- Run multiple channels simultaneously (like real cable TV)
- Stream to any device that can play IPTV (VLC, Plex, smart TVs, etc.)

## 🎯 What Makes This Special?

### Real TV Station Experience
- **Multiple Channels**: Run several TV channels at once, each with its own schedule
- **Professional Timing**: Proper transitions, commercial breaks, and station IDs
- **Live Streaming**: Continuous 24/7 operation with HLS streaming
- **Emergency Overrides**: Break into programming with alerts or announcements

### Smart Content Management
- **Plex Integration**: Automatically imports your existing Plex library with episode-level granularity
- **Smart Sync**: Only updates content that has actually changed (super fast!)
- **Episode-Level Control**: Each TV episode is managed separately for precise scheduling
- **Metadata Storage**: Tracks everything you need for professional scheduling
- **Path Mapping**: Translates Plex internal paths to accessible local file paths
- **Multi-Server Support**: Manage multiple Plex servers from one installation

### Advanced Metadata Management
- **Editorial Overrides**: Customize metadata without overwriting source data from Plex
- **Namespaced Tagging**: Organize content with structured tags like `audience:kids`, `holiday:christmas`, `brand:fast_food`
- **Parental Controls**: MPAA/TV ratings system with daypart restrictions
- **Content Classification**: Flexible tagging system for audience targeting, seasonal content, and brand management

## 🏗️ How All The Pieces Fit Together

### 1. Content Management (✅ Working Now)
```
Your Plex Library → Plex Sync CLI → Retrovue Database
```
- **Import**: Pulls movies and TV shows from your Plex server using the Plex Sync CLI
- **Organize**: Stores metadata, durations, and scheduling preferences
- **Manage**: Configure servers, libraries, and path mappings via command line

### 2. Scheduling System (🔄 Coming Next)
```
Content Library → Schedule Editor → Timeline Management
```
- **Timeline Editor**: Drag-and-drop interface to create broadcast schedules
- **Multi-Channel**: Each channel has its own independent schedule
- **Commercial Integration**: Insert commercials, bumpers, and station IDs
- **Real-time Monitoring**: See what's currently airing on each channel

### 3. Streaming Engine (🔄 Coming Next)
```
Schedules → Program Director → FFmpeg → HLS Streams
```
- **Program Director**: Orchestrates all channels and manages playback
- **FFmpeg Processing**: Converts your media into streaming format
- **HLS Output**: Creates industry-standard streams that work everywhere
- **Multi-Channel**: Runs multiple streams simultaneously

### 4. Client Access (🔄 Coming Next)
```
HLS Streams → Network → VLC/Plex/Smart TV
```
- **VLC**: Direct network stream playback
- **Plex Live TV**: Native integration with Plex
- **Smart TVs**: Works with any IPTV-capable device
- **Mobile Apps**: Stream to phones and tablets

## 🎬 Content Types Supported

### TV Network Content
- **Movies**: Feature films with commercial break planning and chapter marker support
- **TV Shows**: Episodes with intro/outro timing and episode-level scheduling
- **Commercials**: 15s, 30s, 60s spots with advanced targeting and brand management
- **Bumpers**: Station IDs, "We'll be right back" segments with timing control
- **Intros/Outros**: Show openings and closings with seamless integration
- **Interstitials**: Filler content between shows with flexible placement

### Advanced Content Features
- **Chapter Markers**: Support for commercial break planning and content segmentation
- **Manual Ad Break Input**: Custom ad break placement and timing control
- **Media Markers**: Store ad breaks, chapters, and cue points from various sources
- **Content Validation**: Verify media files are playable and codec-compatible
- **Path Mapping**: Translate Plex/TMM paths to accessible local file paths

### Smart Scheduling Features
- **Schedule Blocks**: High-level programming templates (e.g., "Sitcoms at 5pm weekdays")
- **Schedule Instances**: Specific content scheduled for exact date/time combinations
- **Daypart Targeting**: Morning shows, prime time, late night with automatic content filtering
- **Seasonal Content**: Holiday specials, summer programming with automatic seasonal scheduling
- **Demographic Targeting**: Family-friendly, adult content with audience-based scheduling
- **Content Ratings**: G, PG, PG-13, R, Adult classifications with parental control enforcement
- **Commercial Spacing Rules**: Control commercial placement and brand separation
- **Episode Rotation Rules**: Prevent content from repeating too frequently

### Advanced Logging and Analytics
- **Play Log Tracking**: Records what programs and ads actually aired
- **Weekly Log Rotation**: Automatic log management to prevent database bloat
- **Performance Metrics**: Track system performance and resource usage
- **Error Logging**: Record playback errors, missing files, and technical issues
- **Compliance Tracking**: Maintain records for regulatory and audit purposes

## 🚀 Getting Started

### What You Need
- **Python 3.8+** (the programming language Retrovue is built with)
- **FFmpeg** (handles video processing and streaming)
- **Plex Media Server** (optional, for importing your existing library)
- **A computer** that can run 24/7 (like a home server or NAS)

### Quick Start
1. **Install Retrovue**: Follow the setup instructions in the main README
2. **Import Content**: Connect to your Plex server and sync your library
3. **Browse Library**: Use the desktop app to view and organize your content
4. **Create Schedules**: Build your first TV channel schedule (coming soon!)
5. **Start Streaming**: Launch your first 24/7 TV channel (coming soon!)

## 🎯 Current Status

### ✅ What's Working Now
- **Plex Integration**: Complete CLI-based Plex server management and content import
- **Library Management**: Sync and manage Plex libraries with granular control
- **Path Mapping**: Translate Plex paths to accessible local file paths
- **Content Ingestion**: Import movies and TV shows with full metadata
- **Database System**: Store all metadata and scheduling information
- **Smart Sync**: Only update content that has actually changed

### 🔄 What's Coming Next
- **Schedule Editor**: Drag-and-drop timeline management
- **Multi-Channel Support**: Run multiple TV channels simultaneously
- **Program Director**: Orchestrate channels and manage playback
- **Advanced Streaming**: Professional-grade streaming with transitions

### 🎯 End Goal
A **robust IPTV system** that provides a viewer experience **indistinguishable from real cable TV**:
- Multi-channel 24/7 operation
- Realistic transitions and timing
- Professional scheduling and management
- Easy-to-use interface for content creators

## 📚 Learn More

- **[Plex Sync CLI Reference](plex-sync-cli.md)** - Complete command-line interface documentation
- **[Quick Start Guide](quick-start.md)** - Step-by-step setup instructions
- **[Development Roadmap](development-roadmap.md)** - Track progress and see what's coming next
- **[System Architecture](architecture.md)** - Technical details about how Retrovue works
- **[Database Schema](database-schema.md)** - How content and scheduling data is stored
- **[Streaming Engine](streaming-engine.md)** - How video streaming works

## 🤝 Contributing

Retrovue is designed to be a community-driven project. Whether you're a developer, content creator, or just someone who loves retro TV, there are ways to contribute:

- **Report Issues**: Found a bug? Let us know!
- **Feature Requests**: Have an idea? We'd love to hear it!
- **Development**: Help build new features and improvements
- **Testing**: Try it out and provide feedback
- **Documentation**: Help improve guides and tutorials

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check the docs folder for detailed guides

---

*Retrovue: Bringing the magic of retro TV to the modern streaming era* 📺✨

