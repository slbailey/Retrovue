# 📺 Retrovue - Retro IPTV Simulation Project

## 🎬 Inspiration
Inspired by **RetroTV Live 24/7 Vintage Cable TV Network on Raspberry Pi**, this project takes the concept further:  
Instead of a single-device solution, it will build a **network-grade IPTV system** that integrates with Plex Live TV and serves multiple viewers.

---

## 🏗️ Project Goals
Simulate a realistic broadcast TV station experience:
- 📡 Channels with playout schedules  
- 📺 Commercials, intros/outros, bumpers  
- ⚠️ Emergency alert overrides  
- 🎨 Graphics overlays (bugs, lower thirds, branding)  
- 🌐 Deliver streams as HLS playlists (`.m3u8` + segments) consumable by Plex and VLC  
- 🖥️ Provide a management UI for metadata and scheduling  

---

## 📐 System Architecture
**Program Director** (Top-level Controller)  
├─ **Channel Management**  
│  └─ Multiple Channels  
│     ├─ Schedule Manager  
│     ├─ Pipeline Manager  
│     ├─ Graphics Manager  
│     └─ Playback Pipeline  
│  
└─ **Shared Resources**  
  ├─ Content Manager  
  └─ Emergency System  

**Components:**
- **Program Director** – Orchestrates all channels, manages state, coordinates emergencies.  
- **Channel** – Independent broadcast unit with schedule + pipeline.  
- **Schedule Manager** – Maintains coarse (show-level) and fine (break-level) logs.  
- **Pipeline Manager** – Controls playback transitions and timing.  
- **Graphics Manager** – Overlays bugs, branding, emergency graphics.  
- **Content Manager (Shared)** – Ingests and validates assets, stores metadata, distributes to channels.  
- **Emergency System (Shared)** – Provides priority alerts across all channels.  

---

## 📂 Media & Metadata Strategy
- All existing media lives in **Plex** or is tagged with **TinyMediaManager** metadata.  
- Project will:  
  - Store only **playback-relevant metadata** (schedules, playout history, commercial timing).  
  - Reference series/episode metadata from Plex or sidecar files (avoid duplication).  
- 🎯 Goal: A **unified UI for editing scheduling metadata**, not a full media manager.  

---

## 🎛️ Playback Engine
- Core technology: **ffmpeg** → segment + encode into HLS  
- Segments delivered as `.ts` or `fmp4` with rotating `master.m3u8`  
- **Phase 1:** Single-channel with scripted ffmpeg command  
- **Phase 2+:** Multi-channel orchestration + advanced playout logic  
- Deployment: **Docker containers** for isolation and portability  

---

## 🖥️ Management UI
Desktop UI in **Python** (PySide6 / PyQt / Tkinter).  
Features:  
- Media ingestion (browse Plex / TinyMediaManager)  
- Metadata editing (runtime, bumpers, commercial breakpoints)  
- Coarse + fine schedule views  
- Log viewing + error monitoring  

---

## 🚦 Development Roadmap

### **Phase 1 — Proof of Concept** ✅
- [x] Build single-channel playout (`ffmpeg → HLS → VLC`)  
- [x] Solve segment rotation issues (`-hls_delete_threshold`, epoch numbering)  
- [x] Validate continuous playback via local HTTP server  

### **Phase 2 — Core System Architecture**

#### **2.1 Data Foundation** ✅ **COMPLETED**
- [x] **Database Schema Design** - Normalized schema for media files, shows, episodes, movies
- [x] **Content Manager** - Media ingestion, validation, metadata storage
- [x] **Plex Integration** - Import movies/shows from Plex Media Server via API with episode-level granularity
- [x] **Smart Sync System** - Intelligent sync with conflict resolution and change detection
- [x] **Content Import UI** - PySide6 interface with real-time progress updates

#### **2.2 Content Management** ✅ **COMPLETED**
- [x] **Content Browser UI** - Browse and organize content library with proper duration formatting
- [x] **Database Migrations** - Schema updates without data loss
- [x] **Library Management** - Store library names as media file attributes
- [x] **Duration Handling** - Proper millisecond storage and hh:mm:ss.ff display formatting
- [ ] **TMM Integration** - Import content from TinyMediaManager .nfo files (planned)
- [ ] **Advanced Filtering** - Filter by source, type, rating, demographic (planned)
- [ ] **Scheduling Metadata** - Daypart preferences, seasonal targeting, content ratings (planned)

