# Retrovue System Architecture

This document describes the overall architecture of Retrovue, including the layered design, component relationships, and key architectural patterns.

## Overview

Retrovue follows a **Clean Architecture** pattern with clear separation of concerns across multiple layers. The system is designed to be maintainable, testable, and extensible.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
├─────────────────────────────────────────────────────────────┤
│  API (FastAPI)     │  CLI (Typer)     │  Web (Jinja2)     │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Services (Business Logic)  │  Use Cases  │  Orchestration │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                            │
├─────────────────────────────────────────────────────────────┤
│  Entities  │  Value Objects  │  Domain Services  │  Rules  │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                    │
├─────────────────────────────────────────────────────────────┤
│  Database  │  External APIs  │  File System  │  Logging   │
└─────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. Domain Layer (`src/retrovue/domain/`)

**Purpose**: Contains the core business logic and entities, independent of external concerns.

**Components**:

- **Entities** (`entities.py`): Core business objects (Title, Episode, Asset, etc.)
- **Value Objects**: Immutable objects representing domain concepts
- **Domain Services**: Business logic that doesn't belong to a single entity
- **Domain Rules**: Business rules and constraints

**Key Entities**:

```python
# Core content entities
Title -> Season -> Episode
Asset -> Episode (many-to-many via EpisodeAsset)

# Supporting entities
ProviderRef -> External provider references
Marker -> Asset markers (chapters, availability)
ReviewQueue -> Quality assurance items
Source -> Content sources (Plex, filesystem)
```

### 2. Application Layer (`src/retrovue/app/`)

**Purpose**: Orchestrates domain objects and coordinates business workflows.

**Components**:

- **Services** (`*_service.py`): Business logic coordination
  - `IngestService`: Content discovery and ingestion
  - `LibraryService`: Content library management
  - `SourceService`: Source management
- **Use Cases**: Specific business operations
- **Application Services**: Cross-cutting business logic

**Service Pattern**:

```python
class IngestService:
    def __init__(self, db: Session):
        self.db = db

    def run_ingest(self, source: str) -> dict[str, int]:
        # Orchestrate domain objects and adapters
        # Return business results
```

### 3. Infrastructure Layer (`src/retrovue/infra/`)

**Purpose**: Handles external concerns like databases, APIs, and file systems.

**Components**:

- **Database** (`db.py`): SQLAlchemy configuration and session management
- **Settings** (`settings.py`): Application configuration
- **Logging** (`logging.py`): Structured logging with secret redaction
- **External APIs**: Plex, filesystem, etc.

### 4. Adapters Layer (`src/retrovue/adapters/`)

**Purpose**: Implements interfaces between the application and external systems.

**Components**:

- **Importers** (`importers/`): Content discovery from external sources
  - `PlexImporter`: Plex server integration
  - `FilesystemImporter`: Local file system scanning
- **Enrichers** (`enrichers/`): Content metadata enhancement
  - `FFProbeEnricher`: Media file analysis
- **Registry**: Adapter registration and discovery

## Unit of Work Pattern

The system uses a **Unit of Work (UoW)** pattern for database transaction management:

### API Layer (`api/deps.py`)

