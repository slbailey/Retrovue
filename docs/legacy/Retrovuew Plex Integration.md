# 🎬 Plex Integration

> **Legacy Document** — Pre-Alembic version, retained for reference only.

## 📋 Getting Your Plex Token

Your Plex token is like a password that allows RetroVue to access your Plex server:

### **Step 1: Open Plex Web Interface**

- Go to `http://your-plex-server:32400/web`
- Log in with your Plex account

### **Step 2: Get Your Token**

- Press `F12` to open developer tools
- Go to the "Network" tab
- Refresh the page
- Look for any request to your Plex server
- In the request headers, find `X-Plex-Token`
- Copy the token value (long string of letters and numbers)

### **Step 3: Use the Token**

- Paste this token into RetroVue when adding your Plex server
- Keep this token secure - it provides access to your Plex server

## 🔄 Smart Synchronization System

### **Incremental Sync Strategy**

RetroVue implements a sophisticated incremental synchronization system that dramatically improves performance by only processing content that has actually changed in Plex since the last sync.

#### **Plex `updatedAt` Field Integration**

Every piece of content from Plex includes an `updatedAt` timestamp that indicates when the content was last modified. RetroVue leverages this field to implement intelligent incremental sync:

```python
# Database schema includes updated_at_plex field for all content types
shows.updated_at_plex TIMESTAMP     -- Last update from Plex
episodes.updated_at_plex TIMESTAMP  -- Last update from Plex
movies.updated_at_plex TIMESTAMP    -- Last update from Plex
```

#### **Incremental Sync Logic**

```python
# For each content item, check if it has changed
plex_updated_at = content.get('updatedAt')
db_updated_at_plex = db_content.get('updated_at_plex')

# Skip processing if content hasn't changed
if plex_updated_at and db_updated_at_plex and plex_updated_at == db_updated_at_plex:
    return False  # No changes, skip update
```

### **Multi-Level Synchronization**

#### **1. Show-Level Optimization**

```python
# Check if entire show has changed before processing episodes
if (db_show and plex_show_updated_at and
    db_show.get('updated_at_plex') and
    plex_show_updated_at == db_show.get('updated_at_plex')):
    continue  # Skip processing all episodes in this show
```

**Benefits:**

- **Massive Performance Gain**: If a show hasn't changed, skip processing all its episodes
- **Reduced API Calls**: No need to fetch episode data for unchanged shows
- **Faster Sync Times**: Dramatically reduces processing time for large libraries

#### **2. Episode-Level Optimization**

```python
# Check individual episodes for changes
if plex_episode_updated_at and db_episode_updated_at_plex and
   plex_episode_updated_at == db_episode_updated_at_plex:
    return False  # Skip this episode
```

**Benefits:**

- **Granular Control**: Only process episodes that actually changed
- **Accurate Change Detection**: Handles cases where only some episodes in a show changed
- **Efficient Database Updates**: Minimizes unnecessary database operations

#### **3. Movie-Level Optimization**

```python
# Check individual movies for changes
if plex_movie_updated_at and db_movie_updated_at_plex and
   plex_movie_updated_at == db_movie_updated_at_plex:
    return False  # Skip this movie
```

**Benefits:**

- **Movie Library Efficiency**: Skip unchanged movies in large movie libraries
- **Metadata Update Detection**: Only process movies with actual metadata changes
- **Consistent Performance**: Same optimization benefits as TV shows

### **Performance Impact**

#### **Before Incremental Sync**

```
Library with 17,000 episodes:
- Every sync: Process all 17,000 episodes
- Time: 15-20 minutes per sync
- Database operations: 17,000+ update checks
- API calls: Full episode data for every episode
```

#### **After Incremental Sync**

```
Library with 17,000 episodes:
- First sync: Process all 17,000 episodes (establish baseline)
- Subsequent syncs: Process only changed content (typically 0-50 episodes)
- Time: 30 seconds - 2 minutes per sync
- Database operations: Only for changed content
- API calls: Minimal, only for changed shows/episodes
```

## 🎯 Show Disambiguation Strategy

### **The Problem**

Many TV series have been remade or rebooted with the same title but different years:

- **Battlestar Galactica** (1978) - Original series
- **Battlestar Galactica** (2003) - Reboot series
- **Doctor Who** (1963) - Classic series
- **Doctor Who** (2005) - Revival series

### **The Solution**

RetroVue uses a **multi-layered disambiguation strategy**:

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

### **GUID Parsing Examples**

```python
# Plex GUID formats and their parsed equivalents
"com.plexapp.agents.thetvdb://12345"     → (tvdb, 12345)
"com.plexapp.agents.themoviedb://54321"  → (tmdb, 54321)
"imdb://tt0123456"                       → (imdb, tt0123456)
"plex://show/abcdef"                     → (plex, show/abcdef)
```

## 🛠️ CLI Usage Examples

### **Environment Setup**

```bash
# Set Plex connection details (or use command line arguments)
export PLEX_BASE_URL="http://127.0.0.1:32400"
export PLEX_TOKEN="your-plex-token-here"
export PLEX_TV_SECTION_KEY="1"  # Optional: specific TV section
```

### **Discover Shows**

```bash
# Discover all shows with a specific title
python -m retrovue discover --title "Battlestar Galactica"

# Discover specific year (1978 original series)
python -m retrovue discover --title "Battlestar Galactica" --year 1978

# Discover specific year (2003 reboot)
python -m retrovue discover --title "Battlestar Galactica" --year 2003
```