#### **2.3 Scheduling Engine** 🔄 **NEXT PHASE**
- [ ] **Schedule Manager** - Coarse (show-level) and fine (break-level) scheduling
- [ ] **Program Director** - Orchestrates channels and manages state
- [ ] **Channel Classes** - Independent broadcast units with pipelines
- [ ] **Timeline Editor** - Drag & drop scheduling interface

#### **2.4 Streaming Integration** 🔄 **NEXT PHASE**
- [ ] **Pipeline Manager** - Controls playback transitions and timing
- [ ] **Multi-channel Support** - Run multiple streams simultaneously
- [ ] **Emergency System** - Priority alert injection across channels
- [ ] **Schedule-to-Stream** - Convert schedules to live streams

### **Phase 3 — Advanced Features**
- [ ] **Graphics Overlay Engine** - Bugs, lower thirds, branding
- [ ] **Advanced Scheduling** - Commercials, bumpers, promos, live events
- [ ] **Plex Live TV Integration** - Native Plex channel support
- [ ] **Professional Features** - Closed captions, multiple audio tracks

---

## 🏗️ **Implementation Strategy**

### **Why Media-First Approach?**
1. **Content drives scheduling** - You need media to schedule before you can build a scheduler
2. **Metadata informs decisions** - Runtime, commercial breaks, content type all affect scheduling
3. **User workflow is content-centric** - "Schedule this show" vs "Fill this time slot"
4. **Validation requirements** - Need to verify media files work before scheduling them

### **Data Flow Architecture**
```
Media Files → Content Manager → Database → Schedule Manager → Program Director → Streaming Pipeline
     ↑              ↑              ↑              ↑              ↑              ↑
   File System   Metadata      SQLite DB    Timeline UI    Channel Mgr    FFmpeg
```

### **Component Dependencies**
- **Content Manager** ← Independent (can build first)
- **Database Schema** ← Needed by Content Manager  
- **Media Browser UI** ← Depends on Content Manager + Database
- **Schedule Manager** ← Depends on Database + Media metadata
- **Program Director** ← Depends on Schedule Manager
- **Streaming Pipeline** ← Depends on Program Director

---

## 🗄️ **Database Schema Design**

### **Core Tables - Scheduling & Content Delivery Focus**
```sql
-- Content Library (Scheduling Metadata)
content_items (id, file_path, title, duration, content_type, source_type, created_at, updated_at)
content_scheduling_metadata (
    content_id, 
    daypart_preference,    -- morning, afternoon, evening, late_night
    seasonal_preference,   -- spring, summer, fall, winter, holiday
    content_rating,        -- G, PG, PG-13, R, Adult
    commercial_company,    -- For commercials: "Coca-Cola", "McDonald's"
    commercial_category,   -- For commercials: "food", "automotive", "retail"
    target_demographic,    -- "family", "adult", "children", "seniors"
    content_warnings,      -- "violence", "language", "adult_themes"
    scheduling_notes       -- Custom notes for schedulers
)

-- External Source Integration
content_sources (
    id, source_type, source_name, 
    plex_server_url, plex_token,  -- For Plex integration
    tmm_library_path,             -- For TinyMediaManager .nfo files
    last_sync_time, sync_enabled
)

-- Scheduling
channels (id, name, description, target_demographic, content_rating_limit, enabled, created_at)
schedules (id, channel_id, start_time, end_time, content_id, schedule_type, priority)
playout_logs (id, channel_id, content_id, start_time, end_time, status, errors, actual_duration)

-- System Configuration
system_config (key, value, description)
emergency_alerts (id, message, priority, start_time, end_time, channels)
```

### **Key Design Decisions - Scheduling-First Approach**
1. **Content-centric** - All scheduling references content items by ID
2. **Scheduling metadata** - Daypart, seasonal, demographic, rating preferences
3. **External source integration** - Plex API + TinyMediaManager .nfo files
4. **Content delivery focus** - Commercial company, target audience, content warnings
5. **Audit trail** - Complete playout logging with actual vs scheduled duration
6. **Multi-channel ready** - Channel abstraction with demographic targeting

