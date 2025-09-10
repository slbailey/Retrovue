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

#### **2.2 Content Management** 🔄 **IN PROGRESS**
- [x] **Content Browser UI** - Browse and organize content library with proper duration formatting
- [x] **Database Migrations** - Schema updates without data loss
- [x] **Library Management** - Store library names as media file attributes
- [x] **Duration Handling** - Proper millisecond storage and hh:mm:ss.ff display formatting
- [ ] **Menu Bar Structure** - File menu (About, Settings, Quit) and Utilities menu (Sync Media)
- [ ] **Main Window Content List** - Display all media data with Edit Metadata button and modal popup
- [ ] **Content Type Handling** - Support for Movies, TV Shows, Commercials, Bumpers, Intros/Outros, Interstitials
- [ ] **Advanced Metadata Editor** - Media player, chapter markers, and Plex metadata display (read-only)
- [ ] **Content Validation** - Verify media files are playable, check codec support, validate metadata
- [ ] **TMM Directory Management** - Configure list of directories containing TMM .nfo files (with subdirectory support)
- [ ] **Selective Sync System** - Choose to sync ALL sources or select specific Plex libraries and TMM directories
- [ ] **TMM Integration** - Import content from TinyMediaManager .nfo files (depends on directory management)
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
-- Media Files (Core Content Storage)
media_files (id, file_path, duration, media_type, source_type, source_id, library_name, created_at, updated_at)

-- Movies (TV Network Content)
movies (id, media_file_id, title, year, rating, summary, genre, director, created_at, updated_at)

-- TV Shows
shows (id, title, total_seasons, total_episodes, show_rating, show_summary, genre, source_type, source_id, created_at, updated_at)

-- Episodes
episodes (id, media_file_id, show_id, episode_title, season_number, episode_number, rating, summary, created_at, updated_at)

-- Content Type Specific Metadata
content_scheduling_metadata (
    id, media_file_id, content_type,  -- movie, tv_show, commercial, bumper, intro, outro, interstitial
    daypart_preference,    -- morning, afternoon, evening, late_night
    seasonal_preference,   -- spring, summer, fall, winter, holiday
    content_rating,        -- G, PG, PG-13, R, Adult
    commercial_company,    -- For commercials: "Coca-Cola", "McDonald's"
    commercial_category,   -- For commercials: "food", "automotive", "retail"
    commercial_duration,   -- For commercials: 15s, 30s, 60s
    commercial_expiration, -- For commercials: when to stop airing
    target_demographic,    -- "family", "adult", "children", "seniors"
    content_warnings,      -- "violence", "language", "adult_themes"
    scheduling_notes       -- Custom notes for schedulers
)

-- External Source Integration
content_sources (
    id, source_type, source_name, 
    plex_server_url, plex_token,  -- For Plex integration
    last_sync_time, sync_enabled
)

-- TMM Directory Management
tmm_directories (
    id, directory_path, name, description,
    include_subdirectories, enabled, created_at, updated_at
)

-- Sync History Tracking
sync_history (
    id, source_type, source_name, sync_type,
    start_time, end_time, status, items_processed, 
    items_added, items_updated, items_removed, error_message
)

-- Chapter Markers
chapter_markers (
    id, media_file_id, chapter_title, timestamp_ms,
    created_at, updated_at
)

-- Commercial Break Scheduling
commercial_breaks (
    id, media_file_id, chapter_marker_id, commercial_content_id,
    start_time, end_time, created_at, updated_at
)

