# 📡 Plex Sync CLI Reference

## 🎯 Overview

The **Plex Sync CLI** (`cli/plex_sync.py`) is the primary command-line interface for managing Plex Media Server integration with Retrovue. It provides comprehensive tools for server management, library synchronization, content ingestion, and path mapping configuration.

## 🚀 Quick Start

```bash
# Basic help
python -m cli.plex_sync --help

# List all available commands
python -m cli.plex_sync --help

# Get help for a specific command
python -m cli.plex_sync <command> --help
```

## 📋 Command Categories

### **Server Management**
- `servers` - Manage Plex server connections and authentication

### **Library Management** 
- `libraries` - Manage Plex libraries and sync settings
- `sync-libraries` - Control library synchronization

### **Content Operations**
- `ingest` - Import content from Plex to Retrovue database
- `preview-items` - Preview raw Plex data before import

### **Path Mapping**
- `list-mappings` - View path mappings for servers/libraries
- `add-mapping` - Add new path mappings
- `resolve-path` - Test path resolution

### **Testing & Debugging**
- `test-guid` - Test GUID parsing functionality
- `test-pathmap` - Test path mapping resolution
- `map-item` - Test content mapping from JSON

### **Status & Monitoring**
- `ingest-status` - View synchronization status

---

## 🔧 Server Management Commands

### **Add Plex Server**
```bash
python -m cli.plex_sync servers add \
  --db ./retrovue.db \
  --name "HomePlex" \
  --base-url "http://192.168.1.100:32400" \
  --token "your-plex-token-here"
```

**Options:**
- `--db TEXT` - Database path (default: `./retrovue.db`)
- `--name TEXT` - Server name (required)
- `--base-url TEXT` - Server base URL (required)
- `--token TEXT` - Authentication token (required)

### **List Plex Servers**
```bash
python -m cli.plex_sync servers list --db ./retrovue.db
```

**Output:**
```
[OK] Found 2 Plex servers:
ID   Name            Base URL                    Default
--------------------------------------------------------
1    HomePlex        http://192.168.1.100:32400  ✅
2    RemotePlex      http://plex.example.com     ❌
```

### **Delete Plex Server**
```bash
python -m cli.plex_sync servers delete --db ./retrovue.db --id 2
```

**Options:**
- `--db TEXT` - Database path
- `--id INTEGER` - Server ID to delete (required)

### **Update Server Token**
```bash
python -m cli.plex_sync servers update-token \
  --db ./retrovue.db \
  --id 1 \
  --token "new-plex-token-here"
```

**Options:**
- `--db TEXT` - Database path
- `--id INTEGER` - Server ID (required)
- `--token TEXT` - New authentication token (required)

### **Set Default Server**
```bash
python -m cli.plex_sync servers set-default \
  --db ./retrovue.db \
  --server-name "HomePlex"
```

**Options:**
- `--db TEXT` - Database path
- `--server-name TEXT` - Server name to set as default
- `--server-id INTEGER` - Server ID to set as default

---

## 📚 Library Management Commands

### **List Libraries**
```bash
python -m cli.plex_sync libraries list --db ./retrovue.db
```

**Options:**
- `--db TEXT` - Database path (default: `./retrovue.db`)
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)

**Output:**
```
Libraries (showing 14):
ID   Key    Title                Type     Sync  Last Full            Last Incr
------------------------------------------------------------------------------------------
1    18     Adult content        movie    OFF   Never                Never
2    22     Anime Movies         movie    OFF   Never                Never
9    21     Anime TV             show     OFF   Never                Never
10   6      Cartoons             show     OFF   Never                Never
3    5      Godzilla             movie    OFF   Never                Never
4    14     Horror               movie    OFF   Never                Never
5    16     Horror (4K)          movie    OFF   Never                Never
6    15     Kids Movies          movie    OFF   Never                Never
11   20     Kids TV Shows        show     OFF   Never                Never
12   19     MonsterVision        show     OFF   Never                Never
7    1      Movies               movie    OFF   Never                Never
8    17     Movies (4K)          movie    OFF   Never                Never
13   8      RetroTV              show     OFF   Never                Never
14   2      TV Shows             show     OFF   Never                Never
```

### **Sync Libraries from Plex**
```bash
python -m cli.plex_sync libraries sync-from-plex \
  --db ./retrovue.db \
  --enable-all
```