---

## 🎛️ **UI Architecture Strategy**

### **Desktop Application Structure**
```
Retrovue Manager (PySide6)
├── Media Browser Tab
│   ├── File tree view (Plex/TMM integration)
│   ├── Metadata editor (title, runtime, commercial breaks)
│   └── Preview player
├── Schedule Editor Tab  
│   ├── Timeline view (drag & drop scheduling)
│   ├── Channel selector
│   └── Schedule validation
└── Monitor Tab
    ├── Live stream status
    ├── Error logs
    └── Performance metrics
```

### **UI Development Approach**
1. **Start with Content Import** - Import from Plex/TMM, validate data flow
2. **Add Content Browser** - Browse imported content with scheduling metadata
3. **Add Schedule Editor** - Builds on established content library
4. **Finish with Monitor** - Real-time system status and debugging

---

## 📥 **Content Import Strategy**

### **External Source Integration**
```
Plex API → Content Items + Basic Metadata
TMM .nfo → Content Items + Rich Metadata + Scheduling Preferences
Manual Entry → Content Items + Custom Scheduling Metadata
```

### **Import Process Flow**
1. **Plex Integration**
   - Connect to Plex server via API
   - Import movies/shows with basic metadata (title, duration, rating)
   - Map Plex ratings to content_rating (G, PG, PG-13, R, Adult)
   - Set default scheduling preferences based on content type

2. **TinyMediaManager Integration**
   - Scan directories for .nfo files
   - Parse XML metadata (title, plot, genre, custom fields)
   - Extract scheduling-specific metadata from custom fields
   - Handle adult content metadata that won't be in Plex

3. **Commercial Content**
   - Manual entry for commercials without external metadata
   - Company, category, seasonal preferences
   - Daypart targeting (morning coffee, evening dinner, etc.)

### **Content Discovery UI**
```
Content Library Browser
├── Source Filter (Plex, TMM, Manual)
├── Content Type Filter (Movies, Shows, Commercials, Bumpers)
├── Scheduling Metadata Filter (Daypart, Season, Rating, Company)
├── Search & Sort (Title, Duration, Company, Last Used)
└── Bulk Edit (Update scheduling preferences, assign to channels)
```

---

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg installed and in PATH
- Plex Media Server (optional, for content import)
- TinyMediaManager .nfo files (optional, for content import)

### Running the Management Interface

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Launch the management interface
python run_ui.py
```

### Content Import Process
1. **Launch the UI** - Run `python run_ui_v2.py`
2. **Import Tab** - Import content from your sources:
   - **Plex Import**: Enter server URL and token, test connection, sync libraries
   - **Smart Sync**: Only updates changed content, handles multiple library conflicts
3. **Browser Tab** - View your imported content library with proper duration formatting
4. **Content Management**: Browse movies and TV shows with episode-level granularity

### Testing the Streaming Server

```bash
# Start the streaming server (simple loop mode - default)
python main.py

# Or use ErsatzTV-style concat mode
python main.py --mode concat

# Custom options
python main.py --mode concat --loops 10 --port 8081
```

### Testing the Stream
1. Open VLC Media Player
2. Go to: Media → Open Network Stream
3. Enter: `http://localhost:8080/channel/1.ts`
4. Click Play

The stream will loop seamlessly forever with proper timestamp handling.  

---

## 📁 Project Structure

```
Retrovue/
├── main.py                    # Main streaming server script
├── run_ui_v2.py              # Management interface launcher (v2)
├── requirements.txt           # Python dependencies
├── venv/                      # Python virtual environment
└── src/                      # Retrovue framework
    └── retrovue/
        ├── __init__.py
        ├── version.py
        ├── core/              # Core system components
        │   ├── __init__.py
        │   ├── streaming.py   # Streaming components
        │   ├── database_v2.py # Database management (v2 with migrations)
        │   └── plex_integration_v2.py  # Plex API integration (v2 with smart sync)
        └── ui/                # User interface components
            ├── __init__.py
            └── main_window_v2.py # PySide6 management interface (v2)
```

