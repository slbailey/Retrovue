# 🚀 Getting Started with Retrovue

Welcome to Retrovue! This guide will get you up and running with your own retro IPTV system in just 6 simple steps.

## 🎯 What is Retrovue?

Retrovue is a **media-first IPTV system** that simulates a professional broadcast television station. It creates 24/7 TV channels with realistic programming, commercial breaks, and a viewer experience indistinguishable from real cable TV.

## 🎬 The 6-Step Process

### **Step 1: Install Requirements**

Set up the technical foundation with Python, FFmpeg, and Plex integration

### **Step 2: Configure Plex Server**

Add your Plex server and configure authentication

### **Step 3: Import Media**

Sync libraries from Plex and configure path mappings

### **Step 4: Ingest Content**

Import movies and TV shows into the Retrovue database

### **Step 5: Schedule** (Coming Soon)

Create schedule blocks and fill automatically or specify shows

### **Step 6: Stream** (Coming Soon)

Start channel stream and view in VLC or Plex Live TV

---

## 🌐 Web Interface (Recommended for Beginners)

**New in 2025**: Retrovue includes a modern Web UI that makes setup much easier!

### **Launch the Web Interface**

```powershell
# Windows
uvicorn retrovue.api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload

# macOS/Linux
uvicorn retrovue.api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Then open your browser to: **http://localhost:8000**

### **Guided 3-Step Setup**

#### **1. Servers Tab - Add Your Plex Server**

- Click the "Servers" tab
- Enter your Plex server details:
  - **Name**: Friendly name (e.g., "Home Plex")
  - **URL**: `http://your-plex-server:32400`
  - **Token**: [How to get your token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
- Click "Add Server"

#### **2. Libraries Tab - Discover Libraries**

- Click the "Libraries" tab
- Select your server from the dropdown
- Click "Discover Libraries" button
- Check the boxes for libraries you want to sync
- Changes are saved automatically

#### **3. Content Sync Tab - Import Content**

- Click the "Content Sync" tab
- Select server and library
- Add path mappings:
  - **Plex Path**: Path as seen by Plex (e.g., `/mnt/media/movies`)
  - **Local Path**: Corresponding path on your machine (e.g., `D:\Movies`)
  - Click "Add Mapping"
- Set sync limit (optional, useful for testing)
- Click "Dry Run (Preview)" to test
- Click "Sync (Write to DB)" to import
- Watch real-time progress in the log viewer!

### **GUI Features**

- ✅ **Real-time progress** - See every step of the sync process
- ✅ **Error visibility** - All validation errors appear in the GUI
- ✅ **Tooltips** - Hover over any button for helpful guidance
- ✅ **Non-blocking** - UI stays responsive during long operations
- ✅ **Visual feedback** - Immediate confirmation of all actions

---

## 📋 Prerequisites

### **Required Software**

- **Python 3.8+** - The programming language Retrovue is built with
- **FFmpeg** - Handles video processing and streaming (must be in PATH)
- **Git** - For cloning the repository (optional)

### **Optional but Recommended**

- **Plex Media Server** - For importing your existing media library
- **VLC Media Player** - For testing streams
- **A computer that can run 24/7** - Like a home server or NAS

## 🏃‍♂️ Installation

### **Step 1: Clone the Repository**

```bash
git clone https://github.com/your-username/retrovue.git
cd retrovue
```

### **Step 2: Create Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 4: Verify Installation**

```bash
# Test the Plex Sync CLI
python -m cli.plex_sync --help
```

---

## 🎬 Step 2: Configure Plex Server

### **Get Your Plex Token**

1. Open Plex Web Interface: `http://your-plex-server:32400/web`
2. Press `F12` → Network tab → Refresh page
3. Find `X-Plex-Token` in request headers
4. Copy the token value

### **Add Plex Server**

```bash
python -m cli.plex_sync servers add \
  --db ./retrovue.db \
  --name "HomePlex" \
  --base-url "http://your-plex-server:32400" \
  --token "your-plex-token-here"
```

### **Set as Default Server**

```bash
python -m cli.plex_sync servers set-default \
  --db ./retrovue.db \
  --server-name "HomePlex"
```

### **Verify Server Connection**

```bash
python -m cli.plex_sync servers list --db ./retrovue.db
```

---

## 🎬 Step 3: Import Media Libraries

### **Sync Libraries from Plex**

```bash
python -m cli.plex_sync libraries sync-from-plex \
  --db ./retrovue.db \
  --enable-all
```

### **List Available Libraries**

```bash
python -m cli.plex_sync libraries list --db ./retrovue.db
```

### **Configure Path Mappings** (Critical for Streaming)

```bash
# Add path mapping for movies
python -m cli.plex_sync add-mapping \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-prefix "/data/Movies" \
  --local-prefix "C:\Media\Movies"

# Add path mapping for TV shows
python -m cli.plex_sync add-mapping \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 2 \
  --plex-prefix "/data/TV" \
  --local-prefix "C:\Media\TV"
```

### **Test Path Resolution**

```bash
python -m cli.plex_sync resolve-path \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-path "/data/Movies/Test.mkv"
```

---

## 🎬 Step 4: Ingest Content

### **Preview Content (Optional)**

```bash
python -m cli.plex_sync preview-items \
  --db ./retrovue.db \
  --library-key 1 \
  --kind movie \
  --limit 5
```

### **Ingest Content (Dry Run First)**

```bash
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode full \
  --dry-run
```

### **Ingest Content (Commit to Database)**

```bash
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode full \
  --commit
```

### **Check Ingest Status**

```bash
python -m cli.plex_sync ingest-status --db ./retrovue.db
```

---

## 🎯 What You Can Do Now

### **✅ Working Features**

- **Import Content**: Sync movies and TV shows from Plex
- **Browse Library**: View imported content with proper duration formatting
- **Basic Streaming**: Stream a single channel with simple content looping
- **Database Management**: Store and organize media metadata

### **🔄 Coming Soon**

- **Schedule Editor**: Drag-and-drop timeline management
- **Multi-Channel Support**: Run multiple TV channels simultaneously
- **Program Director**: Orchestrate channels and manage playback
- **Advanced Streaming**: Professional-grade streaming with transitions

---

## 🛠️ Troubleshooting

### **Common Issues**

#### **FFmpeg Not Found**

```bash
# Install FFmpeg
# Windows: Download from https://ffmpeg.org/download.html
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

#### **Plex Connection Failed**

- Check Plex server URL (include http:// and port)
- Verify Plex token is correct
- Ensure Plex server is running and accessible
- Check firewall settings

#### **Stream Not Playing in VLC**

- Verify streaming server is running
- Check URL format: `http://localhost:8080/channel/1.ts`
- Try different VLC version
- Check Windows firewall settings

#### **Python Import Errors**

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.8+
```

### **Getting Help**

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the docs folder for detailed guides
- **Discussions**: Ask questions and share ideas

---

## 🎯 Next Steps

### **Explore the Documentation**

- **[Web Interface Guide](web-interface.md)** - Using the modern web UI
- **[Configuration Guide](configuration.md)** - System configuration
- **[Content Management](content-management.md)** - Managing your media library
- **[Streaming Guide](streaming.md)** - Setting up streams

### **Try Advanced Features**

- **CLI Commands**: Use command-line tools for content management
- **Custom Configuration**: Modify settings for your setup
- **Multiple Sources**: Add TinyMediaManager integration
- **Content Validation**: Verify your media files

### **Contribute to Development**

- **Report Issues**: Found a bug? Let us know!
- **Feature Requests**: Have an idea? We'd love to hear it!
- **Development**: Help build new features and improvements
- **Testing**: Try it out and provide feedback

---

## 🎉 Congratulations!

You've successfully set up Retrovue! You now have:

- ✅ A working content management system
- ✅ Basic streaming capabilities
- ✅ A foundation for building your own TV network

**What's Next?** Check out the [Development Roadmap](../developer/development-roadmap.md) to see what features are coming next and how you can contribute to the project.

---

_Happy streaming! 📺✨_
