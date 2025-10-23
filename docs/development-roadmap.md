# 🚦 Development Roadmap

This roadmap tracks our progress through development and helps keep us focused on bite-sized work chunks that move us towards the end goal of a robust IPTV system.

## 🎯 Project Vision

**End Goal**: A robust IPTV-ready simulation of a professional broadcast television station with multi-channel 24/7 operation, realistic transitions and timing, and a viewer experience indistinguishable from real cable TV.

## 📊 Current Status: CLI-First Plex Integration

### **Phase 1 — Proof of Concept** ✅ **COMPLETED**

- [x] Build single-channel playout (`ffmpeg → HLS → VLC`)
- [x] Solve segment rotation issues (`-hls_delete_threshold`, epoch numbering)
- [x] Validate continuous playback via local HTTP server

### **Phase 2 — CLI-First Plex Integration** ✅ **COMPLETED**

- [x] **Repository Cleanup** - Focused codebase with only plex_sync.py dependencies
- [x] **Complete CLI Interface** - Full command-line interface for all Plex operations
- [x] **Server Management** - Add, configure, and manage multiple Plex servers
- [x] **Library Synchronization** - Sync and manage Plex libraries with granular control
- [x] **Path Mapping System** - Translate Plex paths to accessible local file paths
- [x] **Content Ingestion** - Import movies and TV shows with full metadata
- [x] **Smart Synchronization** - Only update content that has actually changed

### **Phase 3 — Media-First Content Foundation** 🔄 **IN PROGRESS**

#### **Core Media-First Features** ✅ **IMPLEMENTED**

- [x] **Media-First Architecture**: Every record begins with a physical media file
- [x] **Content Items System**: Logical wrappers around media files with rich metadata
- [x] **Editorial Override System**: Customize metadata without overwriting source data
- [x] **Namespaced Tagging**: Structured tags for audience/holiday/brand-based scheduling
- [x] **Parental Control System**: MPAA/TV ratings with daypart restrictions

#### **Advanced Content Management** 🔄 **IN PROGRESS**

#### **2.1 Data Foundation** ✅ **COMPLETED**

- [x] **Database Schema Design** - Normalized schema for media files, shows, episodes, movies
- [x] **Content Manager** - Media ingestion, validation, metadata storage
- [x] **Plex Integration** - Import movies/shows from Plex Media Server via API with episode-level granularity
- [x] **Smart Sync System** - Intelligent sync with conflict resolution and change detection
- [x] **Content Import UI** - Web interface with real-time progress updates

#### **2.2 Plex Content Ingestion** ✅ **COMPLETED**

- [x] **Complete Plex Integration** - Full CLI-based Plex server management and content import
- [x] **Episode-Level Granularity** - Each TV episode stored separately for precise scheduling
- [x] **Smart Synchronization** - Only update content that has actually changed (10-50x performance improvement)
- [x] **Progress Tracking** - Real-time updates during import operations
- [x] **Multi-Server Support** - Manage multiple Plex servers from one Retrovue installation
- [x] **CLI Interface** - Complete command-line interface for all Plex operations
- [x] **Database Migrations** - Schema updates without data loss
- [x] **Library Management** - Store library names as media file attributes
- [x] **Duration Handling** - Proper millisecond storage and hh:mm:ss.ff display formatting
- [x] **Path Mapping System** - Translate Plex internal paths to accessible local file paths
- [x] **Server Management** - Add, delete, update, and configure Plex servers
- [x] **Content Ingestion** - Full and incremental content import with dry-run support

#### **2.3 Content Management System** 🔄 **NEXT PHASE**

- [x] **Path Mapping System** - Translate Plex internal paths to accessible file paths (COMPLETED)
- [ ] **Content Validation** - Verify media files are playable, check codec support, validate metadata
- [ ] **Error Handling & Recovery** - Robust error handling with retry logic and recovery strategies
- [ ] **Background Sync Service** - Automated synchronization with configurable intervals
- [ ] **State Management** - Track content states (Normal, RemoteOnly, Unavailable, FileNotFound)
- [ ] **Advanced Metadata Sync** - Comprehensive metadata including artwork, subtitles, chapters
- [ ] **Cleanup Operations** - Remove orphaned items, archive removed content
- [ ] **Performance Monitoring** - Track sync performance, error rates, and system health

#### **2.4 User Interface & Experience** 🔄 **NEXT PHASE**

- [ ] **Menu Bar Structure** - File menu (About, Settings, Quit) and Utilities menu (Sync Media)
- [ ] **Main Window Content List** - Display all media data with Edit Metadata button and modal popup
- [ ] **Content Type Handling** - Support for Movies, TV Shows, Commercials, Bumpers, Intros/Outros, Interstitials
- [ ] **Advanced Metadata Editor** - Media player, chapter markers, and Plex metadata display (read-only)
- [ ] **Configuration Management** - Centralized settings for sync intervals, path mappings, error handling
- [ ] **Selective Sync System** - Choose to sync ALL sources or select specific Plex libraries
- [ ] **Advanced Filtering** - Filter by source, type, rating, demographic (planned)
- [ ] **Scheduling Metadata** - Daypart preferences, seasonal targeting, content ratings (planned)