### Core Components
- **`streaming.py`**: FFmpeg-based streaming components
- **`database_v2.py`**: SQLite database with normalized schema and migrations
- **`plex_integration_v2.py`**: Smart Plex integration with conflict resolution and change detection

### User Interface
- **`main_window_v2.py`**: Complete PySide6 management interface with real-time progress updates
- **Import Tab**: Import content from Plex with smart sync capabilities
- **Browser Tab**: Browse imported content library with proper duration formatting

### Entry Points
- **`main.py`**: Streaming server (command-line interface)
- **`run_ui_v2.py`**: Management interface launcher (v2)

---

## 📋 Key Lessons (from early testing)
- VLC fails if opening `.m3u8` as a file → must serve via HTTP  
- Segments must not be deleted too aggressively → use `-hls_delete_threshold`  
- Use `-hls_start_number_source epoch` or timestamped filenames to avoid index reuse  
- Always re-encode with regular GOP/keyframes for clean segmenting  

---

## 🛠️ Tech Stack
- **Playback:** ffmpeg, Docker  
- **Management UI:** Python (PySide6 / Tkinter)  
- **Database:** SQLite (initial)  
- **Serving:** Python FastAPI / lightweight HTTP server  
- **Clients:** Plex Live TV, VLC  

---

## 🎉 **Current Status - Content Management Complete!**

### **✅ What's Working Now**
- **Content Management System** - Import, browse, and organize your media library
- **Plex Integration** - Import movies and TV shows from your Plex Media Server with episode-level granularity
- **Smart Sync** - Intelligent sync that only updates changed content, handles multiple library conflicts
- **Database Foundation** - SQLite database with normalized schema for media files, shows, episodes, and movies
- **Professional UI** - PySide6 management interface with real-time progress updates and proper duration formatting
- **Streaming Engine** - Working FFmpeg-based streaming with HLS output (basic single-channel)

### **❌ What's NOT Available Yet**
- **Scheduling System** - No timeline management or scheduling engine
- **Multi-source Support** - Only Plex integration works (TMM integration planned but not implemented)
- **Content Filtering** - Basic browsing only, no advanced filtering by metadata
- **Multi-channel Support** - Single channel streaming only
- **Program Director** - No orchestration or channel management
- **Graphics Overlays** - No bugs, lower thirds, or branding overlays
- **Emergency System** - No alert injection or priority overrides

### **🎯 Current Capabilities**
You can currently:
- ✅ **Import Content** - Sync movies and TV shows from Plex Media Server
- ✅ **Browse Library** - View imported content with proper duration formatting (hh:mm:ss.ff)
- ✅ **Basic Streaming** - Stream a single channel with simple content looping
- ✅ **Database Management** - Store and organize media metadata

### **🔄 What's Next - Scheduling & Multi-channel**
The next major development phases will focus on:
- **Schedule Manager** - Build timeline management and scheduling engine
- **Program Director** - Orchestrate multiple channels and manage state
- **Channel Classes** - Independent broadcast units with pipelines
- **Timeline Editor** - Drag & drop scheduling interface
- **Multi-channel Streaming** - Run multiple streams simultaneously
- **Schedule-to-Stream** - Convert schedules to live streams

**Current Status**: Content management foundation is solid. Ready to build the scheduling engine.

### **🐛 Known Issues - Progress Bar Behavior**
**Issue**: Dual progress bar system causing confusion during sync operations.
- **Main Progress Bar**: Shows overall sync progress (e.g., 6% when processing cartoons)
- **Episode Progress Bar**: Resets to 0-100% for each show's episode processing
- **Problem**: Two different progress tracking systems are running simultaneously, making it unclear which progress is being displayed
- **Impact**: User experience confusion during content sync operations
- **Status**: Identified but not yet resolved - needs architectural review of progress callback system

**Next Steps**: 
- Review progress callback architecture in `plex_integration.py`
- Consolidate to single progress tracking system
- Ensure clear progress indication for both overall sync and individual show processing

---

## 🎯 End Goal
Retrovue aims to be a **robust IPTV-ready simulation** of a professional broadcast television station:
- Multi-channel 24/7 operation  
- Realistic transitions and timing  
- Viewer experience **indistinguishable from real cable TV**  
- Easy-to-use management interface  
