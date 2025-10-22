# 📚 Retrovue Documentation Index

Welcome to the Retrovue documentation! This index will help you find exactly what you need.

---

## 🚀 Getting Started

- **[Quick Start Guide](quick-start.md)** - Get Retrovue up and running in minutes
- **[Beginner's Guide (README)](README.md)** - Understand what Retrovue does and how it works

---

## 📖 Core Documentation

### Architecture & Design

- **[System Architecture](architecture.md)** - How all the pieces fit together
- **[Database Schema](database-schema.md)** - Data models and table structures
- **[Development Roadmap](development-roadmap.md)** - Current status and future plans

### Features & Components

- **[Plex Sync CLI](plex-sync-cli.md)** - Command-line interface for Plex integration
- **[Streaming Engine](streaming-engine.md)** - Video delivery and playout

---

## 🖥️ GUI Documentation

- **[GUI Migration Notes](../MIGRATION_NOTES.md)** - Complete history of GUI modularization (Phases 1-8)
- **[Phase 7 Improvements](../PHASE_7_IMPROVEMENTS.md)** - Feature-by-feature improvements in Phase 7
- **[Phase 8 Plan](../PHASE_8_PLAN.md)** - Scheduling UI placeholder planning
- **[Progress Improvements](../PROGRESS_IMPROVEMENTS.md)** - Real-time progress feedback details

### GUI Architecture

The new modular Qt GUI follows this structure:

```
src/retrovue/
├── gui/                    # PySide6/Qt GUI
│   ├── app.py             # Main application window
│   ├── router.py          # Page registry
│   ├── store.py           # Shared state
│   ├── threads.py         # Worker threads
│   └── features/          # Feature-specific pages
│       ├── importers/     # Plex import workflow
│       └── schedules/     # Scheduling (placeholder)
└── core/                  # Business logic
    ├── api.py             # Unified API façade
    ├── servers.py         # Server management
    ├── libraries.py       # Library management
    └── sync.py            # Content synchronization
```

---

## 🔧 Technical Documentation

### Plex Integration

- **[Plex Integration Overview](Plex Integration/Retrovuew Plex Integration.md)** - How Retrovue integrates with Plex
- **[Plex Rework Roadmap](Plex Integration/Plex Rework Roadmap.md)** - Plex feature planning
- **[Gap Analysis](Plex Integration/Retrovue Gap Analysis.md)** - Feature comparison with ErsatzTV

### UI Design Documents

- **[UI Core Concepts](UI/RetroVue_UI_Core.md)** - Core UI architecture
- **[Ingest Module Design](UI/RetroVue_UI_Ingest_Module_v0.1.md)** - Content import UI
- **[Schedule Module Design](UI/RetroVue_UI_Schedule_Module_v0.1.md)** - Scheduling UI concepts
- **[Content Browser TODO](UI/Content_Browser_TODO.md)** - Future content browser plans

---

## 🤝 Contributing

- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to Retrovue
- **[License](../LICENSE)** - MIT License

---

## 🐛 Bug Fixes & Improvements

- **[Limitations Fixed](../LIMITATIONS_FIXED.md)** - Bugs fixed in Phase 7
- **[Phase 7 Complete](../PHASE_7_COMPLETE.md)** - Comprehensive Phase 7 summary
- **[Phase 7 Final Summary](../PHASE_7_FINAL_SUMMARY.md)** - Phase 7 wrap-up
- **[Phase 8 Complete](../PHASE_8_COMPLETE.md)** - Phase 8 completion summary

---

## 📝 Configuration

- **[Environment Variables Example](env.example)** - Sample .env configuration
- Configuration is documented in the main [README](../Readme.md#configuration--secrets-management)

---

## 🔍 Quick Links by Topic

### I want to...

- **Set up Retrovue for the first time** → [Quick Start Guide](quick-start.md)
- **Import content from Plex** → [Plex Sync CLI](plex-sync-cli.md)
- **Understand the architecture** → [System Architecture](architecture.md)
- **See what's planned** → [Development Roadmap](development-roadmap.md)
- **Contribute to the project** → [Contributing Guide](../CONTRIBUTING.md)
- **Learn about the GUI** → [GUI Migration Notes](../MIGRATION_NOTES.md)
- **Report a bug or request a feature** → [GitHub Issues](https://github.com/slbailey/Retrovue/issues)

---

## 📌 File Locations

All documentation is organized in the following structure:

```
Retrovue/
├── Readme.md                      # Main project README
├── MIGRATION_NOTES.md             # GUI modularization history
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
└── documentation/                 # Organized documentation
    ├── INDEX.md                   # This file
    ├── README.md                  # Beginner's guide
    ├── quick-start.md
    ├── architecture.md
    ├── database-schema.md
    ├── development-roadmap.md
    ├── plex-sync-cli.md
    ├── streaming-engine.md
    ├── Plex Integration/          # Plex-specific docs
    └── UI/                        # UI design docs
```

---

**Need help?** [Open an issue](https://github.com/slbailey/Retrovue/issues) or check the [Contributing Guide](../CONTRIBUTING.md).