**Options:**
- `--db TEXT` - Database path
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)
- `--enable-all` - Enable sync for all imported libraries
- `--disable-all` - Disable sync for all imported libraries

**Output:**
```
INFO: Found 14 libraries
inserted=14 updated=0 unchanged=0 total=14
Enabled sync for 14 libraries
```

### **Enable/Disable Library Sync**
```bash
# Enable sync for specific library
python -m cli.plex_sync libraries tag \
  --db ./retrovue.db \
  --library-id 9 \
  --sync-enabled 1

# Disable sync for specific library
python -m cli.plex_sync libraries tag \
  --db ./retrovue.db \
  --library-id 9 \
  --sync-enabled 0
```

**Options:**
- `--db TEXT` - Database path
- `--library-id INTEGER` - Library ID to modify (required)
- `--sync-enabled {0|1}` - Enable (1) or disable (0) sync (required)

### **Bulk Enable/Disable All Libraries**
```bash
# Enable sync for all libraries
python -m cli.plex_sync libraries tag-all \
  --db ./retrovue.db \
  --sync-enabled 1

# Disable sync for all libraries
python -m cli.plex_sync libraries tag-none \
  --db ./retrovue.db
```

**Options:**
- `--db TEXT` - Database path
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)
- `--sync-enabled {0|1}` - Enable (1) or disable (0) sync (required for tag-all)

### **Delete Libraries**
```bash
# Delete specific library
python -m cli.plex_sync libraries delete \
  --db ./retrovue.db \
  --library-id 9

# Delete all libraries for a server
python -m cli.plex_sync libraries delete-all \
  --db ./retrovue.db \
  --yes
```

**Options:**
- `--db TEXT` - Database path
- `--library-id INTEGER` - Library ID to delete (required for delete)
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)
- `--yes` - Confirm deletion (required for delete-all)

---

## 🔄 Sync Library Management Commands

### **List Sync Status**
```bash
python -m cli.plex_sync sync-libraries list --db ./retrovue.db
```

**Options:**
- `--db TEXT` - Database path
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)

### **Enable Library Sync**
```bash
python -m cli.plex_sync sync-libraries enable \
  --db ./retrovue.db \
  --library-id 9
```

**Options:**
- `--db TEXT` - Database path
- `--library-id INTEGER` - Library ID to enable (required)

### **Disable Library Sync**
```bash
python -m cli.plex_sync sync-libraries disable \
  --db ./retrovue.db \
  --library-id 9
```

**Options:**
- `--db TEXT` - Database path
- `--library-id INTEGER` - Library ID to disable (required)

---

## 📥 Content Ingestion Commands

### **Ingest Content from Plex**
```bash
# Full ingest (dry run)
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode full \
  --dry-run

# Full ingest (commit to database)
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode full \
  --commit

# Incremental ingest
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode incremental \
  --since-epoch 1640995200 \
  --commit
```

**Options:**
- `--db TEXT` - Database path (default: `./retrovue.db`)
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)
- `--mode TEXT` - Ingest mode: 'full' or 'incremental' (default: full)
- `--since-epoch INTEGER` - Manual since epoch for incremental mode
- `--libraries TEXT` - Comma-separated library IDs (default: all sync-enabled)
- `--kinds TEXT` - Comma-separated content kinds (default: movie,episode)
- `--limit INTEGER` - Maximum items per library
- `--batch-size INTEGER` - Batch size for commits (default: 50)
- `--dry-run` - Show planned inserts/updates only (default)
- `--commit` - Perform actual database writes
- `--verbose, -v` - Enable verbose output

**Output:**
```
Processing library 1 (movie) in full mode...
Library 1 (movie): 150 scanned, 150 mapped, 0 errors

Processing library 2 (episode) in full mode...
Library 2 (episode): 500 scanned, 500 mapped, 0 errors

=== FINAL SUMMARY ===
Total scanned: 650
Total mapped: 650
Total items: 650
Total files: 650
Total linked: 650
Total errors: 0

[COMMIT] Database writes completed successfully.
[OK] Ingest completed successfully.
```

### **Preview Raw Plex Items**
```bash
python -m cli.plex_sync preview-items \
  --db ./retrovue.db \
  --library-key 1 \
  --kind movie \
  --limit 5
```

**Options:**
- `--db TEXT` - Database path
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)
- `--library-key TEXT` - Library key (required)
- `--kind TEXT` - Content kind (movie, episode) (default: movie)
- `--limit INTEGER` - Number of items to preview (default: 5)

