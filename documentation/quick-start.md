# 🚀 Quick Start Guide

## 🎯 The Retrovue 6-Step Process

Retrovue follows a **media-first approach** with a streamlined 6-step process to get your retro IPTV system up and running:

### **Step 1: Install Requirements** 
Set up the technical foundation with Python, FFmpeg, and optional Plex integration

### **Step 2: Run Retrovue**
Launch the management UI and streaming engine

### **Step 3: Import Media**
Connect to Plex server, sync libraries, and configure path mappings

### **Step 4: Tag & Configure**
Apply namespaced tags for scheduling and add ratings/parental codes

### **Step 5: Schedule**
Create schedule blocks and fill automatically or specify shows

### **Step 6: Stream**
Start channel stream and view in VLC or Plex Live TV

---

## 📋 Detailed Prerequisites

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

## 🎬 Step 3: Import Media - Detailed Instructions

### **Launch the Management Interface**
```bash
python run_ui.py
```

### **Import Content from Plex (Primary Method)**
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

3. **Configure Path Mappings** (Critical for Streaming):
   - Navigate to Settings → Path Mappings
   - Map Plex internal paths to accessible local paths
   - Example: `/media/movies` → `R:\movies`
   - Test each mapping to ensure files are accessible

4. **Browse Your Content**:
   - Click "Browser" tab
   - View your imported movies and TV shows
   - Content is now ready for tagging and scheduling!

### **Import from TinyMediaManager (Alternative Method)**
1. **Configure TMM Directories**:
   - Go to Settings → TMM Directories
   - Add directories containing .nfo files
   - Enable subdirectory scanning if needed

2. **Sync TMM Content**:
   - Click "Import" tab → TMM Sync
   - Select directories to scan
   - Review imported content and metadata

### **Manual Content Entry**
1. **Add Manual Content**:
   - Click "Add Content" button
   - Enter media file path
   - Fill in basic metadata (title, type, duration)
   - Save to database

## 🏷️ Step 4: Tag & Configure - Advanced Metadata Management

### **Apply Namespaced Tags**
Retrovue uses a powerful **namespaced tagging system** for flexible content organization:

#### **Audience Targeting Tags**
- `audience:kids` - Content suitable for children
- `audience:adult` - Adult-oriented content
- `audience:family` - Family-friendly content
- `audience:seniors` - Content appealing to older audiences

#### **Seasonal Content Tags**
- `holiday:christmas` - Christmas-themed content
- `holiday:halloween` - Halloween-themed content
- `holiday:easter` - Easter-themed content
- `season:summer` - Summer programming
- `season:winter` - Winter programming

#### **Brand and Category Tags**
- `brand:fast_food` - Fast food commercials
- `brand:automotive` - Car commercials
- `brand:retail` - Retail store commercials
- `tone:comedy` - Comedic content
- `tone:drama` - Dramatic content
- `tone:action` - Action-oriented content

### **Set Parental Ratings**
Configure content ratings for appropriate scheduling:

#### **Movie Ratings (MPAA)**
- **G** - General audiences
- **PG** - Parental guidance suggested
- **PG-13** - Parents strongly cautioned
- **R** - Restricted
- **NC-17** - No children under 17

#### **TV Ratings**
- **TV-Y** - All children
- **TV-Y7** - Children 7 and older
- **TV-G** - General audience
- **TV-PG** - Parental guidance suggested
- **TV-14** - Parents strongly cautioned
- **TV-MA** - Mature audience only

### **Configure Daypart Restrictions**
Set up automatic content filtering based on time of day:
- **Morning (6 AM - 12 PM)**: Family-friendly content only
- **Afternoon (12 PM - 6 PM)**: General audience content
- **Evening (6 PM - 11 PM)**: All content with parental discretion
- **Late Night (11 PM - 6 AM)**: Adult content allowed

## 📅 Step 5: Schedule - Advanced Scheduling System

### **Create Schedule Blocks (Programming Templates)**
Schedule blocks define high-level programming patterns:

