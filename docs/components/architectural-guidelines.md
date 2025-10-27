# Architectural guidelines

This document outlines the core architectural patterns, design principles, and industry standards used throughout the RetroVue system. It serves as the foundation for understanding how we build and organize our components.

## Design philosophy

RetroVue follows a **Clean Architecture** approach with clear separation of concerns, dependency inversion, and industry-standard patterns. The goal is to create a maintainable, testable, and extensible system that can evolve from a content management system to a full IPTV platform.

**Domain-Driven Design**: The architecture implements domain concepts defined in `docs/domain/` documentation, ensuring that technical implementation aligns with business requirements and entity relationships.

## Core architectural patterns

### Clean architecture layers

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

**Key Principles:**

- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Single Responsibility**: Each layer has one clear purpose
- **Open/Closed**: Open for extension, closed for modification
- **Interface Segregation**: Small, focused interfaces

### Unit of work pattern

The UoW pattern ensures consistent database transaction management across all interfaces:

#### API layer implementation

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

#### CLI layer implementation

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

**Benefits:**

- **Consistent transaction handling** across API and CLI
- **Automatic rollback** on errors
- **Resource cleanup** guaranteed
- **Testable** with dependency injection

### FastAPI integration patterns

#### Dependency injection

```python
# API endpoints use dependency injection for services
@router.get("/assets")
def list_assets(
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service)
):
    return service.list_assets(db)
```

#### Pydantic schema validation

```python
# Request/response schemas with automatic validation
class AssetCreate(BaseModel):
    uri: str
    size: int
    duration_ms: Optional[int] = None

class AssetResponse(BaseModel):
    uuid: UUID
    uri: str
    state: str
    approved_for_broadcast: bool
    created_at: datetime
```

#### Error handling

```python
# Consistent error responses
@router.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )
```

### Adapter pattern for external integrations

#### Base interfaces

```python
class BaseImporter(ABC):
    @abstractmethod
    def discover_content(self, source: str) -> list[ContentItem]:
        pass

class BaseEnricher(ABC):
    @abstractmethod
    def enrich(self, asset: Asset) -> Asset:
        pass
```

#### Registry pattern

```python
class AdapterRegistry:
    def register(self, name: str, adapter_class: Type):
        self._adapters[name] = adapter_class

    def get(self, name: str) -> Type:
        return self._adapters[name]
```

**Benefits:**

- **Pluggable integrations** (Plex, filesystem, etc.)
- **Testable** with mock adapters
- **Extensible** for new data sources
- **Consistent** interface across adapters

## Industry standard patterns

### Repository pattern

```python
class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_uuid(self, asset_uuid: UUID) -> Optional[Asset]:
        return self.db.query(Asset).filter(Asset.uuid == asset_uuid).first()

    def save(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self.db.flush()
        return asset
```

### Service layer pattern

```python
class LibraryService:
    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db)

    def register_asset(self, uri: str, metadata: dict) -> Asset:
        # Business logic coordination
        asset = Asset(uri=uri, state="new", **metadata)
        return self.asset_repo.save(asset)
```

### Factory pattern for complex objects

```python
class StreamingPipelineFactory:
    @staticmethod
    def create_mpegts_pipeline(config: StreamingConfig) -> StreamingPipeline:
        return StreamingPipeline(
            ffmpeg_cmd=FFmpegCommandBuilder(config),
            watchdog=StreamWatchdog(config),
            health_checker=TSHealthChecker()
        )
```

## Interface design patterns

### API vs CLI vs web separation

#### API layer (`api/`)

- **FastAPI** for REST endpoints
- **Pydantic** for request/response validation
- **Dependency injection** for services
- **Automatic OpenAPI** documentation

#### CLI layer (`cli/`)

- **Typer** for command-line interface
- **Same services** as API layer
- **JSON output** for scripting
- **Human-readable** output for users

#### Web layer (`web/`)

- **Jinja2** templates for HTML
- **Same API endpoints** as REST API
- **Bootstrap** for responsive design
- **Progressive enhancement** with JavaScript

### Consistent error handling

