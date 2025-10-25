# Retrovue Review System

> **Legacy Document** — Pre-Alembic version, retained for reference only.

This document describes the review workflow and quality assurance system in Retrovue, including endpoints, data models, and operational procedures.

## Overview

The review system provides quality assurance for content discovery and ingestion. It allows human reviewers to verify and approve assets before they become canonical, ensuring content quality and proper metadata association.

## Review Workflow

### 1. Automatic Review Queueing

Assets are automatically queued for review when:

- **Low confidence scores** from automated analysis
- **Metadata conflicts** between sources
- **Unusual file characteristics** (size, duration, format)
- **Manual triggers** from administrators

### 2. Review Process

```
Asset Discovery → Enrichment → Confidence Scoring → Review Queue → Human Review → Resolution
```

### 3. Resolution Actions

- **Approve**: Mark asset as canonical and link to episode
- **Reject**: Remove from queue without action
- **Request More Info**: Add notes for further investigation

## Data Models

### ReviewQueue Entity

```python
class ReviewQueue(Base):
    """Items that need human review for quality assurance."""

    __tablename__ = "review_queue"

    id: UUID = Primary key
    asset_id: UUID = Foreign key to assets table
    reason: str = Reason for review
    confidence: float = Confidence score (0.0-1.0)
    status: ReviewStatus = PENDING | RESOLVED | REJECTED
    created_at: datetime = When review was queued
    resolved_at: datetime = When review was completed
    notes: str = Resolution notes
```

### ReviewStatus Enum

```python
class ReviewStatus(Enum):
    PENDING = "pending"      # Awaiting review
    RESOLVED = "resolved"    # Review completed successfully
    REJECTED = "rejected"    # Review completed with rejection
```

## API Endpoints

### 1. Enqueue Review

**POST** `/api/review/{asset_id}/enqueue`

Enqueue an asset for human review.

**Parameters**:

- `asset_id` (path): UUID of the asset to review
- `reason` (body): Reason for review
- `score` (body): Confidence score (0.0-1.0)

**Request Body**:

```json
{
  "reason": "Low confidence match",
  "score": 0.3
}
```

**Response**:

```json
{
  "success": true
}
```

**Example**:

```bash
curl -X POST "http://localhost:8080/api/review/123e4567-e89b-12d3-a456-426614174000/enqueue" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Unusual file size", "score": 0.2}'
```

### 2. List Review Queue

**GET** `/api/review/list`

List all pending review items.

**Query Parameters**:

- `status` (optional): Filter by status (pending, resolved, rejected)
- `limit` (optional): Maximum number of items to return
- `offset` (optional): Number of items to skip

**Response**:

```json
{
  "reviews": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "asset_id": "987fcdeb-51a2-43d1-b456-426614174000",
      "reason": "Low confidence match",
      "confidence": 0.3,
      "status": "pending",
      "created_at": "2024-01-15T14:30:00Z",
      "asset": {
        "id": "987fcdeb-51a2-43d1-b456-426614174000",
        "uri": "file:///media/movie.mp4",
        "size": 8589934592,
        "duration_ms": 7200000,
        "canonical": false
      }
    }
  ],
  "total": 1,
  "status_filter": "pending"
}
```

### 3. Resolve Review

**POST** `/api/review/{review_id}/resolve`

Resolve a review queue item.

**Parameters**:

- `review_id` (path): UUID of the review to resolve
- `episode_id` (body): UUID of the episode to associate
- `notes` (body, optional): Resolution notes

**Request Body**:

```json
{
  "episode_id": "456e7890-e89b-12d3-a456-426614174000",
  "notes": "Manually verified and approved"
}
```

**Response**:

```json
{
  "success": true,
  "review_id": "123e4567-e89b-12d3-a456-426614174000",
  "asset_id": "987fcdeb-51a2-43d1-b456-426614174000",
  "episode_id": "456e7890-e89b-12d3-a456-426614174000"
}
```

### 4. Reject Review

