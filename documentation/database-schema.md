# 🗄️ Database Schema Design

## 📊 Core Tables - Scheduling & Content Delivery Focus

### **Media Files (Core Content Storage)**
```sql
media_files (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,           -- Local accessible file path
    plex_path TEXT,                    -- Plex internal path (for reference)
    duration INTEGER NOT NULL,         -- Duration in milliseconds
    media_type TEXT NOT NULL,          -- 'movie', 'episode', 'commercial', 'bumper', etc.
    source_type TEXT NOT NULL,         -- 'plex', 'tmm', 'manual'
    source_id TEXT,                    -- External source identifier
    library_name TEXT,                 -- Plex library name or TMM directory
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### **Movies (TV Network Content)**
```sql
movies (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    year INTEGER,
    rating TEXT,                       -- 'G', 'PG', 'PG-13', 'R', 'Adult', 'NR'
    summary TEXT,
    genre TEXT,
    director TEXT,
    plex_rating_key TEXT UNIQUE,       -- Plex's unique identifier
    updated_at_plex TIMESTAMP,         -- Last update from Plex
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
)
```

### **TV Shows**
```sql
shows (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER,                      -- Year for disambiguation
    total_seasons INTEGER,
    total_episodes INTEGER,
    show_rating TEXT,                  -- 'G', 'PG', 'PG-13', 'R', 'Adult', 'NR'
    show_summary TEXT,
    genre TEXT,
    source_type TEXT NOT NULL,         -- 'plex', 'tmm', 'manual'
    source_id TEXT,                    -- External source identifier
    plex_rating_key TEXT UNIQUE,       -- Plex's unique identifier
    updated_at_plex TIMESTAMP,         -- Last update from Plex
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, year)                -- Prevent duplicate shows
)
```

### **Episodes**
```sql
episodes (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    show_id INTEGER NOT NULL,
    episode_title TEXT NOT NULL,
    season_number INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    rating TEXT,                       -- 'G', 'PG', 'PG-13', 'R', 'Adult', 'NR'
    summary TEXT,
    plex_rating_key TEXT UNIQUE,       -- Plex's unique identifier
    updated_at_plex TIMESTAMP,         -- Last update from Plex
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id),
    FOREIGN KEY (show_id) REFERENCES shows(id)
)
```

### **Show GUIDs (External Identifiers)**
```sql
show_guids (
    id INTEGER PRIMARY KEY,
    show_id INTEGER NOT NULL,
    provider TEXT NOT NULL,            -- 'tvdb', 'tmdb', 'imdb', 'plex'
    external_id TEXT NOT NULL,         -- The actual ID from provider
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES shows(id),
    UNIQUE(provider, external_id)      -- Prevent duplicate GUIDs
)
```

### **Content Type Specific Metadata**
```sql
content_scheduling_metadata (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,        -- 'movie', 'tv_show', 'commercial', 'bumper', 'intro', 'outro', 'interstitial'
    daypart_preference TEXT,           -- 'morning', 'afternoon', 'evening', 'late_night'
    seasonal_preference TEXT,          -- 'spring', 'summer', 'fall', 'winter', 'holiday'
    content_rating TEXT,               -- 'G', 'PG', 'PG-13', 'R', 'Adult'
    commercial_company TEXT,           -- For commercials: "Coca-Cola", "McDonald's"
    commercial_category TEXT,          -- For commercials: "food", "automotive", "retail"
    commercial_duration INTEGER,       -- For commercials: 15, 30, 60 (seconds)
    commercial_expiration DATE,        -- For commercials: when to stop airing
    target_demographic TEXT,           -- "family", "adult", "children", "seniors"
    content_warnings TEXT,             -- "violence", "language", "adult_themes"
    scheduling_notes TEXT,             -- Custom notes for schedulers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
)
```

## 🔗 External Source Integration

### **Content Sources**
```sql
content_sources (
    id INTEGER PRIMARY KEY,
    source_type TEXT NOT NULL,         -- 'plex', 'tmm'
    source_name TEXT NOT NULL,         -- Human-readable name
    plex_server_url TEXT,              -- For Plex integration
    plex_token TEXT,                   -- For Plex integration
    last_sync_time TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### **Plex Path Mapping (CRITICAL for streaming)**
```sql
plex_path_mappings (
    id INTEGER PRIMARY KEY,
    plex_media_source_id INTEGER NOT NULL,
    plex_path TEXT NOT NULL,           -- "/media/movies" (Plex internal path)
    local_path TEXT NOT NULL,          -- "R:\movies" (accessible path)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plex_media_source_id) REFERENCES content_sources(id)
)
```

### **TMM Directory Management**
```sql
tmm_directories (
    id INTEGER PRIMARY KEY,
    directory_path TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    include_subdirectories BOOLEAN DEFAULT 1,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### **Sync History Tracking**
```sql
sync_history (
    id INTEGER PRIMARY KEY,
    source_type TEXT NOT NULL,         -- 'plex', 'tmm'
    source_name TEXT NOT NULL,
    sync_type TEXT NOT NULL,           -- 'full', 'incremental', 'selective'
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL,              -- 'running', 'completed', 'failed'
    items_processed INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_removed INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🎬 Chapter Markers & Media Processing

### **Chapter Markers**
```sql
chapter_markers (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    chapter_title TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL,     -- Timestamp in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
)
```

### **Commercial Break Scheduling**
```sql
commercial_breaks (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    chapter_marker_id INTEGER,         -- Optional: specific chapter marker
    commercial_content_id INTEGER,     -- Media file ID of commercial
    start_time INTEGER NOT NULL,       -- Start time in milliseconds
    end_time INTEGER NOT NULL,         -- End time in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id),
    FOREIGN KEY (chapter_marker_id) REFERENCES chapter_markers(id),
    FOREIGN KEY (commercial_content_id) REFERENCES media_files(id)
)
```

### **Generated Media Segments**
```sql
media_segments (
    id INTEGER PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    segment_path TEXT NOT NULL,
    start_time INTEGER NOT NULL,       -- Start time in milliseconds
    end_time INTEGER NOT NULL,         -- End time in milliseconds
    chapter_marker_id INTEGER,         -- Associated chapter marker
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id),
    FOREIGN KEY (chapter_marker_id) REFERENCES chapter_markers(id)
)
```

## 📺 Scheduling & Playout

### **Channels**
```sql
channels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    target_demographic TEXT,           -- "family", "adult", "children", "seniors"
    content_rating_limit TEXT,         -- "G", "PG", "PG-13", "R", "Adult"
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### **Schedules**
```sql
schedules (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    content_id INTEGER NOT NULL,       -- Media file ID
    schedule_type TEXT NOT NULL,       -- 'show', 'commercial', 'bumper', 'emergency'
    priority INTEGER DEFAULT 0,        -- Higher priority overrides lower
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id),
    FOREIGN KEY (content_id) REFERENCES media_files(id)
)
```

### **Playout Logs**
```sql
playout_logs (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    content_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL,              -- 'scheduled', 'playing', 'completed', 'failed'
    errors TEXT,                       -- Error messages if any
    actual_duration INTEGER,           -- Actual duration in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id),
    FOREIGN KEY (content_id) REFERENCES media_files(id)
)
```

## ⚙️ System Configuration

### **System Configuration**
```sql
system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### **Emergency Alerts**
```sql
emergency_alerts (
    id INTEGER PRIMARY KEY,
    message TEXT NOT NULL,
    priority INTEGER NOT NULL,         -- Higher priority overrides lower
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    channels TEXT,                     -- JSON array of channel IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🎯 Key Design Decisions - Scheduling-First Approach

### **1. Content-Centric Design**
- All scheduling references content items by ID
- Media files are the foundation of the entire system
- Content metadata drives scheduling decisions

### **2. Scheduling Metadata**
- Daypart preferences (morning, afternoon, evening, late night)
- Seasonal targeting (spring, summer, fall, winter, holiday)
- Demographic targeting (family, adult, children, seniors)
- Content rating system (G, PG, PG-13, R, Adult)

### **3. External Source Integration**
- Plex API integration with episode-level granularity
- TinyMediaManager .nfo file support
- Multiple source support with conflict resolution

### **4. Content Delivery Focus**
- Commercial company and category tracking
- Target audience and content warnings
- Commercial duration and expiration dates
- Scheduling notes for content creators

### **5. Audit Trail**
- Complete playout logging with actual vs scheduled duration
- Sync history tracking for all sources
- Error logging and status tracking
- Performance monitoring capabilities

### **6. Multi-Channel Ready**
- Channel abstraction with demographic targeting
- Independent channel scheduling
- Emergency alert system across all channels
- Scalable architecture for multiple simultaneous streams

## 🔄 Database Migrations

### **Migration Strategy**
- Automatic schema updates without data loss
- Version tracking for database schema
- Backward compatibility with existing data
- Safe migration rollback capabilities

### **Key Migration Examples**
```sql
-- Add updated_at_plex to episodes table
ALTER TABLE episodes ADD COLUMN updated_at_plex TIMESTAMP;

-- Add updated_at_plex to movies table  
ALTER TABLE movies ADD COLUMN updated_at_plex TIMESTAMP;

-- Add year-based disambiguation to shows table
ALTER TABLE shows ADD COLUMN year INTEGER;
CREATE UNIQUE INDEX idx_shows_title_year ON shows(title, year);
```

## 📊 Performance Considerations

### **Indexing Strategy**
- Primary keys on all tables
- Foreign key indexes for join performance
- Unique constraints for data integrity
- Composite indexes for common query patterns

### **Query Optimization**
- Normalized schema reduces data duplication
- Efficient joins between related tables
- Proper indexing for common access patterns
- Optimized queries for large library support

### **Scalability**
- SQLite for single-user deployment
- Schema designed for potential PostgreSQL migration
- Efficient pagination for large datasets
- Optimized sync operations for large libraries
