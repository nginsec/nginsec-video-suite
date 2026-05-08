<div align="center">

<img src="https://img.shields.io/badge/nginsec-Video%20Cloud%20Suite-06b6d4?style=for-the-badge&labelColor=0a0e1a" />

# nginsec Video Cloud Suite

### Professional YouTube Downloader · Desktop & Web Edition

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Latest-FF0000?style=flat-square&logo=youtube&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?style=flat-square&logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Version](https://img.shields.io/badge/Version-1.0.0-brightgreen?style=flat-square)

</div>

---

## Overview

**nginsec Video Cloud Suite** is a dual-mode YouTube downloader — a **desktop GUI app** (CustomTkinter) and a **self-hosted web app** (Flask + Socket.io) that can be shared publicly via Ngrok. Both modes are powered by yt-dlp and FFmpeg, supporting up to 4K video and 320 kbps MP3 audio.

---

## Features

| Feature | Desktop | Web |
|---|:---:|:---:|
| 4K / 1080p / 720p video | ✓ | ✓ |
| MP3 320 kbps audio extraction | ✓ | ✓ |
| Real-time progress bar | ✓ | ✓ (Socket.io) |
| Password / access key protection | — | ✓ |
| Shareable via Ngrok | — | ✓ |
| Thumbnail + metadata download | ✓ | — |
| Dark-themed UI | ✓ | ✓ |

---

## Project Structure

```
nginsec-video-suite/
│
├── main.py                 # Desktop app entry point
├── ui.py                   # CustomTkinter GUI
├── download_manager.py     # yt-dlp download engine
├── config.py               # App configuration & constants
├── requirements.txt        # Desktop dependencies
│
└── web/                    # Web Edition
    ├── app.py              # Flask + Socket.io backend
    ├── requirements.txt    # Web dependencies
    └── templates/
        └── index.html      # Dark-themed SPA frontend
```

---

## Quick Start

### Desktop App

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install FFmpeg  (required for 1080p+)
winget install Gyan.FFmpeg        # Windows
brew install ffmpeg               # macOS
sudo apt install ffmpeg           # Linux

# 3. Launch
python main.py
```

### Web Edition (local + Ngrok)

```bash
cd web

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your access key (optional)
cp ../.env.example .env
# Edit .env → set ACCESS_KEY=your_secret

# 3. Start server
python app.py
# → http://localhost:5000   (default key: nginsec2024)

# 4. Share via Ngrok
ngrok http 5000
```

---

## Web Edition — Screenshots

> Dark-themed single-page app with real-time Socket.io progress.

- **Auth gate** — password-protected entry, no page reload
- **Video info** — thumbnail, title, uploader, views, duration loaded via AJAX
- **Format picker** — dynamically populated from available resolutions (240p → 4K + MP3)
- **Live progress** — animated gradient bar with speed / ETA / downloaded stats
- **Save file** — direct browser download after server-side processing

---

## Configuration

### Change web access key

```bash
# Option A — environment variable (recommended)
ACCESS_KEY=mySecretKey python web/app.py

# Option B — edit web/app.py directly
SYSTEM_ACCESS_KEY = 'mySecretKey'
```

### Desktop output folders

Edit `config.py`:

```python
OUTPUT_DIR   = Path.home() / "Downloads" / "nginsec_downloads"
DOWNLOADS_DIR = OUTPUT_DIR / "videos"
MUSIC_DIR     = OUTPUT_DIR / "music"
```

---

## Dependencies

### Desktop (`requirements.txt`)
| Package | Purpose |
|---|---|
| yt-dlp | Download engine |
| customtkinter | Modern dark GUI |
| Pillow | Image handling |
| requests | HTTP client |

### Web (`web/requirements.txt`)
| Package | Purpose |
|---|---|
| flask | Web framework |
| flask-socketio | Real-time progress |
| yt-dlp | Download engine |

> **FFmpeg** must be installed and on PATH for both editions.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ffmpeg is not installed` | FFmpeg missing | `winget install Gyan.FFmpeg` |
| `No module named 'yt_dlp'` | Missing dependencies | `pip install -r requirements.txt` |
| `ModuleNotFoundError: customtkinter` | Desktop deps missing | `pip install customtkinter` |
| `Unauthorized` (web) | Wrong access key | Check your `ACCESS_KEY` env var |
| Slow 4K download | Normal — large file | Wait, or choose 1080p |

---

## Legal Notice

This tool is for **personal and educational use only**.  
Respect copyright laws and YouTube's Terms of Service.  
Do not use for redistribution of copyrighted content.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built & maintained by**

[![nginsec](https://img.shields.io/badge/github-nginsec-06b6d4?style=for-the-badge&logo=github)](https://github.com/nginsec)

*nginsec Video Cloud Suite · Secure Video Retrieval System*

</div>
