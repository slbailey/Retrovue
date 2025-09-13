# 📺 Retrovue - Retro IPTV Simulation Project

## 🎬 What is Retrovue?

Retrovue is a **network-grade IPTV system** that simulates a realistic broadcast TV station experience. Instead of just watching your media files one at a time, Retrovue creates **24/7 TV channels** that play your movies and TV shows on a schedule, insert commercials and station bumpers, and run multiple channels simultaneously.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg installed and in PATH
- Plex Media Server (optional, for content import)

### Installation
```bash
# Clone and setup
git clone https://github.com/your-username/retrovue.git
cd retrovue
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# Launch the management interface
python run_ui.py

# Start streaming server
python main.py
```

### Test the Stream
1. Open VLC Media Player
2. Go to: Media → Open Network Stream
3. Enter: `http://localhost:8080/channel/1.ts`
4. Click Play

## 🎯 Current Status

### ✅ What's Working Now
- **Content Import**: Sync movies and TV shows from Plex Media Server
- **Library Management**: Browse and organize your content library
- **Basic Streaming**: Single-channel streaming with simple content looping
- **Smart Sync System**: Only updates content that has changed (super fast!)

### 🔄 What's Coming Next
- **Schedule Editor**: Drag-and-drop timeline management
- **Multi-Channel Support**: Run multiple TV channels simultaneously
- **Program Director**: Orchestrate channels and manage playback
- **Advanced Streaming**: Professional-grade streaming with transitions

## 📚 Documentation

All documentation has been moved to the `documentation/` folder for better organization:

- **[📖 Beginner's Guide](documentation/README.md)** - What Retrovue does and how all the pieces fit together
- **[🚦 Development Roadmap](documentation/development-roadmap.md)** - Track progress and see what's coming next
- **[🏗️ System Architecture](documentation/architecture.md)** - Technical details about how Retrovue works
- **[🗄️ Database Schema](documentation/database-schema.md)** - How content and scheduling data is stored
- **[🎬 Plex Integration](documentation/plex-integration.md)** - How Retrovue connects to your Plex server
- **[🎛️ Streaming Engine](documentation/streaming-engine.md)** - How video streaming works
- **[🚀 Quick Start Guide](documentation/quick-start.md)** - Step-by-step setup instructions

## 🏗️ Project Goals
Simulate a realistic broadcast TV station experience:
- 📡 Channels with playout schedules  
- 📺 Commercials, intros/outros, bumpers  
- ⚠️ Emergency alert overrides  
- 🎨 Graphics overlays (bugs, lower thirds, branding)  
- 🌐 Deliver streams as HLS playlists (`.m3u8` + segments) consumable by Plex and VLC  
- 🖥️ Provide a management UI for metadata and scheduling  

## 🛠️ Tech Stack

- **Playback:** ffmpeg, Docker  
- **Management UI:** Python (PySide6 / Tkinter)  
- **Database:** SQLite (initial)  
- **Serving:** Python FastAPI / lightweight HTTP server  
- **Clients:** Plex Live TV, VLC  

## 🤝 Contributing

Retrovue is designed to be a community-driven project. Whether you're a developer, content creator, or just someone who loves retro TV, there are ways to contribute:

- **Report Issues**: Found a bug? Let us know!
- **Feature Requests**: Have an idea? We'd love to hear it!
- **Development**: Help build new features and improvements
- **Testing**: Try it out and provide feedback
- **Documentation**: Help improve guides and tutorials

## 🧪 Running Tests with Live Plex

The smoke tests can run against a live Plex server for comprehensive integration testing.

### Required Environment Variables

Set these environment variables to enable live Plex testing:

```bash
# Required: Your Plex server base URL
export PLEX_BASE_URL="http://192.168.1.100:32400"

# Required: Your Plex authentication token
# Get this from: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
export PLEX_TOKEN="your_plex_token_here"

# Optional: Custom name for the test server (defaults to "LivePlex")
export PLEX_SERVER_NAME="HomePlex"
```

### Running Live Tests

```bash
# Run simple smoke tests
python scripts/smoke_test_simple.py

# Run comprehensive smoke tests
python scripts/smoke_test.py

# Run shell-based smoke tests
bash scripts/smoke.sh
```

### Windows (PowerShell)
```powershell
$env:PLEX_BASE_URL="http://192.168.1.100:32400"
$env:PLEX_TOKEN="xxxxx"
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/smoke.ps1
```

### Offline Mode

For CI/testing without network access, set:

```bash
export PLEX_OFFLINE=1
```

This will run tests in offline mode, validating CLI structure without network operations.

### JSON Output

Many commands support `--format json` for machine-readable output:

```bash
# Get server information as JSON
python cli/plex_sync.py --format json servers list

# Add server and get ID as JSON
python cli/plex_sync.py --format json servers add --name "Test" --base-url "http://test" --token "abc123"
```

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check the docs folder for detailed guides

---

*Retrovue: Bringing the magic of retro TV to the modern streaming era* 📺✨