```python
# Standardized error responses
class RetrovueError(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code

class ValidationError(RetrovueError):
    pass

class NotFoundError(RetrovueError):
    pass
```

### Configuration management

```python
# Environment-based configuration with validation
class Settings(BaseSettings):
    database_url: str
    plex_server_url: str
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Data flow patterns

### Content ingestion flow

```
External Source → Importer → Enricher → Domain Entities → Database
     ↓              ↓           ↓            ↓
  Plex API    FilesystemImporter  FFProbeEnricher  Asset/Episode
```

### API request flow

```
HTTP Request → FastAPI Router → Service Layer → Domain Layer → Database
     ↓              ↓              ↓             ↓
  JSON Input    Business Logic   Domain Rules   SQLAlchemy
```

### CLI command flow

```
CLI Command → Typer Router → Service Layer → Domain Layer → Database
     ↓            ↓              ↓             ↓
  Arguments   Business Logic   Domain Rules   SQLAlchemy
```

## Testing patterns

### Unit testing

```python
# Test domain logic in isolation
def test_asset_creation():
    asset = Asset(uri="file://test.mp4", size=1000, state="new")
    assert asset.state == "new"
    assert asset.approved_for_broadcast is False
    assert asset.uri == "file://test.mp4"
```

### Integration testing

```python
# Test service orchestration
def test_library_service_register_asset():
    with session() as db:
        service = LibraryService(db)
        asset = service.register_asset("file://test.mp4", {})
        assert asset.uuid is not None
```

### End-to-end testing

```python
# Test complete workflows
def test_api_asset_creation():
    response = client.post("/api/assets", json={"uri": "file://test.mp4"})
    assert response.status_code == 201
    assert response.json()["uri"] == "file://test.mp4"
```

## Monitoring and observability

### Structured logging

```python
# Consistent logging across all layers
logger = structlog.get_logger()

logger.info("Asset created", asset_uuid=asset.uuid, uri=asset.uri, state=asset.state)
logger.error("Ingest failed", source=source, error=str(e))
```

### Health checks

```python
# System health monitoring
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": check_database_connection(),
        "services": check_service_health()
    }
```

### Metrics collection

```python
# Performance and usage metrics
@router.get("/metrics")
def get_metrics():
    return {
        "assets_count": count_assets(),
        "ingest_rate": calculate_ingest_rate(),
        "error_rate": calculate_error_rate()
    }
```

## Extension patterns

### Adding new importers

```python
# 1. Implement base interface
class CustomImporter(BaseImporter):
    def discover_content(self, source: str) -> list[ContentItem]:
        # Implementation
        pass

# 2. Register in registry
registry.register("custom", CustomImporter)
```

### Adding new API endpoints

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

### Adding new CLI commands

```python
# 1. Create command function
@cli.command()
def custom_command():
    """Custom command description."""
    # Implementation
    pass

# 2. Register in main CLI
cli.add_command(custom_command)
```

## Best practices

### Code organization

- **Layer separation**: Keep domain, application, and infrastructure separate
- **Single responsibility**: Each class/function has one clear purpose
- **Dependency injection**: Use constructor injection for dependencies
- **Interface segregation**: Small, focused interfaces

### Error handling

- **Fail fast**: Validate inputs early
- **Graceful degradation**: Handle errors without crashing
- **Consistent responses**: Standardized error formats
- **Logging**: Comprehensive error logging

### Performance

- **Lazy loading**: Load data only when needed
- **Connection pooling**: Efficient database connections
- **Caching**: Cache expensive operations
- **Async operations**: Use async for I/O-bound tasks

### Security

- **Input validation**: Validate all inputs
- **SQL injection prevention**: Use parameterized queries
- **Secret management**: Never hardcode secrets
- **Access control**: Implement proper authorization

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Patterns](https://docs.sqlalchemy.org/)
- [Pydantic Validation](https://pydantic-docs.helpmanual.io/)
- [Typer CLI Framework](https://typer.tiangolo.com/)

---

_These architectural guidelines ensure consistency, maintainability, and extensibility across all RetroVue components while following industry best practices._
