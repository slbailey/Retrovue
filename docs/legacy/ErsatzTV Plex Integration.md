# ErsatzTV Plex Synchronization Process - Comprehensive Roadmap

> **Legacy Document** — Pre-Alembic version, retained for reference only.

## Overview

ErsatzTV implements a sophisticated multi-layered architecture for synchronizing with Plex media servers. This document provides a detailed roadmap of the entire synchronization process, from initial discovery to ongoing maintenance.

## Architecture Components

### 1. Core Services

- **PlexService**: Background service managing Plex connections and authentication
- **ScannerService**: Background service orchestrating library scanning operations
- **SchedulerService**: Manages scheduled synchronization tasks

### 2. Scanner Components

- **PlexMovieLibraryScanner**: Handles movie library synchronization
- **PlexTelevisionLibraryScanner**: Handles TV show library synchronization
- **PlexOtherVideoLibraryScanner**: Handles other video content synchronization
- **PlexCollectionScanner**: Handles Plex collection synchronization
- **PlexNetworkScanner**: Handles TV network synchronization

### 3. Infrastructure Components

- **PlexServerApiClient**: Low-level Plex API communication
- **PlexSecretStore**: Manages authentication tokens and secrets
- **PlexPathReplacementService**: Handles path mapping between Plex and local filesystems

## Detailed Synchronization Process

### Phase 1: System Initialization

#### 1.1 Service Startup

```
PlexService.StartAsync()
├── Wait for database initialization
├── Wait for search index initialization
├── Initialize Plex secrets file if not exists
└── Trigger initial source synchronization
```

#### 1.2 Initial Source Discovery

```
SynchronizePlexMediaSources
├── Discover Plex servers via network discovery
├── Authenticate with discovered servers
├── Enumerate available libraries
├── Store connection parameters
└── Register libraries in ErsatzTV database
```

#### 1.3 Library Registration

- Each Plex library is registered with:
  - Library ID and name
  - Media type (Movies, Shows, Other Videos)
  - Connection parameters
  - Last scan timestamp
  - Scan configuration

### Phase 2: Authentication & Connection Management

#### 2.1 Authentication Flow

```
Plex Authentication
├── PIN-based authentication for initial setup
├── Token exchange and storage
├── Token refresh mechanism
└── Connection validation (ping tests)
```

#### 2.2 Connection Parameters

- **PlexConnection**: Server URI, port, SSL settings
- **PlexServerAuthToken**: Authentication token with client identifier
- **PlexConnectionParameters**: Combined connection and token data

### Phase 3: Library Synchronization Trigger

#### 3.1 Synchronization Triggers

1. **Scheduled Sync**: Based on configurable refresh interval
2. **Manual Sync**: User-initiated force scan
3. **Deep Scan**: Full metadata refresh regardless of ETags
4. **Incremental Scan**: ETag-based change detection

#### 3.2 Scan Decision Logic

```
Should Scan Library?
├── Check last scan timestamp
├── Compare with refresh interval
├── Check for force scan flag
└── Determine scan type (deep vs incremental)
```

### Phase 4: Library Content Discovery

#### 4.1 API Communication

```
PlexServerApiClient
├── GetLibraries() - Enumerate available libraries
├── GetMovieLibraryContents() - Fetch movie metadata
├── GetShowLibraryContents() - Fetch TV show metadata
├── GetShowSeasons() - Fetch season information
├── GetSeasonEpisodes() - Fetch episode information
└── GetLibrarySectionContents() - Paginated content retrieval
```

#### 4.2 Pagination Strategy

- Large libraries are processed in pages
- Progress tracking for UI updates
- Memory-efficient streaming of results

### Phase 5: Change Detection & ETag Management

#### 5.1 ETag-Based Change Detection

```
ETag Comparison Process
├── Retrieve existing ETags from database
├── Compare with incoming Plex ETags
├── Identify changed items
├── Skip unchanged items (performance optimization)
└── Process only modified content
```

#### 5.2 Item State Management

- **Normal**: File exists locally and is accessible
- **RemoteOnly**: File only available via Plex streaming
- **Unavailable**: File not accessible locally or remotely
- **FileNotFound**: File was removed from Plex

### Phase 6: Metadata Synchronization

#### 6.1 Metadata Types Synchronized

```
Movie Metadata
├── Basic Info: Title, Plot, Year, Content Rating
├── People: Actors, Directors, Writers
├── Classification: Genres, Studios, Tags
├── Identifiers: GUIDs, External IDs
├── Artwork: Posters, Fan Art, Thumbnails
├── Technical: Subtitles, Chapters
└── Statistics: Duration, File size, Stream info

TV Show Metadata
├── Show Info: Title, Plot, Year, Network
├── Season Info: Season numbers, artwork
├── Episode Info: Episode numbers, titles, plots
├── People: Cast, crew information
├── Classification: Genres, studios, tags
├── Identifiers: GUIDs, external IDs
├── Artwork: Show posters, season posters, episode thumbnails
└── Technical: Subtitles, chapters, stream info
```

#### 6.2 Metadata Update Process

```
UpdateMetadata()
├── Compare existing vs incoming metadata
├── Update changed fields
├── Add new relationships (genres, actors, etc.)
├── Remove obsolete relationships
├── Update artwork if newer
├── Refresh subtitles and chapters
└── Mark metadata as updated with timestamp
```

