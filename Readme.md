# 📺 Retrovue - Retro IPTV Simulation Project

[![CI](https://github.com/slbailey/Retrovue/actions/workflows/ci.yml/badge.svg)](https://github.com/slbailey/Retrovue/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎬 What is Retrovue?

Retrovue is a **network-grade IPTV system** that simulates a realistic broadcast TV station experience. Instead of just watching your media files one at a time, Retrovue creates **24/7 TV channels** that play your movies and TV shows on a schedule, insert commercials and station bumpers, and run multiple channels simultaneously.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg installed and in PATH
- Plex Media Server (optional, for content import)

### Installation

**Windows (PowerShell):**

```powershell
# Clone and setup
git clone https://github.com/slbailey/Retrovue.git
cd Retrovue
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Launch the CLI tools
python -m cli.plex_sync --help
```

**macOS/Linux (bash):**

```bash
# Clone and setup
git clone https://github.com/slbailey/Retrovue.git
cd Retrovue
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Launch the CLI tools
python -m cli.plex_sync --help
```

### Launch the GUI (Recommended)

**New in 2025**: Retrovue now includes a modern **PySide6/Qt GUI** for easier setup and management!

```powershell
# Windows
.\venv\Scripts\python.exe run_enhanced_gui.py

# macOS/Linux
python run_enhanced_gui.py
```

**GUI Features:**

- 🖥️ **Servers Tab**: Add and manage your Plex servers
- 📚 **Libraries Tab**: Discover and select libraries to sync
- 🔄 **Content Sync Tab**: Configure path mappings and sync content
- 📊 **Visual Progress**: See sync progress in real-time
- ✨ **User-Friendly**: Tooltips and validation help guide you

**First-Time Setup:**

1. **Servers Tab**: Add your Plex server (name, URL, token)
2. **Libraries Tab**: Click "Discover Libraries" to find available libraries
3. **Content Sync Tab**:
   - Select server and library
   - Add path mappings (Plex path → Local path)
   - Click "Dry Run" to preview, then "Sync" to import

### Test the Stream (Legacy - For Testing Only)

> ⚠️ **Note**: The streaming engine is currently being reworked. The legacy streaming server serves a raw MPEG-TS stream for basic testing purposes.

**For VLC Testing:**

1. Open VLC Media Player
2. Go to: Media → Open Network Stream
3. Enter: `http://localhost:8080/channel/1.ts`
4. Click Play

**Planned Streaming Output:**

- HLS format with `.m3u8` playlists and `.ts` segments
- Multi-channel support with independent schedules
- Industry-standard compatibility with Plex Live TV, smart TVs, and mobile devices
- See [Streaming Engine Documentation](documentation/streaming-engine.md) for technical details

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
- **[🎬 Plex Sync CLI](documentation/plex-sync-cli.md)** - Command-line interface for Plex integration
- **[🎛️ Streaming Engine](documentation/streaming-engine.md)** - How video streaming works
- **[🚀 Quick Start Guide](documentation/quick-start.md)** - Step-by-step setup instructions
- **[📝 GUI Migration Notes](MIGRATION_NOTES.md)** - Complete history of GUI modularization (Phases 1-8)

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
- **Management UI:** Python PySide6/Qt (modern modular GUI)
- **Core API:** Python with clean separation (GUI ↔ Core API ↔ Managers)
- **Database:** SQLite with versioned schema migrations
- **Serving:** Python FastAPI / lightweight HTTP server (planned)
- **Clients:** Plex Live TV, VLC

### Database & Persistence Strategy

**Current Implementation:**

- **SQLite** is used for initial development and single-instance deployments
- **Versioned Schema**: Schema files track version history (`sql/retrovue_schema_v1.2.3.sql` is current)
- **Migration Path**: Schema upgrades are managed through versioned SQL files

**Future Considerations:**

- **PostgreSQL Support**: Planned for multi-user and high-concurrency deployments
- **Schema Migrations**: Will use Alembic for automated database migrations
- **Backward Compatibility**: Upgrade paths will be provided for early adopters
- **Data Export/Import**: Tools will be provided for migrating between database backends

**For Early Adopters:**

- Current SQLite database structure is stable for content management and scheduling
- Schema changes will be documented with upgrade scripts
- Backup your `retrovue.db` file regularly (it's excluded from git via `.gitignore`)

## 🤝 Contributing

Retrovue is designed to be a community-driven project. Whether you're a developer, content creator, or just someone who loves retro TV, there are ways to contribute!

**Ways to Contribute:**

- **Report Issues**: Found a bug? [Create an issue](https://github.com/slbailey/Retrovue/issues/new/choose)
- **Feature Requests**: Have an idea? [Request a feature](https://github.com/slbailey/Retrovue/issues/new/choose)
- **Development**: Help build new features and improvements
- **Testing**: Try it out and provide feedback
- **Documentation**: Help improve guides and tutorials

**Getting Started:**

- Read our [Contributing Guide](CONTRIBUTING.md) for development workflow and guidelines
- Check the [Development Roadmap](documentation/development-roadmap.md) for planned features
- Browse [Good First Issues](https://github.com/slbailey/Retrovue/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to get started

**License:** Retrovue is released under the [MIT License](LICENSE).

## ⚙️ Configuration & Secrets Management

### Configuration Strategy

Retrovue uses multiple configuration approaches depending on the use case:

**1. Database-Stored Configuration (Primary)**

- Plex server URLs, tokens, and library mappings are stored in the SQLite database
- Managed via the CLI: `python -m cli.plex_sync servers add`
- Best for persistent server configuration and library settings

**2. Environment Variables (Testing & CI)**

- Used primarily for testing and CI/CD pipelines
- Overrides database configuration when set
- Useful for temporary testing without modifying database

**3. Configuration Files (Future)**

- Planned support for `.env` files using pydantic settings
- Will support structured configuration with validation
- Environment-specific configs (dev, staging, production)

### Configuration Precedence

When the same setting exists in multiple places:

1. **Environment Variables** (highest priority) - for testing/override
2. **Database Configuration** - for persistent settings
3. **Default Values** (lowest priority) - fallback values

### Secrets Management Best Practices

**DO:**

- ✅ Store Plex tokens in the database (excluded from git via `.gitignore`)
- ✅ Use environment variables for CI/CD pipelines
- ✅ Keep backup copies of your `retrovue.db` file securely
- ✅ Review `documentation/env.example` for environment variable reference

**DON'T:**

- ❌ Commit `retrovue.db` or `PlexToken.txt` to version control
- ❌ Share your Plex token publicly
- ❌ Store tokens in scripts or unencrypted config files
- ❌ Use production credentials in test environments

## 🧪 Running Tests with Live Plex

The smoke tests can run against a live Plex server for comprehensive integration testing.

### Environment Variables for Testing

Set these environment variables to enable live Plex testing:

**PowerShell (Windows):**

```powershell
# Required: Your Plex server base URL
$env:PLEX_BASE_URL="http://192.168.1.100:32400"

# Required: Your Plex authentication token
# Get this from: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
$env:PLEX_TOKEN="your_plex_token_here"

# Optional: Custom name for the test server (defaults to "LivePlex")
$env:PLEX_SERVER_NAME="HomePlex"
```

**Bash (macOS/Linux):**

```bash
# Required: Your Plex server base URL
export PLEX_BASE_URL="http://192.168.1.100:32400"

# Required: Your Plex authentication token
export PLEX_TOKEN="your_plex_token_here"

# Optional: Custom name for the test server (defaults to "LivePlex")
export PLEX_SERVER_NAME="HomePlex"
```

### Running Live Tests

**Python-Based Tests:**

```bash
# Run simple smoke tests
python scripts/smoke_test_simple.py

# Run comprehensive smoke tests
python scripts/smoke_test.py
```

**Shell-Based Tests:**

_Windows (PowerShell):_

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/smoke.ps1
```

_macOS/Linux (bash):_

```bash
bash scripts/smoke.sh
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

_Retrovue: Bringing the magic of retro TV to the modern streaming era_ 📺✨
