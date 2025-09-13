# 🏗️ System Architecture

## 🎯 Core Design Principles

### **Media-First Architecture**
Retrovue is built on a **media-first foundation** where every record begins with a physical media file. This approach ensures that:
- **Physical Reality**: All content must have an actual playable media file as its foundation
- **Logical Wrappers**: Content items (movies, episodes, bumpers, commercials, etc.) are logical wrappers around media files
- **Metadata Layering**: Rich metadata is layered on top of the media file without modifying the original
- **Playback Guarantee**: Every scheduled item can be played because it has a verified media file

### **Editorial Override System**
The system supports **editorial overrides** that allow customization without overwriting source metadata:
- **Source Preservation**: Original Plex/TMM metadata remains intact and accessible
- **Customization Layer**: Editorial changes are stored separately and take precedence during scheduling
- **Flexible Editing**: Users can modify titles, descriptions, ratings, and other metadata without losing source data
- **Audit Trail**: All editorial changes are tracked with timestamps and user attribution

### **Namespaced Tagging System**
Content is organized using **namespaced tags** that drive scheduling and ad targeting:
- **Structured Organization**: Tags follow `namespace:value` format (e.g., `audience:kids`, `holiday:christmas`, `brand:fast_food`)
- **Flexible Targeting**: Multiple tag namespaces allow complex scheduling rules and ad targeting
- **Hierarchical Control**: Tags can be combined for sophisticated content selection and scheduling
- **Extensible Design**: New namespaces can be added without schema changes

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

### **1. Ingestion System**
The **Ingestion System** is responsible for bringing content into Retrovue from Plex Media Server:

#### **Primary Metadata Source**
- **Plex Integration**: Automatically imports movies, TV shows, and metadata from Plex Media Server via the Plex Sync CLI

#### **Path Mapping Resolution**
- **Plex Path Translation**: Converts Plex internal paths to accessible local file paths
- **Cross-Platform Support**: Handles Windows, macOS, and Linux path differences
- **Storage Validation**: Ensures all mapped paths point to accessible media files
- **Longest Prefix Matching**: Uses efficient path resolution with cached mappings

#### **Content Validation**
- **File Accessibility**: Verifies that all media files can be opened and played
- **Codec Support**: Validates that media files use supported video/audio codecs
- **Metadata Integrity**: Checks that imported metadata is complete and consistent
- **Error Recovery**: Handles missing files, corrupted metadata, and sync failures

### **2. Metadata Management System**
The **Metadata Management System** stores and organizes all content information:

#### **Content Items Storage**
- **Primary Metadata**: Stored in `content_items` table with core information
- **Editorial Overrides**: Stored in `content_editorial` table for custom modifications
- **Source Preservation**: Original Plex/TMM metadata remains intact and accessible
- **Version Control**: Tracks changes and maintains metadata history

#### **Namespaced Tagging System**
- **Structured Tags**: Uses `namespace:value` format for organized content classification
- **Audience Targeting**: Tags like `audience:kids`, `audience:adult`, `audience:family`
- **Seasonal Content**: Tags like `holiday:christmas`, `holiday:halloween`, `season:summer`
- **Brand Management**: Tags like `brand:fast_food`, `brand:automotive`, `brand:retail`
- **Content Tone**: Tags like `tone:comedy`, `tone:drama`, `tone:action`, `tone:educational`

#### **Parental Control System**
- **MPAA Ratings**: Movie ratings (G, PG, PG-13, R, NC-17)
- **TV Ratings**: Television content ratings (TV-Y, TV-Y7, TV-G, TV-PG, TV-14, TV-MA)
- **Custom Ratings**: User-defined rating systems for specialized content
- **Daypart Restrictions**: Automatic content filtering based on time of day and audience

### **3. Scheduling Engine**
The **Scheduling Engine** manages when and how content is broadcast:

#### **Schedule Blocks (Templates)**
- **High-Level Rules**: Define programming patterns like "Sitcoms at 5pm weekdays"
- **Day-of-Week Rules**: Specify different programming for different days
- **Time Window Management**: Define specific time slots for different content types
- **Rotation Policies**: Control how often content repeats and when

#### **Schedule Instances (Specific Events)**
- **Exact Scheduling**: Specific content scheduled for specific date/time combinations
- **Event Management**: Handle special programming, live events, and one-time broadcasts
- **Conflict Resolution**: Manage scheduling conflicts and overlapping content
- **Approval Workflow**: Require approval for schedule changes and special events

#### **Advanced Scheduling Features**
- **Daypart Rules**: Different programming for morning, afternoon, evening, late night
- **Rotation Rules**: Prevent content from repeating too frequently
- **Commercial Spacing Rules**: Control commercial placement and separation
- **Seasonal Programming**: Automatic seasonal content scheduling

### **4. Playback/Streaming Engine**
The **Playback/Streaming Engine** handles the actual content delivery:

#### **FFmpeg Integration**
- **HLS/TS Output**: Generates industry-standard HTTP Live Streaming segments
- **Real-time Processing**: Processes content in real-time for live streaming
- **Format Conversion**: Converts various input formats to streaming-compatible output
- **Quality Management**: Maintains consistent video/audio quality across all content

#### **Ad Break Management**
- **Media Markers**: Uses `media_markers` table to define ad break points
- **Chapter Integration**: Integrates with video chapter markers for automatic ad placement
- **Manual Override**: Allows manual ad break placement and timing
- **Detection Algorithms**: Future support for automatic ad break detection

#### **EPG/Guide Data Export**
- **Plex Live TV**: Exports Electronic Program Guide data for Plex Live TV integration
- **Prevue Channel**: Generates program guide data for Prevue-style channel information
- **Standard Formats**: Supports industry-standard EPG formats for maximum compatibility
- **Real-time Updates**: Updates guide data as schedules change

### **5. Logging and Analytics System**
The **Logging System** tracks what content is actually aired:

#### **Play Log Management**
- **Content Tracking**: Records what programs and ads actually aired
- **Timing Accuracy**: Tracks actual vs. scheduled timing for all content
- **Error Logging**: Records playback errors, missing files, and technical issues
- **Performance Metrics**: Tracks system performance and resource usage

#### **Weekly Rotation System**
- **Storage Management**: Automatically rotates logs weekly to prevent database bloat
- **Historical Data**: Maintains accessible historical data for analysis
- **Archive Strategy**: Archives old logs while keeping recent data readily available
- **Compliance Tracking**: Maintains records for regulatory and audit purposes

### **Program Director (Legacy Architecture)**
The **Program Director** serves as the top-level controller in the traditional broadcast architecture:

#### **Channel Orchestration**
- **Multi-Channel Management**: Orchestrates all channels and manages global state
- **Emergency Coordination**: Coordinates emergency alerts across all channels
- **System Monitoring**: Manages system-wide configuration and performance monitoring
- **Lifecycle Management**: Handles channel lifecycle (start, stop, restart, maintenance)

#### **Channel Management (Legacy)**
- **Independent Channels**: Each channel operates as an independent broadcast unit
- **Schedule Management**: Maintains coarse (show-level) and fine (break-level) scheduling
- **Pipeline Control**: Controls playback transitions, timing, and stream quality
- **Graphics Overlay**: Manages bugs, branding, emergency graphics, and lower thirds
- **Playback Pipeline**: Handles actual media playback and stream generation

#### **Shared Resources (Legacy)**
- **Content Distribution**: Ingests and validates assets, stores metadata, distributes to channels
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
