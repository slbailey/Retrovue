# 📺 Retrovue - Retro IPTV Simulation Project

## 🎬 Inspiration
Inspired by **RetroTV Live 24/7 Vintage Cable TV Network on Raspberry Pi**, this project takes the concept further:  
Instead of a single-device solution, it will build a **network-grade IPTV system** that integrates with Plex Live TV and serves multiple viewers.

---

## 🏗️ Project Goals
Simulate a realistic broadcast TV station experience:
- 📡 Channels with playout schedules  
- 📺 Commercials, intros/outros, bumpers  
- ⚠️ Emergency alert overrides  
- 🎨 Graphics overlays (bugs, lower thirds, branding)  
- 🌐 Deliver streams as HLS playlists (`.m3u8` + segments) consumable by Plex and VLC  
- 🖥️ Provide a management UI for metadata and scheduling  

---

## 📐 System Architecture
**Program Director** (Top-level Controller)  
├─ **Channel Management**  
│  └─ Multiple Channels  
│     ├─ Schedule Manager  
│     ├─ Pipeline Manager  
│     ├─ Graphics Manager  
│     └─ Playback Pipeline  
│  
└─ **Shared Resources**  
  ├─ Content Manager  
  └─ Emergency System  

**Components:**
- **Program Director** – Orchestrates all channels, manages state, coordinates emergencies.  
- **Channel** – Independent broadcast unit with schedule + pipeline.  
- **Schedule Manager** – Maintains coarse (show-level) and fine (break-level) logs.  
- **Pipeline Manager** – Controls playback transitions and timing.  
- **Graphics Manager** – Overlays bugs, branding, emergency graphics.  
- **Content Manager (Shared)** – Ingests and validates assets, stores metadata, distributes to channels.  
- **Emergency System (Shared)** – Provides priority alerts across all channels.  

---

## 📂 Media & Metadata Strategy
- All existing media lives in **Plex** or is tagged with **TinyMediaManager** metadata.  
- Project will:  
  - Store only **playback-relevant metadata** (schedules, playout history, commercial timing).  
  - Reference series/episode metadata from Plex or sidecar files (avoid duplication).  
- 🎯 Goal: A **unified UI for editing scheduling metadata**, not a full media manager.  

---

## 🎛️ Playback Engine
- Core technology: **ffmpeg** → segment + encode into HLS  
- Segments delivered as `.ts` or `fmp4` with rotating `master.m3u8`  
- **Phase 1:** Single-channel with scripted ffmpeg command  
- **Phase 2+:** Multi-channel orchestration + advanced playout logic  
- Deployment: **Docker containers** for isolation and portability  

---

## 🖥️ Management UI
Desktop UI in **Python** (PySide6 / PyQt / Tkinter).  
Features:  
- Media ingestion (browse Plex / TinyMediaManager)  
- Metadata editing (runtime, bumpers, commercial breakpoints)  
- Coarse + fine schedule views  
- Log viewing + error monitoring  

---

## 🚦 Development Roadmap
**Phase 1 — Proof of Concept** ✅
- [x] Build single-channel playout (`ffmpeg → HLS → VLC`)  
- [x] Solve segment rotation issues (`-hls_delete_threshold`, epoch numbering)  
- [x] Validate continuous playback via local HTTP server  

**Phase 2 — Core System**
- [ ] Implement Program Director + Channel classes  
- [ ] Add SQLite database for schedules + playback metadata  
- [ ] Prototype minimal metadata editor UI  

**Phase 3 — Expansion**
- [ ] Multi-channel support  
- [ ] Graphics overlay engine  
- [ ] Emergency broadcast injection  
- [ ] Advanced scheduling (commercials, bumpers, promos)  
- [ ] Plex Live TV integration

---

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg installed and in PATH
- Media file for streaming

### Running the Server

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the server (simple loop mode - default)
python main.py

# Or use ErsatzTV-style concat mode
python main.py --mode concat

# Custom options
python main.py --mode concat --loops 10 --port 8081
```

### Testing the Stream
1. Open VLC Media Player
2. Go to: Media → Open Network Stream
3. Enter: `http://localhost:8080/channel/1.ts`
4. Click Play

The stream will loop seamlessly forever with proper timestamp handling.  

---

## 📁 Project Structure

```
Retrovue/
├── main.py                    # Main server script (unified entry point)
├── requirements.txt           # Python dependencies
├── venv/                      # Python virtual environment
└── src/                      # Retrovue framework
    └── retrovue/
        ├── __init__.py
        ├── version.py
        └── core/
            ├── __init__.py
            └── streaming.py   # Core streaming components
```

### Main Server (`main.py`)
- **Unified entry point** for all streaming modes
- **Command-line interface** with multiple options
- **Framework-based** implementation using `src/retrovue/core/`

### Framework Components (`src/retrovue/core/streaming.py`)
- **`ConcatDemuxerStreamer`**: ErsatzTV-style streaming using `-f concat` demuxer
- **`SimpleLoopStreamer`**: Simple streaming using `-stream_loop -1`
- **`StreamHandler`**: Base HTTP handler for streaming endpoints
- **`GracefulHTTPServer`**: HTTP server with graceful client disconnection handling

---

## 📋 Key Lessons (from early testing)
- VLC fails if opening `.m3u8` as a file → must serve via HTTP  
- Segments must not be deleted too aggressively → use `-hls_delete_threshold`  
- Use `-hls_start_number_source epoch` or timestamped filenames to avoid index reuse  
- Always re-encode with regular GOP/keyframes for clean segmenting  

---

## 🛠️ Tech Stack
- **Playback:** ffmpeg, Docker  
- **Management UI:** Python (PySide6 / Tkinter)  
- **Database:** SQLite (initial)  
- **Serving:** Python FastAPI / lightweight HTTP server  
- **Clients:** Plex Live TV, VLC  

---

## 🎯 End Goal
Retrovue aims to be a **robust IPTV-ready simulation** of a professional broadcast television station:
- Multi-channel 24/7 operation  
- Realistic transitions and timing  
- Viewer experience **indistinguishable from real cable TV**  
- Easy-to-use management interface  