**Output:**
```
[OK] Found 5 movie items in library 1:
  1. The Matrix (ratingKey: 123, 136min, updated: 1640995200)
  2. Inception (ratingKey: 124, 148min, updated: 1640995200)
  3. Interstellar (ratingKey: 125, 169min, updated: 1640995200)
  4. The Dark Knight (ratingKey: 126, 152min, updated: 1640995200)
  5. Blade Runner 2049 (ratingKey: 127, 164min, updated: 1640995200)
```

### **Map Single Item**
```bash
# From JSON file
python -m cli.plex_sync map-item --from-json sample_movie.json

# From stdin
echo '{"title":"Test Movie","type":"movie","duration":7200000}' | python -m cli.plex_sync map-item --from-stdin
```

**Options:**
- `--from-json TEXT` - JSON file path
- `--from-stdin` - Read from stdin

**Output:**
```
[OK] Mapped: Test Movie (movie)
  Duration: 7200000 ms
  Rating: PG-13
```

---

## 🗺️ Path Mapping Commands

### **List Path Mappings**
```bash
python -m cli.plex_sync list-mappings \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1
```

**Options:**
- `--db TEXT` - Database path
- `--server-id INTEGER` - Server ID (default: 1)
- `--library-id INTEGER` - Library ID (default: 1)

**Output:**
```
[OK] Found 3 path mappings for server 1, library 1:
  /data/Movies -> C:\Media\Movies
  /data/TV -> C:\Media\TV
  /data/Anime -> C:\Media\Anime
```

### **Add Path Mapping**
```bash
python -m cli.plex_sync add-mapping \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-prefix "/data/Movies" \
  --local-prefix "C:\Media\Movies"
```

**Options:**
- `--db TEXT` - Database path
- `--server-id INTEGER` - Server ID (default: 1)
- `--library-id INTEGER` - Library ID (default: 1)
- `--plex-prefix TEXT` - Plex path prefix (required)
- `--local-prefix TEXT` - Local path prefix (required)

**Output:**
```
[OK] Added path mapping with ID 4:
  /data/Movies -> C:\Media\Movies
```

### **Resolve Path**
```bash
python -m cli.plex_sync resolve-path \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-path "/data/Movies/The Matrix (1999)/The Matrix (1999).mkv"
```

**Options:**
- `--db TEXT` - Database path
- `--server-id INTEGER` - Server ID (default: 1)
- `--library-id INTEGER` - Library ID (default: 1)
- `--plex-path TEXT` - Plex path to resolve (default: `/data/TV/Show/ep1.mkv`)

**Output:**
```
[OK] Resolved path: /data/Movies/The Matrix (1999)/The Matrix (1999).mkv -> C:\Media\Movies\The Matrix (1999)\The Matrix (1999).mkv
```

---

## 🧪 Testing & Debugging Commands

### **Test GUID Parsing**
```bash
python -m cli.plex_sync test-guid --guid "imdb://tt0133093"
```

**Options:**
- `--guid TEXT` - GUID string to parse

**Output:**
```
[OK] Parsed GUID: imdb://tt0133093
  imdb: 0133093
  raw: imdb://tt0133093
```

### **Test Path Mapping**
```bash
python -m cli.plex_sync test-pathmap \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-path "/data/Movies/Test.mkv"
```

**Options:**
- `--db TEXT` - Database path
- `--server-id INTEGER` - Server ID (default: 1)
- `--library-id INTEGER` - Library ID (default: 1)
- `--plex-path TEXT` - Plex path to test (default: `/data/TV/Show/ep1.mkv`)

**Output:**
```
[OK] Path mapping test:
  Plex: /data/Movies/Test.mkv
  Local: C:\Media\Movies\Test.mkv
```

---

## 📊 Status & Monitoring Commands

### **Show Ingest Status**
```bash
python -m cli.plex_sync ingest-status --db ./retrovue.db
```

**Options:**
- `--db TEXT` - Database path
- `--server-name TEXT` - Server name (from stored credentials)
- `--server-id INTEGER` - Server ID (from stored credentials)

