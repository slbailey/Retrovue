# 📚 Content Management System

The Content Management System (CMS) is the core component responsible for discovering, ingesting, organizing, and managing media content in Retrovue. It provides both CLI and web interfaces for content operations and includes a sophisticated review system for quality assurance.

## 🎯 Business Purpose

The CMS serves as the foundation for all content operations in Retrovue:

- **Content Discovery**: Automatically find and catalog media files from various sources
- **Metadata Management**: Enrich content with technical and descriptive metadata
- **Quality Assurance**: Human review system for content validation
- **Library Organization**: Organize content into series, seasons, and episodes
- **Source Management**: Integrate with external sources like Plex servers

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Content Management System                │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface  │  Web Interface  │  API Endpoints        │
├─────────────────────────────────────────────────────────────┤
│                    Application Services                      │
├─────────────────────────────────────────────────────────────┤
│  IngestService  │  LibraryService  │  SourceService       │
├─────────────────────────────────────────────────────────────┤
│                    Domain Entities                          │
├─────────────────────────────────────────────────────────────┤
│  Asset  │  Episode  │  Title  │  ReviewQueue  │  Source   │
├─────────────────────────────────────────────────────────────┤
│                    External Integrations                    │
├─────────────────────────────────────────────────────────────┤
│  Plex API  │  Filesystem  │  FFProbe  │  Database         │
└─────────────────────────────────────────────────────────────┘
```

### Data Model Relationships

```
Title (Series/Movie)
├── Season (for series)
│   └── Episode
│       └── EpisodeAsset (many-to-many)
│           └── Asset
├── Source (Plex, filesystem)
└── ReviewQueue (quality assurance)
```

## 🔧 Technical Implementation

### 1. Core Services

#### IngestService

**Purpose**: Orchestrates content discovery and ingestion workflows

```python
class IngestService:
    def __init__(self, db: Session):
        self.db = db
        self.importer_registry = ImporterRegistry()
        self.enricher_registry = EnricherRegistry()

    def run_ingest(self, source: str) -> dict[str, int]:
        """Run complete ingestion workflow for a source."""
        # 1. Discover content using appropriate importer
        # 2. Enrich with metadata using enrichers
        # 3. Register assets in database
        # 4. Queue for review if needed
        pass
```

**Key Methods:**

- `run_ingest(source)`: Complete ingestion workflow
- `discover_content(source)`: Find content from source
- `enrich_asset(asset)`: Add metadata to asset
- `register_asset(asset)`: Save asset to database

#### LibraryService

**Purpose**: Manages the content library and review system

```python
class LibraryService:
    def __init__(self, db: Session):
        self.db = db

    def register_asset(self, uri: str, metadata: dict) -> Asset:
        """Register a new asset in the library."""
        pass

    def enqueue_review(self, asset_id: UUID, reason: str, confidence: float):
        """Queue an asset for human review."""
        pass

    def resolve_review(self, review_id: UUID, episode_id: UUID):
        """Resolve a review queue item."""
        pass
```

**Key Methods:**

- `list_assets()`: Get all assets in library
- `get_asset(asset_id)`: Get specific asset
- `enqueue_review()`: Queue asset for review
- `resolve_review()`: Complete review process

#### SourceService

**Purpose**: Manages external content sources

```python
class SourceService:
    def __init__(self, db: Session):
        self.db = db

    def register_source(self, name: str, type: str, config: dict) -> Source:
        """Register a new content source."""
        pass

    def list_sources(self) -> list[Source]:
        """List all configured sources."""
        pass
```

### 2. Domain Entities

#### Asset Entity

```python
class Asset(Base):
    """Represents a media file in the library."""

    id: UUID = Primary key
    uri: str = File path or URL
    size: int = File size in bytes
    duration_ms: Optional[int] = Duration in milliseconds
    video_codec: Optional[str] = Video codec
    audio_codec: Optional[str] = Audio codec
    container: Optional[str] = Container format
    canonical: bool = Whether this is the canonical version
    created_at: datetime = When asset was registered
    updated_at: datetime = Last modification time
```

#### Episode Entity

```python
class Episode(Base):
    """Represents an episode of a series or a movie."""

    id: UUID = Primary key
    title: str = Episode title
    season_number: Optional[int] = Season number (for series)
    episode_number: Optional[int] = Episode number
    title_id: UUID = Foreign key to Title
    created_at: datetime = When episode was created
