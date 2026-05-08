"""
Configuration and constants for nginsec Video Cloud Suite v2
"""
import os
from pathlib import Path

# Branding
APP_NAME    = "nginsec Video Cloud Suite"
APP_VERSION = "2.0.0"
APP_AUTHOR  = "nginsec"
BRANDING_TEXT = "nginsec · Secure Video Retrieval System"

# Colors — GitHub-inspired dark theme
COLORS = {
    "primary_bg":    "#0d1117",
    "secondary_bg":  "#161b22",
    "tertiary_bg":   "#21262d",
    "sidebar_bg":    "#010409",
    "border":        "#30363d",
    "accent":        "#58a6ff",
    "accent_hover":  "#388bfd",
    "text_primary":  "#e6edf3",
    "text_secondary":"#8b949e",
    "success":       "#3fb950",
    "error":         "#f85149",
    "warning":       "#d29922",
    "info":          "#79c0ff",
    "purple":        "#bc8cff",
}

# Directories
OUTPUT_DIR    = Path.home() / "Downloads" / "nginsec_downloads"
TEMP_DIR      = OUTPUT_DIR / ".temp"
DOWNLOADS_DIR = OUTPUT_DIR / "videos"
MUSIC_DIR     = OUTPUT_DIR / "music"
METADATA_DIR  = OUTPUT_DIR / "metadata"
DB_PATH       = OUTPUT_DIR / "history.db"

for _d in [OUTPUT_DIR, TEMP_DIR, DOWNLOADS_DIR, MUSIC_DIR, METADATA_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# Features
NOTIFICATION_ENABLED   = True
DEFAULT_SUBTITLE_LANGS = ['tr', 'en']

# Platform registry  (domain → (name, hex-color, bootstrap-icon))
SUPPORTED_PLATFORMS = {
    'youtube.com':   ('YouTube',    '#FF0000', 'bi-youtube'),
    'youtu.be':      ('YouTube',    '#FF0000', 'bi-youtube'),
    'instagram.com': ('Instagram',  '#E1306C', 'bi-instagram'),
    'tiktok.com':    ('TikTok',     '#69C9D0', 'bi-tiktok'),
    'twitter.com':   ('Twitter/X',  '#1D9BF0', 'bi-twitter-x'),
    'x.com':         ('Twitter/X',  '#1D9BF0', 'bi-twitter-x'),
    'twitch.tv':     ('Twitch',     '#9146FF', 'bi-twitch'),
    'vimeo.com':     ('Vimeo',      '#1AB7EA', 'bi-vimeo'),
    'soundcloud.com':('SoundCloud', '#FF5500', 'bi-soundcloud'),
}

# Supported qualities
AUDIO_QUALITIES = {
    "320 kbps (Best)": 320,
    "256 kbps":        256,
    "192 kbps":        192,
    "128 kbps":        128,
}

VIDEO_QUALITIES = [
    "4K (2160p)",
    "1080p (Full HD)",
    "720p (HD)",
    "480p",
    "360p",
    "240p",
]

# Base yt-dlp options
YT_DLP_OPTS_BASE = {
    "quiet":                    False,
    "no_warnings":              False,
    "progress":                 True,
    "outtmpl":                  "",
    "socket_timeout":           30,
    "retries":                  3,
    "fragment_retries":         3,
    "skip_unavailable_fragments": True,
    "postprocessor_args": {
        "ffmpeg": ["-c:v", "copy", "-c:a", "aac"]
    },
}

# Logging
LOG_FORMAT      = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"

# UI dimensions
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 780
SIDEBAR_WIDTH = 210
FONT_LARGE    = ("Segoe UI", 15, "bold")
FONT_MEDIUM   = ("Segoe UI", 12)
FONT_SMALL    = ("Segoe UI", 10)
FONT_MONO     = ("Cascadia Code", 9)