**Output:**
```
Ingest Status (showing 14 libraries):
ID   Key    Title                Type     Sync  Last Full                Last Incr
------------------------------------------------------------------------------------
1    18     Adult content        movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
2    22     Anime Movies         movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
9    21     Anime TV             show     ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
10   6      Cartoons             show     ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
3    5      Godzilla             movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
4    14     Horror               movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
5    16     Horror (4K)          movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
6    15     Kids Movies          movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
11   20     Kids TV Shows        show     ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
12   19     MonsterVision        show     ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
7    1      Movies               movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
8    17     Movies (4K)          movie    ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
13   8      RetroTV              show     ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
14   2      TV Shows             show     ON    2024-01-15 14:30 (1642254600)  2024-01-15 16:45 (1642261500)
```

---

## 🔧 Common Workflows

### **Initial Setup**
```bash
# 1. Add Plex server
python -m cli.plex_sync servers add \
  --db ./retrovue.db \
  --name "HomePlex" \
  --base-url "http://192.168.1.100:32400" \
  --token "your-token"

# 2. Set as default
python -m cli.plex_sync servers set-default \
  --db ./retrovue.db \
  --server-name "HomePlex"

# 3. Sync libraries from Plex
python -m cli.plex_sync libraries sync-from-plex \
  --db ./retrovue.db \
  --enable-all

# 4. Configure path mappings
python -m cli.plex_sync add-mapping \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-prefix "/data/Movies" \
  --local-prefix "C:\Media\Movies"

# 5. Test path resolution
python -m cli.plex_sync resolve-path \
  --db ./retrovue.db \
  --server-id 1 \
  --library-id 1 \
  --plex-path "/data/Movies/Test.mkv"

# 6. Ingest content (dry run first)
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode full \
  --dry-run

# 7. Ingest content (commit)
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode full \
  --commit
```

### **Regular Maintenance**
```bash
# Check sync status
python -m cli.plex_sync ingest-status --db ./retrovue.db

# Incremental sync
python -m cli.plex_sync ingest \
  --db ./retrovue.db \
  --mode incremental \
  --commit

# Update server token if needed
python -m cli.plex_sync servers update-token \
  --db ./retrovue.db \
  --id 1 \
  --token "new-token"
```

### **Troubleshooting**
```bash
# Test server connection
python -m cli.plex_sync libraries list --db ./retrovue.db

# Test path mapping
python -m cli.plex_sync test-pathmap \
  --db ./retrovue.db \
  --plex-path "/data/Movies/Test.mkv"

# Preview raw Plex data
python -m cli.plex_sync preview-items \
  --db ./retrovue.db \
  --library-key 1 \
  --kind movie \
  --limit 1

# Test GUID parsing
python -m cli.plex_sync test-guid --guid "imdb://tt0133093"
```

---

## ⚠️ Error Handling

### **Common Error Codes**
- **Exit Code 1**: General error (check logs for details)
- **Exit Code 2**: Configuration error (server not found, invalid parameters)
- **Exit Code 3**: Network error (connection failed, authentication failed)

### **Authentication Errors**
```
[ERROR] Authentication failed (HTTP 401): Invalid token
```
**Solution**: Update server token using `servers update-token`

### **Connection Errors**
```
[ERROR] Connection failed: [Errno 111] Connection refused
```
**Solution**: Check server URL and ensure Plex server is running

### **Library Not Found**
```
[ERROR] Library 999 not found
```
**Solution**: Use `libraries list` to see available library IDs

### **Path Mapping Errors**
```
No mapping found for: /data/Movies/Test.mkv
```
**Solution**: Add path mapping using `add-mapping` command

---

## 📝 Best Practices

### **Database Management**
- Always use `--dry-run` before `--commit` for ingest operations
- Keep database backups before major operations
- Use incremental sync for regular updates

### **Path Mapping**
- Test path mappings with `resolve-path` before ingesting
- Use consistent path separators (forward slashes for Plex paths)
- Map the longest common prefix for efficiency

### **Server Management**
- Set a default server to avoid specifying `--server-name` repeatedly
- Store tokens securely and update them when they expire
- Use descriptive server names for multiple server setups

### **Performance**
- Use `--limit` for testing with large libraries
- Enable `--verbose` for debugging but disable for production
- Use incremental sync for regular updates instead of full sync

---

## 🔗 Related Documentation

- **[Quick Start Guide](quick-start.md)** - Step-by-step setup instructions
- **[Database Schema](database-schema.md)** - Understanding the data structure
- **[Architecture Overview](architecture.md)** - How the system works
- **[Development Roadmap](development-roadmap.md)** - Current status and future plans