```

#### ReviewQueue Entity

```python
class ReviewQueue(Base):
    """Items that need human review for quality assurance."""

    id: UUID = Primary key
    asset_id: UUID = Foreign key to assets table
    reason: str = Reason for review
    confidence: float = Confidence score (0.0-1.0)
    status: ReviewStatus = PENDING | RESOLVED | REJECTED
    created_at: datetime = When review was queued
    resolved_at: datetime = When review was completed
    notes: str = Resolution notes
```

### 3. External Integrations

#### Plex Integration

```python
class PlexImporter(BaseImporter):
    """Imports content from Plex server."""

    def discover_content(self, source: str) -> list[ContentItem]:
        """Discover content from Plex server."""
        # Connect to Plex API
        # Fetch libraries and items
        # Convert to ContentItem objects
        pass
```

#### Filesystem Integration

```python
class FilesystemImporter(BaseImporter):
    """Imports content from local filesystem."""

    def discover_content(self, source: str) -> list[ContentItem]:
        """Scan filesystem for media files."""
        # Recursively scan directory
        # Filter by media extensions
        # Return ContentItem objects
        pass
```

#### FFProbe Enricher

```python
class FFProbeEnricher(BaseEnricher):
    """Enriches assets with technical metadata using FFProbe."""

    def enrich(self, asset: Asset) -> dict[str, Any]:
        """Extract technical metadata from media file."""
        # Run FFProbe on file
        # Extract codec, duration, resolution info
        # Return metadata dictionary
        pass
```

## 🎮 User Interfaces

### 1. CLI Interface

#### Asset Management Commands

```bash
# List all assets
retrovue assets list

# Get asset details
retrovue assets show <asset_id>

# List assets with filters
retrovue assets list --canonical --format json
```

#### Ingest Commands

```bash
# Run ingestion from source
retrovue assets run <source_name>

# List available sources
retrovue assets sources

# Check ingest status
retrovue assets status
```

#### Review Commands

```bash
# List review queue
retrovue review list

# Resolve review item
retrovue review resolve <review_id> <episode_id>

# Reject review item
retrovue review reject <review_id>
```

### 2. Web Interface

#### Asset Browser

- **URL**: `/assets`
- **Features**:
  - Paginated asset listing
  - Search and filtering
  - Asset details view
  - Bulk operations

#### Review Dashboard

- **URL**: `/review`
- **Features**:
  - Review queue management
  - Asset preview
  - Resolution interface
  - Bulk operations

#### Source Management

- **URL**: `/sources`
- **Features**:
  - Source configuration
  - Connection testing
  - Ingest status monitoring

### 3. API Endpoints

#### Asset Endpoints

```python
# List assets
GET /api/assets
# Get asset details
GET /api/assets/{asset_id}
# Update asset
PUT /api/assets/{asset_id}
# Delete asset
DELETE /api/assets/{asset_id}
```

#### Review Endpoints

```python
# List review queue
GET /api/review/list
# Enqueue for review
POST /api/review/{asset_id}/enqueue
# Resolve review
POST /api/review/{review_id}/resolve
# Reject review
POST /api/review/{review_id}/reject
```

#### Ingest Endpoints

```python
# Run ingestion
POST /api/ingest/run
# Get ingest status
GET /api/ingest/status
# List sources
GET /api/ingest/sources
```

## 🔍 Review System

### Purpose and Workflow

The review system provides quality assurance for content discovery and ingestion:

1. **Automatic Queueing**: Assets are queued based on confidence scores
2. **Human Review**: Reviewers examine assets and metadata
3. **Resolution**: Assets are approved, rejected, or marked for more info
4. **Integration**: Approved assets become canonical in the library

### Review Triggers

Assets are automatically queued for review when:

- **Low confidence scores** (< 0.5) from automated analysis
- **Unusual file characteristics** (size, duration, format)
- **Missing critical metadata** (codecs, duration)
- **Manual triggers** from administrators

### Confidence Scoring

```python
def calculate_confidence_score(asset: Asset) -> float:
    """Calculate confidence score for asset matching."""
    score = 0.0

    # File size reasonableness (0.2 points)
    if 500_000_000 <= asset.size <= 10_000_000_000:  # 500MB - 10GB
        score += 0.2

    # Duration reasonableness (0.2 points)
    if asset.duration_ms and 1_800_000 <= asset.duration_ms <= 7_200_000:  # 30min - 2hrs
        score += 0.2

    # Codec compatibility (0.2 points)
    if asset.video_codec in ['h264', 'h265', 'vp9']:
        score += 0.1
    if asset.audio_codec in ['aac', 'ac3', 'dts']:
        score += 0.1

    # Container format (0.1 points)
    if asset.container in ['mp4', 'mkv', 'avi']:
        score += 0.1

    # Metadata completeness (0.3 points)
    metadata_score = 0.0
    if asset.video_codec:
        metadata_score += 0.1
    if asset.audio_codec:
        metadata_score += 0.1
    if asset.duration_ms:
        metadata_score += 0.1

    score += min(metadata_score, 0.3)

    return min(score, 1.0)