```python
def get_db() -> Generator:
    """Provide a Session per-request with unit-of-work:
    - success => commit once
    - error => rollback
    - always close
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### CLI Layer (`cli/uow.py`)

```python
@contextlib.contextmanager
def session() -> Generator[Session, None, None]:
    """CLI UoW context manager mirroring API semantics."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

## Data Flow

### 1. Content Ingestion Flow

```
External Source → Importer → Enricher → Domain Entities → Database
     ↓              ↓           ↓            ↓
  Plex API    FilesystemImporter  FFProbeEnricher  Asset/Episode
```

### 2. API Request Flow

```
HTTP Request → FastAPI Router → Service Layer → Domain Layer → Database
     ↓              ↓              ↓             ↓
  JSON Input    Business Logic   Domain Rules   SQLAlchemy
```

### 3. CLI Command Flow

```
CLI Command → Typer Router → Service Layer → Domain Layer → Database
     ↓            ↓              ↓             ↓
  Arguments   Business Logic   Domain Rules   SQLAlchemy
```

## Cross-Cutting Concerns

### 1. Logging (`infra/logging.py`)

- **Structured JSON logging** with `structlog`
- **Secret redaction** for security
- **Request correlation IDs** for tracing
- **Service context** binding

### 2. Configuration (`infra/settings.py`)

- **Environment-based configuration** with Pydantic
- **Type validation** and defaults
- **Secret management** for sensitive data

### 3. Database (`infra/db.py`)

- **SQLAlchemy ORM** with PostgreSQL
- **Connection pooling** and optimization
- **Migration support** with Alembic

## Component Relationships

### Service Dependencies

```
IngestService
├── ImporterRegistry (adapters)
├── EnricherRegistry (adapters)
├── Domain Entities (domain)
└── Database Session (infra)

LibraryService
├── Domain Entities (domain)
└── Database Session (infra)

SourceService
├── Domain Entities (domain)
└── Database Session (infra)
```

### API Dependencies

```
FastAPI App
├── Routers (api/routers/)
│   ├── Health Router (health.py)
│   ├── Metrics Router (metrics.py)
│   ├── Assets Router (assets.py)
│   ├── Ingest Router (ingest.py)
│   └── Review Router (review.py)
├── Dependencies (api/deps.py)
│   └── get_db() UoW
└── Schemas (api/schemas.py)
    └── Pydantic models
```

## Design Principles

### 1. Dependency Inversion

- **High-level modules** don't depend on low-level modules
- **Abstractions** don't depend on details
- **Details** depend on abstractions

### 2. Single Responsibility

- **Each layer** has a single, well-defined responsibility
- **Services** handle specific business domains
- **Adapters** handle specific external integrations

### 3. Open/Closed Principle

- **Open for extension** (new importers, enrichers)
- **Closed for modification** (core domain logic)

### 4. Interface Segregation

- **Small, focused interfaces** for adapters
- **Specific contracts** for each integration type

## Extension Points

### 1. Adding New Importers

```python
# 1. Implement base interface
class CustomImporter(BaseImporter):
    def discover_content(self, source: str) -> list[ContentItem]:
        # Implementation
        pass

# 2. Register in registry
registry.register("custom", CustomImporter)
```

### 2. Adding New Enrichers

```python
# 1. Implement base interface
class CustomEnricher(BaseEnricher):
    def enrich(self, asset: Asset) -> dict[str, Any]:
        # Implementation
        pass

# 2. Register in registry
registry.register("custom", CustomEnricher)
```

### 3. Adding New API Endpoints

```python
# 1. Create router
router = APIRouter()

@router.get("/custom")
def custom_endpoint(db: Session = Depends(get_db)):
    # Implementation
    pass

# 2. Include in main app
app.include_router(router, prefix="/api")
```

## Testing Strategy

### 1. Unit Tests

- **Domain entities** and business logic
- **Service layer** with mocked dependencies
- **Adapters** with test doubles

### 2. Integration Tests

- **API endpoints** with test database
- **Service orchestration** with real adapters
- **Database operations** with test data

### 3. End-to-End Tests

- **Complete workflows** from API to database
- **CLI commands** with real services
- **External integrations** with test environments

## Performance Considerations

### 1. Database Optimization

- **Connection pooling** for concurrent requests
- **Indexed queries** for common operations
- **Lazy loading** for large relationships

### 2. Caching Strategy

- **Service-level caching** for expensive operations
- **Database query caching** for repeated queries
- **External API caching** for provider data

### 3. Scalability

- **Stateless services** for horizontal scaling
- **Database sharding** for large datasets
- **Async operations** for I/O-bound tasks

---

_This architecture provides a solid foundation for Retrovue's content management and streaming capabilities while maintaining flexibility for future enhancements._
