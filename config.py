"""
Configuration and constants for nginsec YouTube Video Suite
"""
import os
from pathlib import Path

# Branding
APP_NAME = "nginsec YouTube Video Suite"
APP_VERSION = "1.0.0"
APP_AUTHOR = "nginsec"
BRANDING_TEXT = "Powered by nginsec"

# Colors - Dark Mode with Neon Green Accent
COLORS = {
    "primary_bg": "#0f0f0f",      # Almost black background
    "secondary_bg": "#1a1a1a",    # Dark gray for panels
    "tertiary_bg": "#2a2a2a",     # Lighter gray for elements
    "accent": "#00ff00",           # Neon Green
    "accent_hover": "#00cc00",     # Darker green on hover
    "text_primary": "#ffffff",     # White text
    "text_secondary": "#b0b0b0",   # Gray text
    "success": "#00ff00",          # Green for success
    "error": "#ff3333",            # Red for errors
    "warning": "#ffaa00",          # Orange for warnings
    "info": "#00bfff",             # Cyan for info
}

# Directories
OUTPUT_DIR = Path.home() / "Downloads" / "nginsec_downloads"
TEMP_DIR = OUTPUT_DIR / ".temp"
DOWNLOADS_DIR = OUTPUT_DIR / "videos"
MUSIC_DIR = OUTPUT_DIR / "music"
METADATA_DIR = OUTPUT_DIR / "metadata"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
MUSIC_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

# Supported formats
AUDIO_QUALITIES = {
    "320 kbps (Best)": 320,
    "256 kbps": 256,
    "192 kbps": 192,
    "128 kbps": 128,
}

VIDEO_QUALITIES = [
    "4K (2160p)",
    "1080p (Full HD)",
    "720p (HD)",
    "480p",
    "360p",
    "240p",
]

# Download options
YT_DLP_OPTS_BASE = {
    "quiet": False,
    "no_warnings": False,
    "progress": True,
    "outtmpl": "",  # Will be set dynamically
    "socket_timeout": 30,
    "retries": 3,
    "fragment_retries": 3,
    "skip_unavailable_fragments": True,
    "postprocessor_args": {
        "ffmpeg": [
            "-c:v", "copy",
            "-c:a", "aac"
        ]
    }
}

# Logging format
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"

# UI Dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
FONT_LARGE = ("Segoe UI", 16, "bold")
FONT_MEDIUM = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