**POST** `/api/review/{review_id}/reject`

Reject a review queue item.

**Parameters**:

- `review_id` (path): UUID of the review to reject
- `notes` (body, optional): Rejection reason

**Request Body**:

```json
{
  "notes": "Poor quality, unsuitable for library"
}
```

**Response**:

```json
{
  "success": true,
  "review_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "rejected"
}
```

## CLI Commands

### 1. List Review Queue

```bash
# List all pending reviews
retrovue review list

# List with JSON output
retrovue review list --json

# List resolved reviews
retrovue review list --status resolved
```

**Output**:

```
Review Queue (3 items)
=====================

ID: 123e4567-e89b-12d3-a456-426614174000
Asset: file:///media/movie1.mp4 (8.0 GB)
Reason: Low confidence match
Confidence: 0.3
Created: 2024-01-15 14:30:00

ID: 456e7890-e89b-12d3-a456-426614174000
Asset: file:///media/movie2.mp4 (6.5 GB)
Reason: Unusual file size
Confidence: 0.2
Created: 2024-01-15 14:25:00
```

### 2. Resolve Review

```bash
# Resolve a review item
retrovue review resolve <review_id> <episode_id>

# Resolve with notes
retrovue review resolve <review_id> <episode_id> --notes "Manually verified"

# Resolve with JSON output
retrovue review resolve <review_id> <episode_id> --json
```

**Output**:

```
Review resolved successfully
Review ID: 123e4567-e89b-12d3-a456-426614174000
Asset ID: 987fcdeb-51a2-43d1-b456-426614174000
Episode ID: 456e7890-e89b-12d3-a456-426614174000
Notes: Manually verified and approved
```

## Service Layer

### LibraryService Review Methods

```python
class LibraryService:
    """Service for managing the content library."""

    def enqueue_review(self, asset_id: UUID, reason: str, confidence: float) -> ReviewQueue:
        """Enqueue an asset for review."""
        # Implementation details...

    def list_review_queue(self) -> list[ReviewQueue]:
        """List items in the review queue."""
        # Implementation details...

    def resolve_review(self, review_id: UUID, episode_id: UUID, notes: str = None) -> bool:
        """Resolve a review queue item."""
        # Implementation details...
```

### Review Queue Operations

```python
# Enqueue an asset for review
review = library_service.enqueue_review(
    asset_id=asset.id,
    reason="Low confidence match",
    confidence=0.3
)

# List pending reviews
reviews = library_service.list_review_queue()

# Resolve a review
success = library_service.resolve_review(
    review_id=review.id,
    episode_id=episode.id,
    notes="Manually verified"
)
```

## Web Interface

### Review Dashboard

The web interface provides a dashboard for managing review items:

**URL**: `/review`

**Features**:

- **Review queue listing** with pagination
- **Asset details** with metadata preview
- **Confidence scores** and review reasons
- **Bulk operations** for multiple items
- **Search and filtering** capabilities

### Review Item Details

**URL**: `/review/{review_id}`

**Features**:

- **Asset metadata** display
- **Confidence analysis** breakdown
- **Episode association** interface
- **Resolution actions** (approve/reject)
- **Notes and comments** system

## Quality Assurance Rules

### 1. Automatic Review Triggers

```python
def should_enqueue_for_review(asset: Asset, confidence: float) -> bool:
    """Determine if an asset should be queued for review."""

    # Low confidence scores
    if confidence < 0.5:
        return True

    # Unusual file characteristics
    if asset.size < 100_000_000:  # Less than 100MB
        return True

    if asset.duration_ms and asset.duration_ms < 60_000:  # Less than 1 minute
        return True

    # Missing critical metadata
    if not asset.video_codec or not asset.audio_codec:
        return True

    return False
```

### 2. Confidence Scoring

