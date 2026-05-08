"""
Download Manager - Backend logic for yt-dlp operations
Handles all video/audio downloads and metadata extraction
"""
import os
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
import yt_dlp
import requests
from config import (
    DOWNLOADS_DIR, MUSIC_DIR, METADATA_DIR, TEMP_DIR,
    AUDIO_QUALITIES, YT_DLP_OPTS_BASE, LOG_FORMAT, LOG_DATE_FORMAT
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class DownloadManager:
    """Handles all YouTube video/audio downloads with thread safety"""

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.current_download = None
        self.is_downloading = False
        self.lock = threading.Lock()
        self.cancel_flag = False

    def _progress_hook(self, d: Dict) -> None:
        """Hook for yt-dlp progress updates"""
        if self.cancel_flag:
            raise ValueError("Download cancelled by user")

        if d['status'] == 'downloading':
            self.current_download = d
            if self.progress_callback:
                self.progress_callback({
                    'status': 'downloading',
                    'downloaded_bytes': d.get('downloaded_bytes', 0),
                    'total_bytes': d.get('total_bytes', 0),
                    'total_bytes_estimate': d.get('total_bytes_estimate', 0),
                    'filename': d.get('filename', ''),
                    'speed': d.get('speed', 0),
                    'elapsed': d.get('elapsed', 0),
                    'eta': d.get('eta', 0),
                })
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback({
                    'status': 'finished',
                    'filename': d.get('filename', '')
                })
        elif d['status'] == 'error':
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': str(d)
                })

    def get_video_info(self, url: str) -> Optional[Dict]:
        """Fetch video information without downloading"""
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._format_video_info(info)
        except Exception as e:
            logger.error(f"Error fetching video info: {str(e)}")
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': f"Failed to fetch video: {str(e)}"
                })
            return None

    def _format_video_info(self, info: Dict) -> Dict:
        """Format video information for display"""
        formats = info.get('formats', [])

        # Group available resolutions
        resolutions = set()
        for fmt in formats:
            height = fmt.get('height')
            if height:
                resolutions.add(f"{height}p")

        return {
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', 'Unknown'),
            'upload_date': info.get('upload_date', ''),
            'description': info.get('description', ''),
            'thumbnail': info.get('thumbnail', ''),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'comment_count': info.get('comment_count', 0),
            'subtitles': list(info.get('subtitles', {}).keys()),
            'formats_available': sorted(list(resolutions), reverse=True),
            'is_live': info.get('is_live', False),
            'age_limit': info.get('age_limit', 0),
        }

    def download_video(self, url: str, quality: str = "best") -> bool:
        """Download video with specified quality"""
        with self.lock:
            if self.is_downloading:
                return False
            self.is_downloading = True
            self.cancel_flag = False

        try:
            thread = threading.Thread(
                target=self._download_video_thread,
                args=(url, quality),
                daemon=False
            )
            thread.start()
            thread.join()
            return True
        except Exception as e:
            logger.error(f"Error starting download: {str(e)}")
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': str(e)
                })
            return False
        finally:
            with self.lock:
                self.is_downloading = False

    def _download_video_thread(self, url: str, quality: str) -> None:
        """Actual download logic running in thread"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_template = str(DOWNLOADS_DIR / f"{timestamp}_%(title)s.%(ext)s")

            opts = YT_DLP_OPTS_BASE.copy()
            opts['outtmpl'] = output_template
            opts['progress_hooks'] = [self._progress_hook]
            opts['format'] = self._get_format_string(quality)
            opts['merge_output_format'] = 'mp4'

            if self.progress_callback:
                self.progress_callback({
                    'status': 'started',
                    'message': f'Starting download with quality: {quality}'
                })

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if self.progress_callback:
                self.progress_callback({
                    'status': 'completed',
                    'message': 'Video download completed successfully'
                })
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': str(e)
                })

    def _get_format_string(self, quality: str) -> str:
        """Convert quality string to yt-dlp format string"""
        quality_mapping = {
            "4K (2160p)": "bestvideo[height<=2160]+bestaudio/best",
            "1080p (Full HD)": "bestvideo[height<=1080]+bestaudio/best",
            "720p (HD)": "bestvideo[height<=720]+bestaudio/best",
            "480p": "bestvideo[height<=480]+bestaudio/best",
            "360p": "bestvideo[height<=360]+bestaudio/best",
            "240p": "bestvideo[height<=240]+bestaudio/best",
            "best": "bestvideo+bestaudio/best",
        }
        return quality_mapping.get(quality, "best")

    def download_audio(self, url: str, quality_kbps: int = 320) -> bool:
        """Download audio only as MP3"""
        with self.lock:
            if self.is_downloading:
                return False
            self.is_downloading = True
            self.cancel_flag = False

        try:
            thread = threading.Thread(
                target=self._download_audio_thread,
                args=(url, quality_kbps),
                daemon=False
            )
            thread.start()
            thread.join()
            return True
        except Exception as e:
            logger.error(f"Error starting audio download: {str(e)}")
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': str(e)
                })
            return False
        finally:
            with self.lock:
                self.is_downloading = False

    def _download_audio_thread(self, url: str, quality_kbps: int) -> None:
        """Actual audio download logic running in thread"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_template = str(MUSIC_DIR / f"{timestamp}_%(title)s.%(ext)s")

            opts = YT_DLP_OPTS_BASE.copy()
            opts['outtmpl'] = output_template
            opts['progress_hooks'] = [self._progress_hook]
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': str(quality_kbps),
                }
            ]

            if self.progress_callback:
                self.progress_callback({
                    'status': 'started',
                    'message': f'Starting audio extraction: {quality_kbps}kbps MP3'
                })

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if self.progress_callback:
                self.progress_callback({
                    'status': 'completed',
                    'message': 'Audio download completed successfully'
                })
        except Exception as e:
            logger.error(f"Audio download failed: {str(e)}")
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': str(e)
                })

    def download_metadata(self, url: str, video_title: str) -> bool:
        """Download video metadata (description, thumbnail, subtitles, tags)"""
        try:
            info = self.get_video_info(url)
            if not info:
                return False

            # Create metadata directory for this video
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            metadata_path = METADATA_DIR / safe_title
            metadata_path.mkdir(parents=True, exist_ok=True)

            # Save description
            if info.get('description'):
                with open(metadata_path / "description.txt", 'w', encoding='utf-8') as f:
                    f.write(info['description'])

            # Download thumbnail
            if info.get('thumbnail'):
                try:
                    response = requests.get(info['thumbnail'], timeout=10)
                    if response.status_code == 200:
                        with open(metadata_path / "thumbnail.jpg", 'wb') as f:
                            f.write(response.content)
                except Exception as e:
                    logger.warning(f"Failed to download thumbnail: {str(e)}")

            # Save metadata as JSON
            metadata = {
                'title': info.get('title'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'duration': info.get('duration'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'comment_count': info.get('comment_count'),
                'subtitles_available': info.get('subtitles', []),
                'formats_available': info.get('formats_available', []),
            }

            with open(metadata_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Metadata saved to {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading metadata: {str(e)}")
            return False

    def cancel_download(self) -> None:
        """Cancel the current download"""
        self.cancel_flag = True
        with self.lock:
            self.is_downloading = False