#### **Example Schedule Blocks**
- **"Sitcoms at 5pm"**: Weekdays 5:00 PM - 6:00 PM, comedy content only
- **"Morning News"**: Daily 7:00 AM - 8:00 AM, news and information
- **"Late Night Movies"**: Weekends 11:00 PM - 2:00 AM, R-rated movies allowed
- **"Kids After School"**: Weekdays 3:00 PM - 5:00 PM, TV-Y and TV-G content only

#### **Schedule Block Configuration**
1. **Basic Settings**:
   - Name: Descriptive name for the block
   - Channel: Which channel this applies to
   - Day of Week: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, Weekday, Weekend, Daily
   - Time Window: Start and end times

2. **Content Filtering**:
   - Content Type: Movies, episodes, commercials, etc.
   - Tag Filters: JSON array of tag requirements
   - Parental Rating Limit: Maximum rating allowed
   - Duration Limits: Minimum/maximum content duration

### **Create Schedule Instances (Specific Events)**
Schedule instances are specific content scheduled for exact date/time combinations:

#### **Automatic Scheduling**
- **Auto-Fill**: Let the system automatically select content based on schedule block rules
- **Tag Matching**: System selects content that matches required tags
- **Rating Compliance**: Ensures content meets parental rating requirements
- **Rotation Management**: Prevents content from repeating too frequently

#### **Manual Scheduling**
- **Specific Shows**: Schedule specific movies or episodes for exact times
- **Special Events**: One-time programming, live events, special presentations
- **Override Scheduling**: Override automatic scheduling with manual selections
- **Priority Management**: Set priority levels for content conflicts

### **Schedule Approval Workflow**
1. **Review Schedule**: Check automatically generated schedule
2. **Make Adjustments**: Modify content selections as needed
3. **Approve Schedule**: Finalize schedule for broadcast
4. **Monitor Changes**: Track any last-minute schedule modifications

## 🎛️ Step 6: Stream - Advanced Streaming Options

### **Start the Streaming Server**
```bash
# Simple loop mode (default)
python main.py

# Or use concat mode for better transitions
python main.py --mode concat

# Custom options
python main.py --mode concat --loops 10 --port 8081
```

### **Streaming Modes Explained**

#### **Loop Mode (Basic)**
- **Use Case**: Simple content looping for testing and basic operation
- **Features**: Basic HLS streaming with content looping
- **Limitations**: Single channel, no scheduling, simple transitions
- **Best For**: Initial setup and testing

#### **Concat Mode (Advanced)**
- **Use Case**: More sophisticated content playback with better transitions
- **Features**: Improved content transitions, better timing control
- **Limitations**: Still single channel, limited scheduling
- **Best For**: Production use with single channel

#### **Multi-Channel Mode (Future)**
- **Use Case**: Full broadcast TV simulation with multiple channels
- **Features**: Multiple channels, advanced scheduling, emergency overrides
- **Benefits**: Professional broadcast TV experience
- **Best For**: Complete TV network simulation

### **Test the Stream**
1. **Open VLC Media Player**
2. **Go to**: Media → Open Network Stream
3. **Enter**: `http://localhost:8080/channel/1.ts`
4. **Click Play**

You should see your content streaming continuously with proper HLS segment handling!

### **Advanced Streaming Features**

#### **Ad Break Integration**
- **Chapter Markers**: Automatic ad break detection from video chapters
- **Manual Markers**: Custom ad break placement and timing
- **Commercial Insertion**: Seamless commercial insertion during playback
- **Timing Control**: Precise control over ad break timing and duration

#### **EPG/Guide Data Export**
- **Plex Live TV**: Export Electronic Program Guide data for Plex integration
- **Prevue Channel**: Generate program guide data for Prevue-style channel information
- **Real-time Updates**: Guide data updates automatically as schedules change
- **Standard Formats**: Industry-standard EPG formats for maximum compatibility

#### **Play Log Tracking**
- **Content Tracking**: Records what programs and ads actually aired
- **Timing Accuracy**: Tracks actual vs. scheduled timing for all content
- **Error Logging**: Records playback errors, missing files, and technical issues
- **Weekly Rotation**: Automatic log management to prevent database bloat

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