#### **2.5 Multi-Source Content** 🔄 **FUTURE PHASE**

- [ ] **TMM Directory Management** - Configure list of directories containing TMM .nfo files (with subdirectory support)
- [ ] **TMM Integration** - Import content from TinyMediaManager .nfo files (depends on directory management)
- [ ] **Jellyfin Integration** - Support for Jellyfin media servers
- [ ] **Emby Integration** - Support for Emby media servers
- [ ] **Local File System** - Direct import from local directories
- [ ] **Unified Content Model** - Consistent interface across all content sources

### **Phase 3 — Advanced Scheduling Engine** 🔄 **IN PROGRESS**

#### **Schedule Blocks & Instances** 🔄 **IN PROGRESS**

- [ ] **Schedule Blocks**: High-level programming templates (e.g., "Sitcoms at 5pm weekdays")
- [ ] **Schedule Instances**: Specific content scheduled for exact date/time combinations
- [ ] **Daypart Rules**: Different programming for morning, afternoon, evening, late night
- [ ] **Rotation Rules**: Prevent content from repeating too frequently
- [ ] **Commercial Spacing Rules**: Control commercial placement and brand separation

#### **Advanced Scheduling Features** 🔄 **PLANNED**

- [ ] **Auto-Fill Scheduling**: System automatically selects content based on rules
- [ ] **Tag-Based Selection**: Content selection based on namespaced tags
- [ ] **Rating Compliance**: Automatic content filtering based on parental ratings
- [ ] **Seasonal Programming**: Automatic seasonal content scheduling
- [ ] **Approval Workflow**: Schedule review and approval process

### **Phase 4 — Advanced Streaming & Playback** 🔄 **PLANNED**

#### **Ad Break Management** 🔄 **IN PROGRESS**

- [ ] **Media Markers**: Store ad breaks, chapters, and cue points
- [ ] **Chapter Integration**: Automatic ad break detection from video chapters
- [ ] **Manual Ad Break Input**: Custom ad break placement and timing
- [ ] **Commercial Insertion**: Seamless commercial insertion during playback

#### **EPG/Guide Data Export** 🔄 **PLANNED**

- [ ] **Plex Live TV Integration**: Export EPG data for Plex Live TV
- [ ] **Prevue Channel Output**: Generate program guide data for Prevue-style channels
- [ ] **Real-time Updates**: Guide data updates automatically as schedules change
- [ ] **Standard Formats**: Industry-standard EPG formats for maximum compatibility

#### **Play Log & Analytics** 🔄 **PLANNED**

- [ ] **Play Log Tracking**: Records what programs and ads actually aired
- [ ] **Weekly Log Rotation**: Automatic log management to prevent database bloat
- [ ] **Performance Metrics**: Track system performance and resource usage
- [ ] **Error Logging**: Record playback errors, missing files, and technical issues

### **Phase 5 — Multi-Channel & Advanced Features** 🔄 **FUTURE PHASE**

#### **Multi-Channel Support** 🔄 **PLANNED**

- [ ] **Multiple Channels**: Run multiple TV channels simultaneously
- [ ] **Channel Management**: Independent channel scheduling and control
- [ ] **Emergency System**: Priority alert injection across all channels
- [ ] **Resource Management**: CPU and memory allocation per channel

#### **Professional Features** 🔄 **FUTURE PHASE**

- [ ] **Graphics Overlay Engine**: Bugs, lower thirds, branding
- [ ] **Advanced Scheduling**: Commercials, bumpers, promos, live events
- [ ] **Campaign Management**: Ad campaign and flight window support
- [ ] **Quality Control**: Optional QC checks and validation
- [ ] **Professional Features**: Closed captions, multiple audio tracks

#### **Advanced Detection & Automation** 🔄 **FUTURE PHASE**

- [ ] **Auto Ad Break Detection**: Black frame and loudness detection
- [ ] **Cue-Based Overlays**: Logo bugs and graphics at specific cue points
- [ ] **Smart Content Selection**: AI-powered content recommendation
- [ ] **Automated Scheduling**: Machine learning-based schedule optimization

## 🎯 Current Focus: Plex Content Ingestion Enhancement

### **Immediate Next Steps (Priority Order)**

#### **1. Path Mapping System** 🚨 **CRITICAL**

**Why**: Required before streaming integration can work
**What**: Translate Plex internal paths to accessible file paths
**Status**: Partially implemented, needs completion
**Estimated Time**: 2-3 hours

#### **2. Content Validation System** 🚨 **HIGH PRIORITY**

**Why**: Ensure all imported content is playable before scheduling
**What**: Verify media files are accessible, check codec support, validate metadata
**Status**: Not started
**Estimated Time**: 4-6 hours

#### **3. Error Handling & Recovery** 🚨 **HIGH PRIORITY**

**Why**: Robust content ingestion requires proper error handling
**What**: Retry logic, error classification, recovery strategies, detailed logging
**Status**: Basic error handling exists, needs enhancement
**Estimated Time**: 6-8 hours

