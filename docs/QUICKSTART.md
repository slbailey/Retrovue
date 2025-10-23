# Retrovue Quick Start Guide

This guide will help you get Retrovue up and running quickly for development and testing.

## Prerequisites

### Required Software

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 13+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)
- **Git** - [Download Git](https://git-scm.com/downloads)

### Optional Software

- **Docker** - [Download Docker](https://www.docker.com/get-started) (for containerized development)
- **VLC Media Player** - [Download VLC](https://www.videolan.org/vlc/) (for testing streams)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/retrovue.git
cd retrovue
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install package in development mode
pip install -e .

# Install additional development dependencies
pip install -r requirements-dev.txt
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb retrovue

# Run database migrations
alembic upgrade head
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+psycopg://retrovue:retrovue@localhost:5432/retrovue
ECHO_SQL=false

# Application Settings
LOG_LEVEL=INFO
ENV=dev
ALLOWED_ORIGINS=*

# Media Configuration
MEDIA_ROOTS=./test_media
PLEX_TOKEN=your-plex-token-here
```

### 2. Test Media Setup

```bash
# Create test media directory
mkdir -p test_media/movies
mkdir -p test_media/tv

# Add some test videos (optional)
# Copy some MP4/MKV files to test_media/movies/
```

## Development Setup

### 1. Start the Development Server

```bash
# Start the API server
python -m retrovue.api.main

# Or use uvicorn directly
uvicorn retrovue.api.main:app --reload --host 0.0.0.0 --port 8080
```

### 2. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8080/api/healthz

# Check metrics endpoint
curl http://localhost:8080/api/metrics

# Check CLI
retrovue --help
```

### 3. Access Web Interface

Open your browser and navigate to:

- **Dashboard**: http://localhost:8080/
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/healthz

## First Content Ingest

### 1. Using the CLI

```bash
# Discover content from filesystem
retrovue ingest run filesystem:./test_media --enrichers ffprobe

# List discovered assets
retrovue assets list

# List review queue
retrovue review list
```

### 2. Using the API

```bash
# Start ingest via API
curl -X POST "http://localhost:8080/api/ingest/run" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "filesystem:./test_media",
    "enrichers": ["ffprobe"]
  }'

# List assets
curl "http://localhost:8080/api/assets/list"

# List review queue
curl "http://localhost:8080/api/review/list"
```

### 3. Using the Web Interface

1. Navigate to http://localhost:8080/
2. Click "New Source" to add a filesystem source
3. Configure the source with path `./test_media`
4. Click "Start Ingest" to begin discovery
5. Review the ingest summary and results

## Docker Development

### 1. Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f retrovue

# Stop services
docker-compose down
```

### 2. Docker Compose Configuration

**docker-compose.dev.yml**:

```yaml
version: "3.8"

services:
  retrovue:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql+psycopg://retrovue:retrovue@db:5432/retrovue
      - LOG_LEVEL=DEBUG
      - ENV=dev
      - MEDIA_ROOTS=/media
    volumes:
      - ./test_media:/media
      - .:/app
    depends_on:
      - db
    command: uvicorn retrovue.api.main:app --reload --host 0.0.0.0 --port 8080

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=retrovue
      - POSTGRES_USER=retrovue
      - POSTGRES_PASSWORD=retrovue
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 3. Development Commands

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
docker-compose exec retrovue alembic upgrade head

# Run CLI commands
docker-compose exec retrovue retrovue --help

# View logs
docker-compose logs -f retrovue
```

## Testing the Stream

### 1. Start Content Ingestion

```bash
# Ingest test content
retrovue ingest run filesystem:./test_media --enrichers ffprobe

# Mark assets as canonical (for testing)
retrovue assets list --status pending
# Note the asset IDs and mark them as canonical via API or web interface
```

### 2. Test HLS Stream

```bash
# Start the streaming server (if implemented)
python -m retrovue.streaming.server

# Test with VLC
# 1. Open VLC Media Player
# 2. Go to: Media → Open Network Stream
# 3. Enter: http://localhost:8080/channel/1/playlist.m3u8
# 4. Click Play
```

### 3. Verify Stream Quality

- ✅ Stream starts immediately
- ✅ No buffering or stuttering
- ✅ Timeline shows correct duration
- ✅ Audio and video are synchronized

## Common Development Tasks

### 1. Database Operations

```bash
# Reset database
alembic downgrade base
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### 2. Content Management

```bash
# List all assets
retrovue assets list

# List pending assets
retrovue assets list --status pending

# List canonical assets
retrovue assets list --status canonical

# List review queue
retrovue review list

# Resolve review item
retrovue review resolve <review_id> <episode_id>
```

### 3. Development Tools

```bash
# Run tests
pytest

# Run linting
flake8 src/
black src/

# Run type checking
mypy src/

# Generate documentation
sphinx-build docs/ docs/_build/
```

## Troubleshooting

### Common Issues

**1. Database Connection Failed**

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check database exists
psql -h localhost -U retrovue -d retrovue -c "SELECT 1"

# Reset database
dropdb retrovue
createdb retrovue
alembic upgrade head
```

**2. Import Errors**

```bash
# Reinstall package
pip uninstall retrovue
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"

# Verify installation
python -c "import retrovue; print(retrovue.__version__)"
```

**3. FFmpeg Not Found**

```bash
# Check FFmpeg installation
ffmpeg -version

# Install FFmpeg (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg

# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Windows)
# Download from https://ffmpeg.org/download.html
```

**4. Permission Errors**

```bash
# Check file permissions
ls -la test_media/

# Fix permissions
chmod -R 755 test_media/

# Check database permissions
psql -h localhost -U retrovue -d retrovue -c "SELECT current_user"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Enable SQL logging
export ECHO_SQL=true

# Start with debug mode
python -m retrovue.api.main --debug
```

### Log Analysis

```bash
# View application logs
tail -f logs/retrovue.log

# Filter error logs
grep "ERROR" logs/retrovue.log

# Monitor database queries
grep "SQL" logs/retrovue.log
```

## Next Steps

### 1. Explore the Codebase

- **Architecture**: Read `docs/ARCHITECTURE.md`
- **Database Schema**: Review `docs/DB_SCHEMA.md`
- **API Documentation**: Visit http://localhost:8080/docs

### 2. Add Your Content

- **Filesystem Import**: Add media files to `test_media/`
- **Plex Integration**: Configure Plex server connection
- **Custom Importers**: Implement custom content sources

### 3. Customize Configuration

- **Environment Variables**: Modify `.env` file
- **Database Settings**: Adjust connection pool settings
- **Logging Configuration**: Customize log levels and formats

### 4. Production Deployment

- **Docker Deployment**: Use production Docker images
- **Kubernetes**: Deploy to Kubernetes cluster
- **Cloud Deployment**: Deploy to AWS, GCP, or Azure

## Development Workflow

### 1. Daily Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run tests
pytest

# Check code quality
flake8 src/
black src/
mypy src/

# Start development server
uvicorn retrovue.api.main:app --reload
```

### 2. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-importer

# Make changes
# ... edit code ...

# Run tests
pytest tests/

# Commit changes
git add .
git commit -m "Add new importer feature"

# Push branch
git push origin feature/new-importer
```

### 3. Database Changes

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Review migration
cat alembic/versions/xxx_add_new_table.py

# Apply migration
alembic upgrade head

# Test migration
pytest tests/
```

## Getting Help

### 1. Documentation

- **README**: Project overview and setup
- **Architecture**: System design and patterns
- **API Reference**: Endpoint documentation
- **CLI Reference**: Command-line interface

### 2. Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and community support
- **Wiki**: Additional documentation and examples

### 3. Development Resources

- **Code Examples**: See `examples/` directory
- **Test Cases**: Review `tests/` directory
- **Configuration**: Check `docs/CONFIGURATION.md`

---

_This quick start guide will get you up and running with Retrovue in minutes. For more detailed information, see the other documentation files in the `docs/` directory._