### **Sync Specific Shows**

```bash
# Sync the 1978 original series
python -m retrovue sync --title "Battlestar Galactica" --year 1978

# Sync the 2003 reboot series
python -m retrovue sync --title "Battlestar Galactica" --year 2003

# Sync all shows with the title (both series)
python -m retrovue sync --title "Battlestar Galactica"
```

### **Full Library Sync**

```bash
# Sync all libraries with progress tracking
python -m retrovue sync-all --page-size 200

# Dry run to see what would be synced
python -m retrovue sync-all --dry-run
```

### **CLI Options**

```bash
# Global options
--debug              # Enable debug logging
--dry-run            # Show what would be done without making changes
--db-path PATH       # Path to SQLite database file

# Plex connection options
--plex-url URL       # Plex server URL
--plex-token TOKEN   # Plex authentication token
--plex-section KEY   # Plex TV section key

# Examples with options
python -m retrovue discover --title "Battlestar Galactica" --year 1978 --debug
python -m retrovue sync --title "Battlestar Galactica" --year 2003 --dry-run
```

## 🔄 Path Mapping System

### **The Problem**

Plex stores media files using internal paths that may not be directly accessible to RetroVue's streaming engine. For example:

- **Plex Path**: `/media/movies/Action Movie (2023).mp4`
- **Local Path**: `R:\movies\Action Movie (2023).mp4`

### **The Solution**

RetroVue implements a comprehensive path mapping system that translates between Plex internal paths and accessible local paths.

#### **Database Schema**

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

#### **Path Mapping Service**

```python
class PlexPathMappingService:
    def get_local_path(self, plex_path: str) -> str:
        # Find the best matching path mapping
        # Use longest prefix matching for accuracy
        # Return the translated local path
```

#### **How It Works**

1. **Import Process** - Plex paths are stored in `plex_path` column, local paths in `file_path` column
2. **Path Mapping Service** - `PlexPathMappingService` handles all path conversions
3. **Database Integration** - `get_local_path_for_media_file()` uses the service for path resolution
4. **Streaming Ready** - FFmpeg can now access files using the correct local paths

## 📊 Progress Tracking Design Pattern

### **Progress Bar Structure**

- **Library Progress**: Shows overall library sync progress (e.g., "TV Shows (1/3)")
- **Item Progress**: Shows current item being processed within the current library/show

### **Progress Display Logic**

#### **For Movies:**

```
Item Progress: Movie Title (1/250)
Item Progress: Another Movie (2/250)
Item Progress: Yet Another Movie (3/250)
```

- Format: `Movie Title (current movie / total movies in library)`
- Progress tracks current movie being processed within the library

#### **For TV Shows:**

```
Item Progress: Show Name / Episode Title (1/124)
Item Progress: Show Name / Another Episode (2/124)
Item Progress: Show Name / Yet Another Episode (3/124)
```

- Format: `Show Name / Episode Title (current episode / total episodes in current show)`
- Progress tracks current episode being processed within the current show
- Uses Plex's `allLeaves` endpoint to get accurate episode counts

### **Status Message Behavior**

Status messages at the bottom **only appear when database changes occur**:

- `Status: Added movie: New Movie Title`
- `Status: Updated episode: Existing Episode Title`
- `Status: Removed episode: Deleted Episode Title`

**No status messages during scanning** when no changes are needed - keeps the interface clean and focused.

## 🔧 Error Handling & Fallbacks

### **Missing `updatedAt` Fields**

```python
# Handle cases where Plex doesn't provide updatedAt
if not plex_updated_at:
    # Process content normally (fallback to full comparison)
    return process_content()
```

### **Timestamp Mismatches**

```python
# Handle timestamp format differences
try:
    if plex_updated_at == db_updated_at_plex:
        return False  # Skip update
except:
    # Fallback to processing if comparison fails
    return process_content()
```

### **Network Issues**

- Automatic retry logic for failed API calls
- Graceful degradation when Plex server is unavailable
- Error logging and user notification
- Partial sync recovery

## 📈 Monitoring & Debugging

### **Sync Statistics**

- **Total Content**: Count of all content in library
- **Processed Content**: Count of content actually processed
- **Skipped Content**: Count of content skipped due to no changes
- **Performance Metrics**: Sync time, API calls, database operations

### **Debug Information**

```python
# Debug logging for sync operations
if debug_mode:
    print(f"Show {show_title}: {plex_updated_at} vs {db_updated_at_plex}")
    print(f"Episode {episode_title}: {plex_episode_updated_at} vs {db_episode_updated_at_plex}")
```

## 🎯 Benefits of Plex Integration

1. **Dramatic Performance Improvement**: 10-50x faster sync times for unchanged content
2. **Reduced Server Load**: Minimal API calls and database operations
3. **Accurate Change Detection**: Only processes content that actually changed
4. **Scalable Architecture**: Performance doesn't degrade with library size
5. **User Experience**: Fast, responsive sync operations
6. **Resource Efficiency**: Reduced CPU, memory, and network usage
7. **Reliable Operation**: Robust error handling and fallback mechanisms
8. **Professional Disambiguation**: Handles complex show identification scenarios
9. **Path Flexibility**: Works with any Plex server configuration
10. **Comprehensive Monitoring**: Full visibility into sync operations
