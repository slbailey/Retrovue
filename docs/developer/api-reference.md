# 🔌 API Reference

Complete reference for the Retrovue REST API, including all endpoints, request/response formats, and authentication.

## 🌐 Base URL

```
http://localhost:8000/api
```

## 🔐 Authentication

Currently, the API does not require authentication for local development. In production deployments, authentication will be added.

## 📋 Current API Endpoints

The Retrovue API is built with FastAPI and provides endpoints for content management, ingestion, and health monitoring.

## 📋 API Endpoints

### **Health & Status**

#### **GET** `/api/healthz`

Check API health and database connectivity.

**Response:**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "db": "ok",
  "response_time_ms": 15.23,
  "timestamp": 1640995200.0
}
```

**Error Response (503):**

```json
{
  "status": "error",
  "version": "0.1.0",
  "db": "error",
  "db_error": "Connection failed",
  "response_time_ms": 15.23,
  "timestamp": 1640995200.0
}
```

### **Assets Management**

#### **GET** `/api/v1/assets`

List all assets with optional filtering.

**Query Parameters:**

- `limit` (optional): Maximum number of items (default: 50)
- `offset` (optional): Number of items to skip (default: 0)
- `canonical` (optional): Filter by canonical status (true/false)
- `deleted` (optional): Filter by deleted status (true/false)

**Response:**

```json
{
  "assets": [
    {
      "id": 1,
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "uri": "file:///media/movie.mp4",
      "size": 8589934592,
      "duration_ms": 7200000,
      "video_codec": "h264",
      "audio_codec": "aac",
      "container": "mp4",
      "canonical": true,
      "is_deleted": false,
      "discovered_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 1250,
  "limit": 50,
  "offset": 0
}
```

#### **GET** `/api/v1/assets/{asset_id}`

Get detailed information about a specific asset.

**Parameters:**

- `asset_id` (path): ID of the asset

**Response:**

```json
{
  "id": 1,
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "uri": "file:///media/movie.mp4",
  "size": 8589934592,
  "duration_ms": 7200000,
  "video_codec": "h264",
  "audio_codec": "aac",
  "container": "mp4",
  "canonical": true,
  "is_deleted": false,
  "discovered_at": "2024-01-15T14:30:00Z",
  "episodes": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "title_id": "789e0123-e89b-12d3-a456-426614174000",
      "season_id": "012e3456-e89b-12d3-a456-426614174000",
      "number": 1,
      "name": "Pilot"
    }
  ],
  "markers": [
    {
      "id": "321e6543-e89b-12d3-a456-426614174000",
      "kind": "chapter",
      "start_ms": 0,
      "end_ms": 300000,
      "payload": { "title": "Opening Credits" }
    }
  ]
}
```

### **Content Ingestion**

#### **POST** `/api/ingest/run`

Start content ingestion process.

**Query Parameters:**

- `source` (required): Source type (plex, filesystem, etc.)
- `source_id` (optional): Specific source ID

**Request Body:**

```json
{
  "library_ids": ["library1", "library2"],
  "enrichers": ["ffprobe", "metadata"]
}
```

**Response:**

```json
{
  "success": true,
  "discovered": 100,
  "registered": 95,
  "enriched": 90,
  "canonicalized": 85,
  "queued_for_review": 10
}
```

#### **GET** `/api/ingest/status`

Get status of the last ingestion process.

**Response:**

```json
{
  "last_run": "2024-01-15T14:30:00Z",
  "status": "completed",
  "discovered": 100,
  "registered": 95,
  "enriched": 90,
  "canonicalized": 85,
  "queued_for_review": 10
}
```

### **Review System**

#### **GET** `/api/v1/review`

List items in the review queue.

**Query Parameters:**

- `status` (optional): Filter by status (pending, resolved, rejected)
- `limit` (optional): Maximum number of items (default: 50)
- `offset` (optional): Number of items to skip (default: 0)

**Response:**

```json
{
  "reviews": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "asset_id": 1,
      "reason": "Low confidence match",
      "confidence": 0.3,
      "status": "pending",
      "created_at": "2024-01-15T14:30:00Z",
      "asset": {
        "id": 1,
        "uuid": "987fcdeb-51a2-43d1-b456-426614174000",
        "uri": "file:///media/movie.mp4",
        "size": 8589934592,
        "canonical": false
      }
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

#### **POST** `/api/v1/review/{review_id}/resolve`

Resolve a review queue item.

**Parameters:**

- `review_id` (path): UUID of the review to resolve

**Request Body:**

```json
{
  "episode_id": "456e7890-e89b-12d3-a456-426614174000",
  "notes": "Manually verified and approved"
}
```

**Response:**

```json
{
  "success": true,
  "review_id": "123e4567-e89b-12d3-a456-426614174000",
  "asset_id": 1,
  "episode_id": "456e7890-e89b-12d3-a456-426614174000"
}
```

#### **POST** `/api/v1/review/{review_id}/reject`

Reject a review queue item.

**Parameters:**

- `review_id` (path): UUID of the review to reject

**Request Body:**

```json
{
  "notes": "Poor quality, unsuitable for library"
}
```

**Response:**

```json
{
  "success": true,
  "review_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "rejected"
}
```

### **Series and Episodes**

#### **GET** `/api/v1/series`

List all series (titles) in the library.

**Query Parameters:**

- `limit` (optional): Maximum number of items (default: 50)
- `offset` (optional): Number of items to skip (default: 0)
- `kind` (optional): Filter by title kind (movie, show)

**Response:**

```json
{
  "series": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "kind": "show",
      "name": "Cheers",
      "year": 1982,
      "external_ids": { "imdb": "tt0083399" },
      "created_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

#### **GET** `/api/v1/series/{series_id}/episodes`

Get episodes for a specific series.

**Parameters:**

- `series_id` (path): UUID of the series

**Response:**

```json
{
  "series": {
    "id": "789e0123-e89b-12d3-a456-426614174000",
    "name": "Cheers",
    "year": 1982
  },
  "episodes": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "season_id": "012e3456-e89b-12d3-a456-426614174000",
      "number": 1,
      "name": "Pilot",
      "assets": [
        {
          "id": 1,
          "uuid": "987fcdeb-51a2-43d1-b456-426614174000",
          "uri": "file:///media/cheers_s01e01.mp4",
          "size": 8589934592,
          "duration_ms": 1800000,
          "canonical": true
        }
      ]
    }
  ]
}
```

### **Metrics**

#### **GET** `/api/metrics`

Get system metrics and performance data.

**Response:**

```json
{
  "database": {
    "connections": 5,
    "active_queries": 2
  },
  "content": {
    "total_assets": 1250,
    "canonical_assets": 1200,
    "pending_reviews": 3,
    "total_series": 25,
    "total_episodes": 500
  },
  "ingest": {
    "last_run": "2024-01-15T14:30:00Z",
    "status": "completed",
    "total_discovered": 100,
    "total_registered": 95
  }
}
```

## 📊 Error Handling

### **Error Response Format**

All API errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### **Common Error Codes**

- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error
- `503` - Service Unavailable (database issues)

### **HTTP Status Codes**

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Unprocessable Entity
- `500` - Internal Server Error
- `503` - Service Unavailable

## 🔧 Rate Limiting

Currently, no rate limiting is implemented. In production deployments, rate limiting will be added to prevent abuse.

## 📝 Examples

### **Complete Workflow Example**

```bash
# 1. Check API health
curl http://localhost:8000/api/healthz

