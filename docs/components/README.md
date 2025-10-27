# Components Documentation

This directory contains **technical architecture documentation** for RetroVue's system components and implementation patterns. These documents describe **how** the system is built and organized to implement the business concepts defined in the domain documentation.

## Purpose

The `components/` directory serves as the **technical implementation guide** for understanding:

- **How** system components work together
- **What** technical patterns and architectures are used
- **How** domain concepts are implemented in code
- **What** interfaces and protocols components follow

This complements the `docs/domain/` directory by providing the technical implementation details that bring domain concepts to life.

## Relationship to Domain Documentation

| `docs/domain/`                    | `docs/components/`                                       |
| --------------------------------- | -------------------------------------------------------- |
| **WHAT** the system represents    | **HOW** the system implements it                         |
| Business entities (Asset, Source) | Technical components (Content Manager, Streaming Engine) |
| Conceptual models                 | Implementation architecture                              |
| Business rules                    | Technical patterns                                       |

## Core Component Categories

### Content Management Components

- **[content-manager.md](content-manager.md)** - Library discovery and management system
- **[importers.md](importers.md)** - Content discovery from external sources (Plex, filesystem)
- **[enrichers.md](enrichers.md)** - Metadata enhancement and content processing
- **[assets.md](assets.md)** - Asset management and processing

### Streaming & Playout Components

- **[streaming-engine.md](streaming-engine.md)** - FFmpeg-based MPEG-TS streaming
- **[playout.md](playout.md)** - Content playback and channel management
- **[mpegts-streaming.md](mpegts-streaming.md)** - MPEG Transport Stream implementation
- **[streaming-pipeline-concepts.md](streaming-pipeline-concepts.md)** - Streaming architecture concepts

### System Architecture

- **[architectural-guidelines.md](architectural-guidelines.md)** - Core design patterns and principles
- **[plex-cli.md](plex-cli.md)** - Plex integration and CLI operations

## Key Architectural Patterns

### Clean Architecture Implementation

The components follow Clean Architecture principles:

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

### Component Interfaces

Components implement standardized interfaces:

- **Importers**: `Importer(Protocol)` for content discovery
- **Enrichers**: `Enricher(Protocol)` for metadata enhancement
- **Producers**: Base classes for playout plan generation
- **Services**: Business logic orchestration

## How to Use This Documentation

### For Developers

1. **Start with [architectural-guidelines.md](architectural-guidelines.md)** - Understand the overall patterns
2. **Read component-specific docs** - Understand how each component works
3. **Follow the interfaces** - Implement components using defined protocols
4. **Reference domain docs** - Ensure implementation matches business concepts

### For System Architects

1. **Study the architecture** - Understand how components interact
2. **Review patterns** - See how Clean Architecture is applied
3. **Plan integrations** - Understand component boundaries
4. **Design extensions** - Follow established patterns for new components

### For DevOps/Operations

1. **Focus on streaming components** - Understand the runtime architecture
2. **Review infrastructure patterns** - See how external systems integrate
3. **Understand deployment** - See how components are organized

## Implementation Guidelines

### Component Development

When implementing new components:

1. **Follow domain concepts** - Implement the business logic defined in `docs/domain/`
2. **Use established patterns** - Follow Clean Architecture and protocol patterns
3. **Implement interfaces** - Use the defined protocols (Importer, Enricher, etc.)
4. **Document behavior** - Update component docs when adding new functionality

### Integration Patterns

Components integrate through:

- **Protocol interfaces** - Standardized contracts between components
- **Event-driven communication** - Loose coupling through events
- **Service orchestration** - Application layer coordinates component interactions
- **Dependency injection** - Components receive dependencies rather than creating them

## Document Structure

Each component document follows a consistent structure:

- **Overview** - What the component does
- **Architecture** - How it's organized internally
- **Interfaces** - How other components interact with it
- **Implementation** - Technical details and patterns
- **Related components** - Cross-references to other components

## Critical Implementation Rules

Several rules guide component implementation:

1. **Domain Alignment**: Components must implement domain concepts correctly
2. **Interface Compliance**: Components must implement defined protocols
3. **Separation of Concerns**: Components have single, well-defined responsibilities
4. **Dependency Direction**: Dependencies point inward toward the domain layer

## Related Documentation

- **[Domain Documentation](../domain/)** - Business concepts and entities
- **[Runtime Documentation](../runtime/)** - How components operate at runtime
- **[Developer Documentation](../developer/)** - Implementation guides and patterns
- **[Contract Documentation](../contracts/)** - Behavioral specifications

---

**Note**: This component documentation describes **how** the system is implemented. It should align with the domain concepts defined in `docs/domain/`. When domain concepts change, component documentation should be updated to reflect the new implementation requirements.



