# 📺 Retrovue - Retro IPTV Simulation Project

## 🎬 What is Retrovue?

Retrovue is a **network-grade IPTV system** that simulates a realistic broadcast TV station experience. Think of it as your own personal cable TV network that can serve multiple viewers simultaneously.

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
- **Plex Integration**: Automatically imports your existing Plex library
- **Smart Sync**: Only updates content that has actually changed (super fast!)
- **Episode-Level Control**: Each TV episode is managed separately for precise scheduling
- **Metadata Storage**: Tracks everything you need for professional scheduling

## 🏗️ How All The Pieces Fit Together

### 1. Content Management (✅ Working Now)
```
Your Plex Library → Retrovue Database → Content Browser
```
- **Import**: Pulls movies and TV shows from your Plex server
- **Organize**: Stores metadata, durations, and scheduling preferences
- **Browse**: View and manage your content library through a desktop app

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
- **Movies**: Feature films with commercial break planning
- **TV Shows**: Episodes with intro/outro timing
- **Commercials**: 15s, 30s, 60s spots with targeting
- **Bumpers**: Station IDs, "We'll be right back" segments
- **Intros/Outros**: Show openings and closings
- **Interstitials**: Filler content between shows

### Smart Scheduling Features
- **Daypart Targeting**: Morning shows, prime time, late night
- **Seasonal Content**: Holiday specials, summer programming
- **Demographic Targeting**: Family-friendly, adult content
- **Content Ratings**: G, PG, PG-13, R, Adult classifications

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
- **Content Import**: Sync movies and TV shows from Plex
- **Library Management**: Browse and organize your content
- **Database System**: Store all metadata and scheduling information
- **Basic Streaming**: Single-channel streaming with simple content looping

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

- **[Development Roadmap](development-roadmap.md)** - Track progress and see what's coming next
- **[System Architecture](architecture.md)** - Technical details about how Retrovue works
- **[Database Schema](database-schema.md)** - How content and scheduling data is stored
- **[Plex Integration](plex-integration.md)** - How Retrovue connects to your Plex server
- **[Streaming Engine](streaming-engine.md)** - How video streaming works
- **[Quick Start Guide](quick-start.md)** - Step-by-step setup instructions

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
