# 🚀 Quick Start Guide

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
python -c "import retrovue; print('Retrovue installed successfully!')"
```

## 🎬 First Run - Content Management

### **Launch the Management Interface**
```bash
python run_ui.py
```

### **Import Content from Plex (Optional)**
1. **Get Your Plex Token**:
   - Open Plex Web Interface: `http://your-plex-server:32400/web`
   - Press `F12` → Network tab → Refresh page
   - Find `X-Plex-Token` in request headers
   - Copy the token value

2. **Add Plex Server**:
   - Click "Import" tab in Retrovue
   - Enter Plex server URL: `http://your-plex-server:32400`
   - Enter your Plex token
   - Click "Test Connection"
   - Click "Sync Libraries"

3. **Browse Your Content**:
   - Click "Browser" tab
   - View your imported movies and TV shows
   - Content is now ready for scheduling!

## 🎛️ First Run - Streaming Server

### **Start the Streaming Server**
```bash
# Simple loop mode (default)
python main.py

# Or use concat mode for better transitions
python main.py --mode concat

# Custom options
python main.py --mode concat --loops 10 --port 8081
```

### **Test the Stream**
1. **Open VLC Media Player**
2. **Go to**: Media → Open Network Stream
3. **Enter**: `http://localhost:8080/channel/1.ts`
4. **Click Play**

You should see your content streaming continuously!

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

## 🎯 Next Steps

### **Explore the Documentation**
- **[System Architecture](architecture.md)** - How Retrovue works
- **[Database Schema](database-schema.md)** - How data is stored
- **[Plex Integration](plex-integration.md)** - Connecting to Plex
- **[Streaming Engine](streaming-engine.md)** - How streaming works

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

## 🎉 Congratulations!

You've successfully set up Retrovue! You now have:
- ✅ A working content management system
- ✅ Basic streaming capabilities
- ✅ A foundation for building your own TV network

**What's Next?** Check out the [Development Roadmap](development-roadmap.md) to see what features are coming next and how you can contribute to the project.

---

*Happy streaming! 📺✨*
