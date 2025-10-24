# 📚 Retrovue Documentation

Welcome to the Retrovue documentation! This documentation is organized around the core components of the system, making it easy to understand both the business purpose and technical implementation of each component.

## 🏗️ Documentation Architecture

Our documentation follows a component-based architecture that mirrors the system's design:

```
┌─────────────────────────────────────────────────────────────┐
│                    Architectural Guidelines               │
├─────────────────────────────────────────────────────────────┤
│  Design Patterns  │  Industry Standards  │  Best Practices │
├─────────────────────────────────────────────────────────────┤
│                    Core Components                         │
├─────────────────────────────────────────────────────────────┤
│  Content Management  │  Program Manager  │  Channel Manager │
├─────────────────────────────────────────────────────────────┤
│                    User Documentation                     │
├─────────────────────────────────────────────────────────────┤
│  Getting Started  │  User Guides  │  Configuration  │  FAQ  │
├─────────────────────────────────────────────────────────────┤
│                    Technical Documentation                 │
├─────────────────────────────────────────────────────────────┤
│  API Reference  │  CLI Reference  │  Database  │  Streaming │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### For Users

- **[Getting Started](user/getting-started.md)** - Set up Retrovue in 6 simple steps
- **[Web Interface Guide](user/web-interface.md)** - Use the modern web UI
- **[Configuration Guide](user/configuration.md)** - Configure your system

### For Developers

- **[Architecture Overview](developer/architecture.md)** - Understand the system design
- **[API Reference](developer/api-reference.md)** - Complete API documentation
- **[CLI Reference](developer/cli-reference.md)** - Command-line interface guide

## 📖 Documentation Sections

### 🏗️ Architectural Guidelines

Core architectural patterns, design principles, and industry standards:

- **[Architectural Guidelines](components/architectural-guidelines.md)** - Design patterns, UoW, FastAPI, Clean Architecture
- **[Design Principles](components/architectural-guidelines.md#design-principles)** - Dependency inversion, single responsibility, open/closed
- **[Industry Standards](components/architectural-guidelines.md#industry-standard-patterns)** - Repository pattern, service layer, factory pattern
- **[Best Practices](components/architectural-guidelines.md#best-practices)** - Code organization, error handling, performance, security

### 🧩 Core Components

Business-level explanations and technical implementation for each system component:

#### Content Management System

- **[Content Management System](components/content-management-system.md)** - Content discovery, ingestion, and library management
- **[Review System](components/content-management-system.md#review-system)** - Quality assurance and human review workflow
- **[CLI Interface](components/content-management-system.md#cli-interface)** - Command-line content management
- **[Web Interface](components/content-management-system.md#web-interface)** - Web-based content management

#### Program Manager

- **[Program Manager](components/program-manager.md)** - Programming creation, scheduling, and content rotation
- **[Schedule Generation](components/program-manager.md#schedule-generation)** - Automatic programming schedule creation
- **[Content Rotation](components/program-manager.md#content-rotation)** - Content distribution and rotation rules
- **[Programming Patterns](components/program-manager.md#program-types)** - Series, movie, and block programming

#### Channel Manager

- **[Channel Manager](components/channel-manager.md)** - IPTV channel creation, configuration, and management
- **[Multi-Channel Management](components/channel-manager.md#multi-channel-management)** - Orchestrating multiple channels
- **[Stream Management](components/channel-manager.md#streaming-infrastructure)** - FFmpeg integration and stream health
- **[Resource Allocation](components/channel-manager.md#resource-allocation)** - System resource management

### 👥 User Documentation

Everything you need to use Retrovue effectively:

- **[Getting Started](user/getting-started.md)** - Complete setup guide
- **[Web Interface](user/web-interface.md)** - Modern web UI guide
- **[Configuration](user/configuration.md)** - System configuration
- **[Content Management](user/content-management.md)** - Managing your media library
- **[Streaming](user/streaming.md)** - Setting up and using streams
- **[Troubleshooting](user/troubleshooting.md)** - Common issues and solutions
- **[FAQ](user/faq.md)** - Frequently asked questions

### 👨‍💻 Developer Documentation

Technical documentation for developers and contributors:

- **[Architecture](developer/architecture.md)** - System architecture and design patterns
- **[API Reference](developer/api-reference.md)** - Complete REST API documentation
- **[CLI Reference](developer/cli-reference.md)** - Command-line interface reference
- **[Database Schema](developer/database-schema.md)** - Database design and relationships
- **[Testing](developer/testing.md)** - Testing strategies and guidelines
- **[Contributing](developer/contributing.md)** - How to contribute to the project

### 🔧 Technical Documentation

Deep technical details for system administrators and advanced users:

- **[Streaming Engine](technical/streaming-engine.md)** - FFmpeg and HLS implementation
- **[Plex Integration](technical/plex-integration.md)** - Plex server integration details
- **[Database Management](technical/database-management.md)** - Database operations and maintenance
- **[Deployment](technical/deployment.md)** - Production deployment guide
- **[Performance](technical/performance.md)** - Performance tuning and optimization
- **[Security](technical/security.md)** - Security considerations and best practices

## 🎯 Find What You Need

### I want to...

#### Understand the System

- **Learn the architecture** → [Architectural Guidelines](components/architectural-guidelines.md)
- **Understand content management** → [Content Management System](components/content-management-system.md)
- **Learn about programming** → [Program Manager](components/program-manager.md)
- **Understand channels** → [Channel Manager](components/channel-manager.md)

#### Get Started

- **Set up Retrovue for the first time** → [Getting Started](user/getting-started.md)
- **Use the web interface** → [Web Interface Guide](user/web-interface.md)
- **Configure my system** → [Configuration Guide](user/configuration.md)

#### Manage Content

- **Import content from Plex** → [Content Management](user/content-management.md)
- **Review content quality** → [Review System](components/content-management-system.md#review-system)
- **Organize my library** → [Content Management System](components/content-management-system.md)

#### Create Programming

- **Build program schedules** → [Program Manager](components/program-manager.md)
- **Set up content rotation** → [Content Rotation](components/program-manager.md#content-rotation)
- **Create programming blocks** → [Programming Patterns](components/program-manager.md#program-types)

#### Manage Channels

- **Create IPTV channels** → [Channel Manager](components/channel-manager.md)
- **Start streaming** → [Streaming Guide](user/streaming.md)
- **Monitor channel health** → [Stream Management](components/channel-manager.md#streaming-infrastructure)

#### Development

- **Use the API** → [API Reference](developer/api-reference.md)
- **Use the CLI** → [CLI Reference](developer/cli-reference.md)
- **Deploy to production** → [Deployment Guide](technical/deployment.md)
- **Troubleshoot issues** → [Troubleshooting Guide](user/troubleshooting.md)

## 📁 File Organization

The documentation is organized into component-based directories:

```
docs/
├── components/     # Core system components
│   ├── architectural-guidelines.md
│   ├── content-management-system.md
│   ├── program-manager.md
│   └── channel-manager.md
├── user/           # User-facing documentation
├── developer/      # Developer documentation
├── technical/     # Technical deep-dives
└── README.md      # This file
```

## 🔄 Documentation Status

- ✅ **Architectural Guidelines** - Complete with design patterns and best practices
- ✅ **Core Components** - Complete with business and technical documentation
- ✅ **User Documentation** - Complete and up-to-date
- ✅ **Developer Documentation** - Complete with architecture details
- 🔄 **Technical Documentation** - In progress, some sections need updates
- ✅ **API Reference** - Complete and comprehensive
- ✅ **CLI Reference** - Complete with examples

## 🤝 Contributing to Documentation

We welcome contributions to improve our documentation! See our [Contributing Guide](developer/contributing.md) for details on how to:

- Report documentation issues
- Suggest improvements
- Submit documentation updates
- Help translate documentation

## 📞 Getting Help

- **Documentation Issues**: [GitHub Issues](https://github.com/slbailey/Retrovue/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/slbailey/Retrovue/discussions)
- **General Questions**: [GitHub Discussions](https://github.com/slbailey/Retrovue/discussions)

---

**Need help finding something?** Check our [Quick Links](#-find-what-you-need) above or use the search function in your documentation viewer.