```

### Review Resolution

#### Approve Asset

```python
# Link asset to episode and mark as canonical
def resolve_review(review_id: UUID, episode_id: UUID, notes: str = None):
    review = get_review(review_id)
    asset = get_asset(review.asset_id)
    episode = get_episode(episode_id)

    # Create EpisodeAsset relationship
    episode_asset = EpisodeAsset(
        episode_id=episode_id,
        asset_id=asset.id,
        canonical=True
    )

    # Update review status
    review.status = ReviewStatus.RESOLVED
    review.resolved_at = datetime.utcnow()
    review.notes = notes
```

#### Reject Asset

```python
# Remove from queue without linking
def reject_review(review_id: UUID, notes: str = None):
    review = get_review(review_id)
    review.status = ReviewStatus.REJECTED
    review.resolved_at = datetime.utcnow()
    review.notes = notes
```

## 📊 Content Lifecycle

### 1. Discovery Phase

```
External Source → Importer → ContentItem → Asset Registration
```

### 2. Enrichment Phase

```
Asset → Enricher → Metadata → Updated Asset
```

### 3. Review Phase

```
Asset → Confidence Scoring → Review Queue → Human Review → Resolution
```

### 4. Integration Phase

```
Approved Asset → Episode Association → Library Integration → Streaming Ready
```

## 🔧 Configuration

### Source Configuration

```python
# Plex source configuration
plex_source = {
    "name": "My Plex Server",
    "type": "plex",
    "config": {
        "server_url": "http://192.168.1.100:32400",
        "token": "plex_token_here",
        "libraries": ["Movies", "TV Shows"]
    }
}

# Filesystem source configuration
filesystem_source = {
    "name": "Local Media",
    "type": "filesystem",
    "config": {
        "path": "/media/movies",
        "extensions": [".mp4", ".mkv", ".avi"]
    }
}
```

### Review Configuration

```python
# Review system settings
review_config = {
    "confidence_threshold": 0.5,
    "auto_queue_rules": [
        "size < 100MB",
        "duration < 1 minute",
        "missing_codec_info"
    ],
    "notification_settings": {
        "email_alerts": True,
        "slack_webhook": "https://hooks.slack.com/..."
    }
}
```

## 📈 Monitoring and Analytics

### Key Metrics

- **Asset count**: Total assets in library
- **Review queue size**: Pending review items
- **Ingest rate**: Assets processed per hour
- **Confidence distribution**: Review confidence scores
- **Resolution rate**: Reviews resolved per day

### Health Checks

```python
def check_cms_health():
    return {
        "database_connection": check_db_connection(),
        "review_queue_size": count_pending_reviews(),
        "ingest_status": check_ingest_health(),
        "source_connections": check_source_health()
    }
```

## 🚀 Future Enhancements

### Planned Features

- **Machine Learning**: Improve confidence scoring with ML models
- **Bulk Operations**: Batch processing for large libraries
- **Advanced Filtering**: Complex search and filter capabilities
- **Metadata Enrichment**: Integration with external metadata providers
- **Content Deduplication**: Automatic duplicate detection and resolution

### Integration Opportunities

- **Plex Live TV**: Direct integration with Plex Live TV
- **XMLTV**: Export guide data in XMLTV format
- **External APIs**: Integration with TVDB, TMDB, etc.
- **Cloud Storage**: Support for cloud-based media storage

---

_The Content Management System provides the foundation for all content operations in Retrovue, ensuring quality, organization, and accessibility of media content._