# 2. List assets
curl http://localhost:8000/api/v1/assets?limit=10

# 3. Start content ingestion
curl -X POST "http://localhost:8000/api/ingest/run?source=plex" \
  -H "Content-Type: application/json" \
  -d '{"library_ids": ["library1"], "enrichers": ["ffprobe"]}'

# 4. Check ingestion status
curl http://localhost:8000/api/ingest/status

# 5. List review queue
curl http://localhost:8000/api/v1/review

# 6. Get series list
curl http://localhost:8000/api/v1/series

# 7. Get episodes for a series
curl http://localhost:8000/api/v1/series/{series_id}/episodes
```

### **Python Client Example**

```python
import requests

# Base URL
base_url = "http://localhost:8000/api"

# Check health
response = requests.get(f"{base_url}/healthz")
print(response.json())

# List assets
response = requests.get(f"{base_url}/v1/assets", params={"limit": 10})
assets = response.json()
print(f"Found {len(assets['assets'])} assets")

# Start ingestion
ingest_data = {
    "library_ids": ["library1"],
    "enrichers": ["ffprobe"]
}
response = requests.post(
    f"{base_url}/ingest/run?source=plex",
    json=ingest_data
)
result = response.json()
print(f"Ingestion completed: {result['registered']} items registered")
```

## 🎯 Next Steps

- **Check [CLI Reference](cli-reference.md)** for command-line interface
- **Read [Architecture Guide](architecture.md)** for system design
- **Review [Database Schema](database-schema.md)** for data models
- **See [Testing Guide](testing.md)** for development practices
