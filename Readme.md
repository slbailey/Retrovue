# 📺 Retrovue

_A Retro IPTV Simulation Project_

> “Here, something is always on.”

Retrovue is more than software — it’s a love letter to broadcast television.  
In an age where streaming platforms bury us in endless menus and algorithmic sameness, Retrovue restores what we’ve lost: **the art of timing, surprise, and shared experience.**

It recreates the magic of flipping through channels and stumbling onto something wonderful — a movie halfway through, a forgotten cartoon, or a local station ID you haven’t seen since childhood. Every frame is driven by a living schedule, every break perfectly timed, every bumper and commercial right where it belongs.

## ❤️ Why It Exists

We live in an on-demand world — but constant choice can be exhausting.  
Old television had rhythm. You didn’t scroll, you _tuned in_. You let the world surprise you. Retrovue exists to bring that rhythm back — not through nostalgia alone, but through **precision engineering**.

What began as a hobby project to repurpose an old iPad screen during lockdown evolved into a full-fledged system: a network-grade, modular IPTV engine that behaves like a real broadcast backend. Every minute on every channel follows the rules of a genuine TV network — because _authenticity comes from structure._

## 🧠 The Philosophy

Retrovue is built on a simple belief:

> **Structure is how we build trust — in code, and in community.**

Every module — ingest, schedule, playout, or analytics — obeys strict contracts.  
Those contracts define _what must be true_, not _how it’s done_.  
They make the system testable, modular, and expandable — a living ecosystem of cooperating parts, just like a real broadcast operation.

This discipline makes Retrovue different from hobbyist “shuffle players.” It doesn’t _fake_ live TV; it _becomes_ it.

## ⚙️ The Vision

Imagine building your own cable network — with real channels, daily schedules, commercials, and bumpers — powered entirely by your media collection.  
That’s Retrovue’s heart:

- 📡 Channels that run 24/7 with realistic pacing
- 🧩 Commercial breaks aligned to chapter markers
- 🎬 Intros, IDs, and sign-offs
- 📊 As-run logs, guide channels, and promos
- 🧠 A Program Director that knows what’s airing and when

It’s not just about _what_ plays — it’s about _when._

---

[![CI](https://github.com/slbailey/Retrovue/actions/workflows/ci.yml/badge.svg)](https://github.com/slbailey/Retrovue/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg installed and in PATH
- Plex Media Server (optional, for content import)

### Installation

**Windows (PowerShell):**

```powershell
git clone https://github.com/slbailey/Retrovue.git
cd Retrovue
python -m venv venv
.
env\Scripts\Activate.ps1
pip install -r requirements.txt
python -m retrovue.cli.main --help
```

**macOS/Linux (bash):**

```bash
git clone https://github.com/slbailey/Retrovue.git
cd Retrovue
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m retrovue.cli.main --help
```

## 🧭 Channel Management CLI

**New in 2025:** Retrovue now includes a comprehensive CLI for channel management!

```bash
retrovue channel list
retrovue channel create --name "RetroToons" --timezone "America/New_York"   --grid-size-minutes 30 --grid-offset-minutes 0 --rollover-minutes 360 --active
retrovue channel show --id 1
retrovue channel update --id 1 --name "NewName" --inactive
retrovue channel delete --id 1
```

## 📦 Source Management CLI

**New in 2025:** Modular source management for content discovery!

```bash
retrovue source list
retrovue source list-types
retrovue source add --type plex --help
retrovue source add --type filesystem --help
```

## 🌐 Launch the Web Interface

```bash
python run_admin.py
```

Open **http://localhost:8000** in your browser to manage servers, libraries, and syncs in real time.

## 🎯 Current Status

✅ Content import from Plex  
✅ Library management  
✅ Basic single-channel streaming  
✅ Smart sync with minimal updates

🔄 Coming soon: Multi-channel scheduling, drag-and-drop timeline editor, advanced playout orchestration.

## 📚 Documentation

See `docs/` for:

- [Beginner’s Guide](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DB_SCHEMA.md)
- [CLI Reference](docs/CLI.md)
- [Streaming Engine](docs/streaming-engine.md)
- [Development Roadmap](docs/development-roadmap.md)

## 🏗️ Project Goals

- Simulate real broadcast station flow
- Integrate commercials, bumpers, and station branding
- Handle 24/7 scheduling and as-run logging
- Provide a management UI for everything

## 🛠️ Tech Stack

- Playback: **ffmpeg**, Docker
- Core API: **Python (FastAPI)**
- Database: **SQLite → PostgreSQL (planned)**
- Web UI: **FastAPI + HTML/JS**
- Clients: **Plex Live TV, VLC**

## 🤝 Contributing

We welcome developers, archivists, and nostalgia lovers.  
Read our [Contributing Guide](CONTRIBUTING.md) and check [Good First Issues](https://github.com/slbailey/Retrovue/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

---

_Retrovue: Bringing the magic of retro TV to the modern streaming era._ 📺✨