#### **4. Background Sync Service**

**Why**: Automated synchronization for production use
**What**: Scheduled sync operations, configurable intervals, service management
**Status**: Not started
**Estimated Time**: 8-10 hours

#### **5. State Management System**

**Why**: Track content availability and health
**What**: Normal, RemoteOnly, Unavailable, FileNotFound states with transitions
**Status**: Not started
**Estimated Time**: 4-6 hours

### **Medium-Term Goals (Next 2-4 weeks)**

#### **Advanced Metadata Synchronization**

- Comprehensive metadata sync (artwork, subtitles, chapters)
- Relationship management (actors, genres, studios)
- Metadata validation and consistency checks
- Artwork download and caching system

#### **Performance Monitoring & Analytics**

- Track sync performance metrics
- Monitor error rates and system health
- Performance optimization recommendations
- Detailed logging and audit trails

#### **Cleanup & Maintenance Operations**

- Remove orphaned items no longer in Plex
- Archive removed content for potential recovery
- Database optimization and maintenance
- Automated cleanup scheduling

### **Long-Term Goals (Next 1-2 months)**

#### **Multi-Source Content Integration**

- TMM Integration - Parse .nfo files for rich metadata
- Jellyfin Integration - Support for Jellyfin media servers
- Emby Integration - Support for Emby media servers
- Local File System - Direct import from local directories
- Unified Content Model - Consistent interface across all sources

#### **Professional UI & Experience**

- Menu Bar Structure - File menu (About, Settings, Quit) and Utilities menu
- Main Window Content List - Display all media data with Edit Metadata button
- Advanced Metadata Editor - Media player, chapter markers, Plex metadata display
- Configuration Management - Centralized settings for all sync operations

#### **Scheduling Engine Foundation**

- Timeline management system preparation
- Content type handling (Movies, TV Shows, Commercials, Bumpers, etc.)
- Scheduling metadata (daypart preferences, seasonal targeting, content ratings)
- Advanced filtering and content selection

## 🏗️ Implementation Strategy

### **Why Content Management First?**

1. **Content drives scheduling** - You need reliable media to schedule before you can build a scheduler
2. **Metadata informs decisions** - Runtime, commercial breaks, content type all affect scheduling
3. **User workflow is content-centric** - "Schedule this show" vs "Fill this time slot"
4. **Validation requirements** - Need to verify media files work before scheduling them
5. **Foundation for scaling** - Robust content management supports future multi-source integration

### **Content Management Data Flow**

```
Plex Server → Plex Integration → Content Validation → Database → Content Browser → Scheduling Engine
     ↑              ↑                    ↑              ↑              ↑              ↑
   API Calls    Metadata Sync      File Validation   SQLite DB    UI Management   Future Phase
```

### **Component Dependencies**

- **Plex Integration** ← Independent (can build first)
- **Database Schema** ← Needed by Plex Integration
- **🚨 Path Mapping System** ← CRITICAL: Required before streaming integration
- **Content Validation** ← Depends on Path Mapping System
- **Error Handling** ← Depends on Content Validation
- **Background Sync Service** ← Depends on Error Handling
- **State Management** ← Depends on Background Sync Service
- **Scheduling Engine** ← Depends on State Management (Future Phase)
- **Streaming Pipeline** ← Depends on Scheduling Engine (Future Phase)

## 📈 Success Metrics

### **Phase 2.2 Completion Criteria (Plex Content Ingestion)**

- [ ] Path mapping system fully functional
- [ ] Content validation system operational
- [ ] Error handling & recovery system robust
- [ ] Background sync service automated
- [ ] State management system tracking content health
- [ ] Performance monitoring and analytics working

### **Phase 2.3 Completion Criteria (Content Management System)**

- [ ] Advanced metadata synchronization complete
- [ ] Cleanup & maintenance operations automated
- [ ] Performance monitoring providing actionable insights
- [ ] All media files accessible and playable
- [ ] Database schema optimized for scheduling requirements

### **Phase 3 Readiness Criteria (Scheduling Engine)**

- [ ] Content management system complete and stable
- [ ] Multi-source content integration working
- [ ] Professional UI & experience implemented
- [ ] Scheduling metadata system ready
- [ ] All content validated and ready for scheduling

## 🎯 Next Work Session Focus

**Recommended Next Steps**:

1. **Complete Path Mapping System** - Critical for streaming integration
2. **Implement Content Validation System** - Ensure all content is playable
3. **Enhance Error Handling & Recovery** - Robust content ingestion

**Estimated Time**: 12-17 hours total
**Expected Outcome**: Production-ready content management system with reliable Plex integration

## 📝 Notes

- **Current Status**: Basic Plex integration working, focusing on production-grade reliability
- **Key Achievement**: Smart sync system with 10-50x performance improvement
- **Next Milestone**: Complete content management foundation before moving to scheduling
- **Risk Mitigation**: Path mapping and content validation are critical path items
- **Strategic Focus**: Building enterprise-grade content management to support future TV simulation features
