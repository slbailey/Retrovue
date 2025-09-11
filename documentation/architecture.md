# 🏗️ System Architecture

## 📐 Overall Architecture

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

## 🧩 Core Components

### **Program Director**
- Orchestrates all channels and manages global state
- Coordinates emergency alerts across all channels
- Manages system-wide configuration and monitoring
- Handles channel lifecycle (start, stop, restart)

### **Channel Management**
- **Channel**: Independent broadcast unit with its own schedule and pipeline
- **Schedule Manager**: Maintains coarse (show-level) and fine (break-level) scheduling logs
- **Pipeline Manager**: Controls playback transitions, timing, and stream quality
- **Graphics Manager**: Overlays bugs, branding, emergency graphics, and lower thirds
- **Playback Pipeline**: Handles actual media playback and stream generation

### **Shared Resources**
- **Content Manager**: Ingests and validates assets, stores metadata, distributes to channels
- **Emergency System**: Provides priority alert injection across all channels

## 🎛️ Playback Engine Architecture

### **Core Technology Stack**
- **FFmpeg**: Video processing, encoding, and HLS segment generation
- **HLS (HTTP Live Streaming)**: Industry-standard streaming protocol
- **Docker**: Containerized deployment for isolation and portability

### **Streaming Pipeline**
```
Media Files → FFmpeg → HLS Segments → HTTP Server → Client Players
     ↑           ↑           ↑            ↑            ↑
  Database   Encoding    .ts/.m4s     .m3u8        VLC/Plex
```

### **HLS Implementation**
- **Segments**: `.ts` or `fmp4` files with rotating `master.m3u8`
- **Segment Management**: `-hls_delete_threshold` for proper cleanup
- **Indexing**: `-hls_start_number_source epoch` to avoid index reuse
- **Quality**: Regular GOP/keyframes for clean segmenting

## 🖥️ Management UI Architecture

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

## 📂 Media & Metadata Strategy

### **Content Storage Philosophy**
- All existing media lives in **Plex** or is tagged with **TinyMediaManager** metadata
- Project stores only **playback-relevant metadata** (schedules, playout history, commercial timing)
- References series/episode metadata from Plex or sidecar files (avoid duplication)
- **Goal**: A **unified UI for editing scheduling metadata**, not a full media manager

### **Content Types**
- **Movies**: Feature films with commercial break planning
- **TV Shows**: Episodes with intro/outro timing
- **Commercials**: 15s, 30s, 60s spots with targeting
- **Bumpers**: Station IDs, "We'll be right back" segments
- **Intros/Outros**: Show openings and closings
- **Interstitials**: Filler content between shows

## 🔄 Data Flow Architecture

### **Content Processing Pipeline**
```
Media Files → Content Manager → Database → Schedule Manager → Program Director → Streaming Pipeline
     ↑              ↑              ↑              ↑              ↑              ↑
   File System   Metadata      SQLite DB    Timeline UI    Channel Mgr    FFmpeg
```

### **Component Dependencies**
- **Content Manager** ← Independent (can build first)
- **Database Schema** ← Needed by Content Manager  
- **Path Mapping System** ← CRITICAL: Required before streaming integration
- **Media Browser UI** ← Depends on Content Manager + Database
- **Schedule Manager** ← Depends on Database + Media metadata
- **Program Director** ← Depends on Schedule Manager
- **Streaming Pipeline** ← Depends on Program Director + Path Mapping System

## 🎯 Show Disambiguation Strategy

### **The Problem**
Many TV series have been remade or rebooted with the same title but different years:
- **Battlestar Galactica** (1978) - Original series
- **Battlestar Galactica** (2003) - Reboot series
- **Doctor Who** (1963) - Classic series
- **Doctor Who** (2005) - Revival series

### **The Solution**
Retrovue uses a **multi-layered disambiguation strategy**:

#### **1. Year-Based Disambiguation**
- **Primary Key**: `(title, year)` combination
- **Database Constraint**: `UNIQUE(title, year)` prevents duplicate shows
- **Example**: "Battlestar Galactica (1978)" vs "Battlestar Galactica (2003)"

#### **2. GUID-Based Identification**
- **External Identifiers**: TVDB, TMDB, IMDB, Plex internal GUIDs
- **Stable References**: GUIDs remain constant across Plex updates
- **Multiple GUIDs**: Each show can have multiple external identifiers
- **Priority Order**: TVDB > TMDB > IMDB > Plex (for primary GUID selection)

#### **3. Plex Rating Key Tracking**
- **Unique Identifier**: Plex's internal `ratingKey` for each show
- **Database Storage**: `plex_rating_key` field with unique constraint
- **Sync Reliability**: Ensures accurate updates and conflict resolution

## 🎬 Chapter Marker Strategy & Media Splitting

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

## 🛠️ Tech Stack

### **Core Technologies**
- **Playback**: FFmpeg, Docker
- **Management UI**: Python (PySide6 / Tkinter)
- **Database**: SQLite (initial)
- **Serving**: Python FastAPI / lightweight HTTP server
- **Clients**: Plex Live TV, VLC

### **Development Environment**
- **Python**: 3.8+
- **Virtual Environment**: venv for dependency isolation
- **Package Management**: pip with requirements.txt
- **Version Control**: Git with feature branch workflow

## 📋 Key Lessons (from early testing)
- VLC fails if opening `.m3u8` as a file → must serve via HTTP
- Segments must not be deleted too aggressively → use `-hls_delete_threshold`
- Use `-hls_start_number_source epoch` or timestamped filenames to avoid index reuse
- Always re-encode with regular GOP/keyframes for clean segmenting