-- Generated Media Segments
media_segments (
    id, media_file_id, segment_path, start_time, end_time,
    chapter_marker_id, created_at, updated_at
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
├── Menu Bar
│   ├── File Menu
│   │   ├── About (application info, version)
│   │   ├── Settings (opens settings dialog)
│   │   └── Quit (exit application)
│   └── Utilities Menu
│       └── Sync Media... (opens selective sync dialog)
├── Main Window (Default View)
│   ├── Content List (all media data from database)
│   ├── Row Selection (click to select media item)
│   ├── Edit Metadata Button (opens metadata editor modal)
│   └── Content Filtering (search, filter by type/source)
├── Advanced Metadata Editor Modal
│   ├── Media Player (top left) - Video playback with controls
│   ├── Chapter Markers (top right) - List of chapters with timestamps
│   ├── Chapter Controls (middle) - Add, Set Time, Delete, Generate buttons
│   ├── Plex Metadata Display (bottom) - Read-only Plex metadata fields
│   └── Save/Cancel buttons
├── Import/Sync Tab
│   ├── Source Selection (ALL, specific Plex libraries, specific TMM directories)
│   ├── Sync Progress (library-level and item-level progress)
│   └── Sync History (last sync times, results)
├── Schedule Editor Tab  
│   ├── Timeline view (drag & drop scheduling)
│   ├── Channel selector
│   └── Schedule validation
├── Settings Dialog
│   ├── Plex Settings (server URL, token)
│   └── TMM Directories (configure .nfo file locations)
└── Monitor Tab
    ├── Live stream status
    ├── Error logs
    └── Performance metrics
```

### **UI Development Approach**
1. **Menu Bar Foundation** - File menu (About, Settings, Quit) and Utilities menu (Sync Media)
2. **Main Window Content List** - Display all media data with Edit Metadata functionality
3. **Metadata Editor Modal** - Edit media metadata with full database integration
4. **Content Import** - Import from Plex/TMM, validate data flow
5. **Schedule Editor** - Builds on established content library
6. **Monitor** - Real-time system status and debugging

---

## 🖥️ **Main Window Content Management**

### **Primary Interface Design**
The main window serves as the central content management interface, displaying all media data from the database with full editing capabilities.

### **Content List Features**
- **Comprehensive Display** - Show all media files (movies, episodes) with key metadata
- **Row Selection** - Click any row to select a media item for editing
- **Edit Metadata Button** - Prominent button to open metadata editor for selected item
- **Content Filtering** - Search and filter by type, source, rating, etc.
- **Sortable Columns** - Sort by title, duration, type, source, last modified

### **Advanced Metadata Editor Modal**
- **Media Player (Top Left)** - Video playback window with standard controls (play/pause, volume, fullscreen)
- **Chapter Markers (Top Right)** - List of chapters with titles and timestamps, selectable rows
- **Chapter Controls (Middle)** - Buttons for chapter management:
  - **Add** - Add new chapter marker at current playhead position
  - **Set Time** - Update selected chapter time to current playhead position
  - **Delete** - Remove selected chapter marker
  - **Generate** - Auto-generate chapter markers from black space between frames
- **Content Type Selection** - Choose content type (Movie, TV Show, Commercial, Bumper, Intro/Outro, Interstitial)
- **Plex Metadata Display (Bottom)** - Read-only display of Plex metadata:
  - General: Title, Actors, Directors, Copyright
  - Production: Sort Name, Producers, Screenwriters, Studio, Comments
  - Media: Media Type, Definition, Rating, Advisory, iTunes Genre
  - Series: TV Series Name, Season, Episode, Episode ID, Cover Art
- **Save/Cancel** - Save chapter markers and content type to database or discard changes

### **User Workflow**
1. **Open Application** - Main window displays all content immediately
2. **Browse Content** - Scroll through or filter the content list
3. **Select Item** - Click on any row to select a media item
4. **Edit Metadata** - Click "Edit Metadata" button to open advanced editor modal
5. **Video Playback** - Use media player to navigate through content
6. **Chapter Management** - Add, modify, or delete chapter markers using controls
7. **View Plex Metadata** - Review read-only Plex metadata at bottom
8. **Save Changes** - Save chapter markers to database or discard changes

---

## 🎬 **Chapter Marker Strategy & Media Splitting**

### **Chapter Markers as Commercial Break Guidelines**
Chapter markers serve as **scheduling metadata** rather than embedded .mp4 chapter data:
- **Database-Only Storage** - Chapter markers stored in `chapter_markers` table, not in .mp4 files
- **Commercial Break Planning** - Markers indicate where commercials should be inserted during scheduling
- **Playback Flexibility** - Original .mp4 files remain unchanged, allowing multiple scheduling strategies

### **Media Splitting During Playback**
**Yes, we can still split media during playback** using several approaches:

#### **Option 1: FFmpeg Real-Time Splitting**
- **Stream Segmentation** - FFmpeg can split streams at specific timestamps without modifying source files
- **Command Example**: `ffmpeg -i input.mp4 -ss 00:02:15 -t 00:09:25 -c copy segment1.ts`
- **Benefits**: No file modification, real-time processing, multiple output formats
- **Use Case**: Live streaming with commercial insertion

#### **Option 2: Pre-Generated Segments**
- **Scheduled Processing** - Generate segments during off-peak hours based on chapter markers
- **Storage Strategy** - Store segments in database with chapter marker relationships
- **Benefits**: Faster playback, reduced server load, better quality control
- **Use Case**: Scheduled programming with known commercial breaks

#### **Option 3: Dynamic Playlist Generation**
- **HLS Playlist Manipulation** - Generate .m3u8 playlists that skip commercial segments
- **Chapter Marker Integration** - Use database markers to determine segment boundaries
- **Benefits**: Standard HLS compatibility, flexible commercial insertion
- **Use Case**: IPTV streaming with commercial management

### **Implementation Strategy**
1. **Chapter Marker Creation** - Users mark commercial break points in metadata editor
2. **Scheduling Integration** - Chapter markers inform where commercials should be inserted
3. **Playback Engine** - FFmpeg uses chapter marker timestamps for real-time splitting
4. **Commercial Insertion** - Replace marked segments with commercial content during streaming

### **Database Integration**
```sql
-- Chapter markers linked to media files
chapter_markers (id, media_file_id, chapter_title, timestamp_ms, created_at, updated_at)

-- Commercial break scheduling
commercial_breaks (id, media_file_id, chapter_marker_id, commercial_content_id, start_time, end_time)

-- Generated segments (for pre-processing approach)
media_segments (id, media_file_id, segment_path, start_time, end_time, chapter_marker_id)
```

---

## 📥 **Content Import Strategy**

### **External Source Integration**
```
Plex API → Content Items + Basic Metadata
TMM .nfo → Content Items + Rich Metadata + Scheduling Preferences
Manual Entry → Content Items + Custom Scheduling Metadata
```

### **Import Process Flow**
1. **Selective Sync Interface**
   - **Sync ALL** - Sync all configured Plex libraries and TMM directories
   - **Selective Sync** - Choose specific Plex libraries and/or TMM directories to sync
   - **Source Management** - View and manage configured sources before syncing
   - **Sync History** - Track last sync times and results for each source

2. **Plex Integration**
   - Connect to Plex server via API
   - **Library Selection** - Choose specific libraries or sync all available
   - Import movies/shows with basic metadata (title, duration, rating)
   - Map Plex ratings to content_rating (G, PG, PG-13, R, Adult)
   - Set default scheduling preferences based on content type

3. **TinyMediaManager Integration**
   - **TMM Directory Management** - Configure list of directories containing .nfo files (with subdirectory support)
   - **Directory Selection** - Choose specific TMM directories or sync all configured
   - Scan selected directories for .nfo files
   - Parse XML metadata (title, plot, genre, custom fields)
   - Extract scheduling-specific metadata from custom fields
   - Handle adult content metadata that won't be in Plex

4. **Commercial Content**
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
- **Menu Bar Structure** - No proper File/Utilities menu structure
- **Main Window Content Management** - No main window content list with Edit Metadata functionality
- **Content Type Handling** - No support for different TV network content types (Movies, Commercials, Bumpers, etc.)
- **Advanced Metadata Editor** - No media player, chapter markers, or Plex metadata display
- **Content Validation** - No verification of media file playability or codec support
- **Scheduling System** - No timeline management or scheduling engine
- **Selective Sync** - No ability to choose specific libraries/directories for sync
- **TMM Integration** - TMM directory management and .nfo file parsing not implemented
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