### Phase 7: File System Integration

#### 7.1 Path Replacement System

```
Path Mapping Process
├── Retrieve Plex internal file paths
├── Apply path replacement rules
├── Map to local filesystem paths
├── Validate file existence
└── Set appropriate item state
```

#### 7.2 File State Determination

```
File State Logic
├── Check if local file exists
├── If exists: Mark as Normal
├── If not exists but remote streaming supported: Mark as RemoteOnly
├── If not exists and no remote streaming: Mark as Unavailable
└── Update database with new state
```

### Phase 8: Database Operations

#### 8.1 Repository Pattern

- **PlexMovieRepository**: Movie-specific database operations
- **PlexTelevisionRepository**: TV show-specific database operations
- **PlexOtherVideoRepository**: Other video database operations
- **MediaSourceRepository**: Media source management
- **MetadataRepository**: Metadata CRUD operations

#### 8.2 Database Transactions

```
Database Operations
├── Begin transaction
├── Insert/Update media items
├── Update metadata relationships
├── Update artwork references
├── Update file states
├── Update ETags
└── Commit transaction
```

### Phase 9: Progress Reporting & UI Updates

#### 9.1 Progress Tracking

```
ScannerProgressUpdate Events
├── Library-level progress (percentage complete)
├── Item-level updates (items added/updated)
├── Error reporting
└── Completion notifications
```

#### 9.2 Real-time Updates

- Progress updates sent via MediatR events
- UI receives real-time scanning progress
- Error notifications for failed items
- Completion status for each library

### Phase 10: Error Handling & Recovery

#### 10.1 Error Categories

- **Network Errors**: Connection timeouts, server unavailable
- **Authentication Errors**: Token expiration, invalid credentials
- **Data Errors**: Malformed metadata, missing required fields
- **File System Errors**: Path mapping failures, permission issues

#### 10.2 Recovery Strategies

```
Error Recovery
├── Retry failed operations with exponential backoff
├── Log detailed error information
├── Continue processing other items
├── Report errors to UI
└── Maintain partial synchronization state
```

### Phase 11: Cleanup & Maintenance

#### 11.1 Orphaned Item Cleanup

```
Cleanup Process
├── Identify items no longer in Plex
├── Mark as FileNotFound
├── Remove from active playlists
├── Archive metadata for potential recovery
└── Update database state
```

#### 11.2 Performance Optimization

- **Incremental Scanning**: Only process changed items
- **Batch Operations**: Group database updates
- **Memory Management**: Stream large datasets
- **Concurrent Processing**: Parallel library scanning

## Data Flow Diagram

```
[Plex Server]
    ↓ (API Calls)
[PlexServerApiClient]
    ↓ (Raw Data)
[Library Scanners]
    ↓ (Processed Data)
[Repository Layer]
    ↓ (Database Operations)
[ErsatzTV Database]
    ↓ (State Updates)
[UI Components]
```

## Configuration Options

### Library Refresh Settings

- **Refresh Interval**: How often to scan libraries (hours)
- **Deep Scan**: Force full metadata refresh
- **Path Replacements**: Custom path mapping rules
- **Remote Streaming**: Enable/disable remote access

### Performance Tuning

- **Concurrent Scans**: Number of simultaneous library scans
- **Batch Size**: Items processed per batch
- **Timeout Settings**: API call timeouts
- **Retry Logic**: Failed operation retry attempts

## Monitoring & Logging

### Logging Levels

- **Debug**: Detailed operation tracing
- **Info**: General operation status
- **Warning**: Non-fatal errors and issues
- **Error**: Fatal errors requiring attention

### Key Metrics

- **Scan Duration**: Time to complete library scans
- **Items Processed**: Number of items synchronized
- **Error Rate**: Percentage of failed operations
- **Memory Usage**: Resource consumption during scans

## Security Considerations

### Authentication

- **Token Management**: Secure storage and rotation
- **Connection Security**: SSL/TLS for API communication
- **Access Control**: User permission validation

### Data Privacy

- **Local Storage**: Sensitive data encryption
- **Network Security**: Secure API communication
- **Audit Logging**: Track access and modifications

## Troubleshooting Guide

### Common Issues

1. **Authentication Failures**: Check token validity and server connectivity
2. **Path Mapping Errors**: Verify path replacement rules
3. **Metadata Inconsistencies**: Check for Plex server issues
4. **Performance Problems**: Review scan intervals and batch sizes

### Diagnostic Tools

- **Connection Testing**: Ping Plex servers
- **Token Validation**: Verify authentication status
- **Path Verification**: Test file system access
- **Log Analysis**: Review detailed operation logs

## Future Enhancements

### Planned Features

- **Real-time Sync**: WebSocket-based live updates
- **Selective Sync**: Choose specific libraries/content
- **Advanced Filtering**: Content-based sync rules
- **Performance Analytics**: Detailed scan metrics

### Scalability Improvements

- **Distributed Scanning**: Multi-instance coordination
- **Caching Layer**: Reduce API calls
- **Incremental Metadata**: Delta-based updates
- **Background Processing**: Non-blocking operations

This roadmap provides a comprehensive view of ErsatzTV's Plex synchronization process, from high-level architecture to implementation details. The system is designed for reliability, performance, and maintainability while providing extensive configurability for different deployment scenarios.
