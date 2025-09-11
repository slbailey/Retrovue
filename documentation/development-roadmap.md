# 🚦 Development Roadmap

This roadmap tracks our progress through development and helps keep us focused on bite-sized work chunks that move us towards the end goal of a robust IPTV system.

## 🎯 Project Vision

**End Goal**: A robust IPTV-ready simulation of a professional broadcast television station with multi-channel 24/7 operation, realistic transitions and timing, and a viewer experience indistinguishable from real cable TV.

## 📊 Current Status: Phase 2 - Core System Architecture

### **Phase 1 — Proof of Concept** ✅ **COMPLETED**
- [x] Build single-channel playout (`ffmpeg → HLS → VLC`)
- [x] Solve segment rotation issues (`-hls_delete_threshold`, epoch numbering)
- [x] Validate continuous playback via local HTTP server

### **Phase 2 — Core System Architecture** 🔄 **IN PROGRESS**

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
- [ ] **🚨 CRITICAL: Path Mapping System** - Translate Plex internal paths to accessible file paths (REQUIRED for streaming)
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

## 🎯 Current Focus: Content Management Completion

### **Immediate Next Steps (Priority Order)**

#### **1. Path Mapping System** 🚨 **CRITICAL**
**Why**: Required before streaming integration can work
**What**: Translate Plex internal paths to accessible file paths
**Status**: Partially implemented, needs completion
**Estimated Time**: 2-3 hours

#### **2. Menu Bar Structure** 
**Why**: Professional UI foundation
**What**: File menu (About, Settings, Quit) and Utilities menu (Sync Media)
**Status**: Not started
**Estimated Time**: 1-2 hours

#### **3. Main Window Content List**
**Why**: Core content management interface
**What**: Display all media data with Edit Metadata button and modal popup
**Status**: Not started
**Estimated Time**: 3-4 hours

#### **4. Content Type Handling**
**Why**: Support for different TV network content types
**What**: Movies, TV Shows, Commercials, Bumpers, Intros/Outros, Interstitials
**Status**: Not started
**Estimated Time**: 2-3 hours

#### **5. Advanced Metadata Editor**
**Why**: Professional content editing capabilities
**What**: Media player, chapter markers, and Plex metadata display (read-only)
**Status**: Not started
**Estimated Time**: 4-6 hours

### **Medium-Term Goals (Next 2-4 weeks)**

#### **Content Validation System**
- Verify media files are playable
- Check codec support
- Validate metadata completeness
- Handle missing or corrupted files

#### **TMM Integration**
- Configure TMM directory management
- Parse .nfo files for rich metadata
- Handle adult content metadata
- Support for custom scheduling preferences

#### **Selective Sync System**
- Choose specific Plex libraries to sync
- Select specific TMM directories
- Sync history tracking
- Conflict resolution between sources

### **Long-Term Goals (Next 1-2 months)**

#### **Scheduling Engine**
- Timeline management system
- Drag-and-drop scheduling interface
- Multi-channel support
- Commercial break planning

#### **Program Director**
- Channel orchestration
- State management
- Emergency system integration
- Real-time monitoring

#### **Multi-Channel Streaming**
- Simultaneous channel operation
- Professional transitions
- HLS streaming optimization
- Client compatibility testing

## 🏗️ Implementation Strategy

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
- **🚨 Path Mapping System** ← CRITICAL: Required before streaming integration
- **Media Browser UI** ← Depends on Content Manager + Database
- **Schedule Manager** ← Depends on Database + Media metadata
- **Program Director** ← Depends on Schedule Manager
- **Streaming Pipeline** ← Depends on Program Director + Path Mapping System

## 📈 Success Metrics

### **Phase 2 Completion Criteria**
- [ ] All content types supported (Movies, TV Shows, Commercials, Bumpers, etc.)
- [ ] Complete metadata editing capabilities
- [ ] Path mapping system fully functional
- [ ] Content validation system operational
- [ ] TMM integration working
- [ ] Selective sync system implemented

### **Phase 3 Readiness Criteria**
- [ ] Content management system complete and stable
- [ ] All media files accessible and playable
- [ ] Metadata system supports scheduling requirements
- [ ] UI provides professional content management experience
- [ ] Database schema supports scheduling and streaming needs

## 🎯 Next Work Session Focus

**Recommended Next Steps**:
1. **Complete Path Mapping System** - Critical for streaming integration
2. **Implement Menu Bar Structure** - Professional UI foundation
3. **Build Main Window Content List** - Core content management interface

**Estimated Time**: 6-9 hours total
**Expected Outcome**: Professional content management interface with full metadata editing capabilities

## 📝 Notes

- **Current Status**: Content management foundation is solid, ready to build scheduling engine
- **Key Achievement**: Robust Plex integration with smart sync system
- **Next Milestone**: Complete content management system before moving to scheduling
- **Risk Mitigation**: Path mapping system is critical path item for streaming integration
