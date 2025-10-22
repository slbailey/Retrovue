# Retrovue Architecture

## Overview

Retrovue follows a layered architecture pattern that separates concerns and provides clear boundaries between different parts of the system. The architecture is designed to be maintainable, testable, and extensible.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   FastAPI       │  │   REST API      │  │   Web UI    │  │
│  │   Routers       │  │   Endpoints     │  │   (Future)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Content       │  │   Import        │  │  Library   │  │
│  │   Services      │  │   Services      │  │  Services   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Entities      │  │   Value         │  │  Domain    │  │
│  │   (Title, etc.) │  │   Objects       │  │  Events    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Adapters Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Plex          │  │   Jellyfin      │  │  File      │  │
│  │   Importer      │  │   Importer      │  │  System    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Database      │  │   Logging       │  │  Settings   │  │
│  │   (SQLAlchemy)  │  │   (structlog)   │  │  (Pydantic)│  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### API Layer (`src/retrovue/api/`)

- **Purpose**: Handles HTTP requests and responses
- **Responsibilities**:
  - FastAPI routers and endpoints
  - Request/response serialization
  - API documentation
  - Authentication and authorization
- **Dependencies**: Application layer only

### Application Layer (`src/retrovue/app/`)

- **Purpose**: Orchestrates business use cases
- **Responsibilities**:
  - Business logic coordination
  - Use case implementation
  - Transaction management
  - Service orchestration
- **Dependencies**: Domain layer, Adapters layer

### Domain Layer (`src/retrovue/domain/`)

- **Purpose**: Contains core business logic
- **Responsibilities**:
  - Business entities (Title, Episode, Asset)
  - Value objects (GUID, Path, etc.)
  - Domain events
  - Business rules and invariants
- **Dependencies**: None (pure business logic)

### Adapters Layer (`src/retrovue/adapters/`)

- **Purpose**: Integrates with external systems
- **Responsibilities**:
  - Plex integration
  - Jellyfin integration
  - Filesystem integration
  - External API clients
  - Data enrichment services
- **Dependencies**: Domain layer, Infrastructure layer

### Infrastructure Layer (`src/retrovue/infra/`)

- **Purpose**: Provides technical infrastructure
- **Responsibilities**:
  - Database access (SQLAlchemy)
  - Logging (structlog)
  - Configuration (Pydantic)
  - Metrics (Prometheus)
  - File system operations
- **Dependencies**: None (technical concerns only)

### CLI Layer (`src/retrovue/cli/`)

- **Purpose**: Command-line interface
- **Responsibilities**:
  - Typer command definitions
  - CLI argument parsing
  - Command orchestration
- **Dependencies**: Application layer only

### Shared Layer (`src/retrovue/shared/`)

- **Purpose**: Common utilities and types
- **Responsibilities**:
  - Shared types and enums
  - Utility functions
  - Common exceptions
  - Cross-cutting concerns
- **Dependencies**: None (pure utilities)

## Key Principles

1. **Dependency Inversion**: High-level modules don't depend on low-level modules
2. **Single Responsibility**: Each layer has a clear, focused responsibility
3. **Interface Segregation**: Dependencies are on interfaces, not implementations
4. **Open/Closed**: Open for extension, closed for modification
5. **Don't Repeat Yourself**: Shared functionality goes in the shared layer

## Data Flow

1. **API Requests**: HTTP → API Layer → Application Layer → Domain/Adapters
2. **CLI Commands**: CLI → Application Layer → Domain/Adapters
3. **Import Process**: Adapters → Domain → Application → Infrastructure
4. **Business Logic**: Application → Domain → Adapters → Infrastructure

## Migration Strategy

The existing codebase will be gradually migrated to this architecture:

1. **Phase 1**: Create new layer structure (✅ Complete)
2. **Phase 2**: Implement domain models and ORM
3. **Phase 3**: Create application services facade
4. **Phase 4**: Implement plugin interfaces for importers
5. **Phase 5**: Build ingest pipeline and review queue
6. **Phase 6**: Migrate CLI to use application services
7. **Phase 7**: Add configuration, logging, and metrics
8. **Phase 8**: Implement HLS output contract
9. **Phase 9**: Complete documentation and examples

## Benefits

- **Maintainability**: Clear separation of concerns
- **Testability**: Each layer can be tested independently
- **Extensibility**: New importers and features can be added easily
- **Flexibility**: Can swap implementations without affecting business logic
- **Scalability**: Architecture supports future growth and complexity