```python
def calculate_confidence_score(asset: Asset, metadata: dict) -> float:
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

## Integration Points

### 1. Ingest Pipeline Integration

```python
class IngestPipeline:
    """Content ingestion pipeline with review integration."""

    def process_discovered_item(self, item: DiscoveredItem) -> Asset:
        """Process a discovered item through the pipeline."""
        # Register asset
        asset = self.library_service.register_asset_from_discovery(item)

        # Enrich with metadata
        enriched_asset = self.enrich_asset(asset)

        # Calculate confidence score
        confidence = self.calculate_confidence_score(enriched_asset)

        # Queue for review if needed
        if self.should_enqueue_for_review(enriched_asset, confidence):
            self.library_service.enqueue_review(
                asset_id=enriched_asset.id,
                reason="Automated quality check",
                confidence=confidence
            )

        return enriched_asset
```

### 2. Notification System

```python
class ReviewNotificationService:
    """Service for sending review notifications."""

    def notify_review_queued(self, review: ReviewQueue):
        """Notify administrators of new review items."""
        # Send email/Slack notification
        pass

    def notify_review_resolved(self, review: ReviewQueue):
        """Notify of review resolution."""
        # Send completion notification
        pass
```

## Monitoring and Analytics

### 1. Review Metrics

```python
class ReviewMetrics:
    """Metrics for review system performance."""

    def get_review_stats(self) -> dict:
        """Get review system statistics."""
        return {
            "pending_reviews": self.count_pending_reviews(),
            "resolved_today": self.count_resolved_today(),
            "average_resolution_time": self.get_average_resolution_time(),
            "confidence_distribution": self.get_confidence_distribution()
        }
```

### 2. Performance Monitoring

```python
def monitor_review_performance():
    """Monitor review system performance."""
    metrics = {
        "queue_size": len(library_service.list_review_queue()),
        "oldest_pending": get_oldest_pending_review(),
        "resolution_rate": calculate_resolution_rate(),
        "average_confidence": calculate_average_confidence()
    }

    # Alert if queue is too large
    if metrics["queue_size"] > 100:
        send_alert("Review queue is large", metrics)

    # Alert if oldest pending is too old
    if metrics["oldest_pending"] > timedelta(days=7):
        send_alert("Old reviews pending", metrics)
```

## Best Practices

### 1. Review Queue Management

- **Regular processing**: Process review queue daily
- **Priority handling**: Address high-confidence items first
- **Batch operations**: Use bulk actions for efficiency
- **Documentation**: Add clear notes for future reference

### 2. Quality Standards

- **Consistent criteria**: Use standardized review criteria
- **Training**: Train reviewers on quality standards
- **Feedback loops**: Use resolution data to improve automation
- **Metrics tracking**: Monitor review quality and efficiency

### 3. Automation Integration

- **Confidence thresholds**: Tune confidence scoring
- **Rule refinement**: Update automatic triggers based on data
- **Machine learning**: Use historical data to improve automation
- **Exception handling**: Handle edge cases gracefully

## Troubleshooting

### Common Issues

**1. Review Queue Backup**

```bash
# Check queue size
retrovue review list --json | jq '.total'

# Process oldest items first
retrovue review list --json | jq '.reviews | sort_by(.created_at) | .[0:10]'
```

**2. Low Confidence Scores**

```python
# Analyze confidence distribution
def analyze_confidence_scores():
    reviews = library_service.list_review_queue()
    scores = [r.confidence for r in reviews]
    print(f"Average confidence: {sum(scores) / len(scores):.2f}")
    print(f"Min confidence: {min(scores):.2f}")
    print(f"Max confidence: {max(scores):.2f}")
```

**3. Resolution Failures**

```python
# Check for resolution errors
def check_resolution_errors():
    failed_resolutions = session.query(ReviewQueue).filter(
        ReviewQueue.status == ReviewStatus.PENDING,
        ReviewQueue.created_at < datetime.utcnow() - timedelta(hours=24)
    ).all()

    for review in failed_resolutions:
        print(f"Old pending review: {review.id} - {review.reason}")
```

---

_This review system ensures content quality and proper metadata association through human oversight and automated quality checks._
