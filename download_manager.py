"""
Download Manager v2 — yt-dlp engine with history, queue, clip, subtitles, multi-platform
"""
import json
import os
import shutil
import sqlite3
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime

import yt_dlp
import requests

from config import (
    DOWNLOADS_DIR, MUSIC_DIR, METADATA_DIR, DB_PATH,
    AUDIO_QUALITIES, YT_DLP_OPTS_BASE, LOG_FORMAT, LOG_DATE_FORMAT,
    NOTIFICATION_ENABLED, DEFAULT_SUBTITLE_LANGS, SUPPORTED_PLATFORMS,
)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


# ── yt-dlp logger (captures OAuth2 device-code prompts) ───────────────────────

_OAUTH2_KEYWORDS = ('google.com/device', 'authorization code', 'Input this',
                    'Please open', 'Waiting for authorization')


class _YtDlpLogger:
    """Forwards yt-dlp output to our logger; routes OAuth2 prompts to the UI."""

    def __init__(self, cb=None):
        self._cb = cb

    def debug(self, msg):
        if msg.startswith('[debug]'):
            return
        if self._cb and any(kw.lower() in msg.lower() for kw in _OAUTH2_KEYWORDS):
            self._cb({'status': 'oauth2_prompt', 'message': msg.strip()})

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


# ── Node.js detection ─────────────────────────────────────────────────────────

def _find_node() -> str:
    """Find Node.js executable — checks PATH then common Windows install dirs."""
    found = shutil.which('node') or shutil.which('node.exe')
    if found:
        return found
    candidates = [
        r'C:\Program Files\nodejs\node.exe',
        r'C:\Program Files (x86)\nodejs\node.exe',
        os.path.expanduser(r'~\AppData\Local\Programs\nodejs\node.exe'),
        os.path.expanduser(r'~\AppData\Roaming\nvm\current\node.exe'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ''

_NODE = _find_node()
if _NODE:
    logger.info(f'Node.js found: {_NODE}')
else:
    logger.warning('Node.js not found — YouTube may have limited formats')


# ── Auto cookie extraction ─────────────────────────────────────────────────────

_SESSION_COOKIES_PATH: str = ''   # cached for the process lifetime

_OAUTH2_TOKEN_PATHS = [
    Path(os.environ.get('APPDATA', '~')) / 'yt-dlp' / 'youtube-oauth2.token.json',
    Path.home() / '.config' / 'yt-dlp' / 'youtube-oauth2.token.json',
    Path.home() / '.cache'  / 'yt-dlp' / 'youtube-oauth2.token.json',
]


def _clear_stale_oauth2_token() -> None:
    """Delete any cached OAuth2 token so yt-dlp-youtube-oauth2 starts a fresh device-code flow."""
    for p in _OAUTH2_TOKEN_PATHS:
        try:
            if p.exists():
                p.unlink()
                logger.info(f'Cleared stale OAuth2 token: {p}')
        except Exception:
            pass


def _ytdlp_browser_cookies(browser: str) -> str:
    """
    Try yt-dlp's built-in cookie extraction for the given browser.
    Works for Opera/Edge (regular DPAPI); Chrome 127+ may still fail (ABE).
    Returns path to temp Netscape file, or '' on failure.
    """
    tmp_path = str(Path(__file__).parent / f'_auto_{browser}_cookies.txt')
    try:
        opts = {
            'quiet':              True,
            'no_warnings':        True,
            'cookiesfrombrowser': (browser,),
            'cookiefile':         tmp_path,
        }
        with yt_dlp.YoutubeDL(opts):
            pass   # __exit__ flushes cookie jar to tmp_path

        if Path(tmp_path).exists() and Path(tmp_path).stat().st_size > 300:
            logger.info(f'yt-dlp {browser} cookies: {Path(tmp_path).stat().st_size} bytes')
            return tmp_path
        Path(tmp_path).unlink(missing_ok=True)
    except Exception as e:
        logger.debug(f'yt-dlp {browser} cookie extract: {e}')
        Path(tmp_path).unlink(missing_ok=True)
    return ''


def _rookiepy_export() -> str:
    """
    Export YouTube cookies from Chrome/Edge/Opera to a Netscape temp file.
    rookiepy handles Chrome 127+ App-Bound Encryption without DPAPI issues.
    Returns temp file path on success, '' on failure.
    """
    try:
        import rookiepy
    except ImportError:
        return ''

    import tempfile
    for browser_name in ('chrome', 'edge', 'opera', 'firefox'):
        try:
            fn = getattr(rookiepy, browser_name, None)
            if fn is None:
                continue
            cookies = fn(domains=['.youtube.com'])
            if not cookies:
                continue

            tmp = tempfile.NamedTemporaryFile(
                suffix='_yt_cookies.txt', delete=False, mode='w',
                dir=str(Path(__file__).parent),
            )
            tmp.write('# Netscape HTTP Cookie File\n')
            for c in cookies:
                domain = c.get('domain', '.youtube.com')
                if not domain.startswith('.'):
                    domain = '.' + domain
                expires = int(
                    c.get('expirationDate') or c.get('expires') or c.get('expiry') or 0
                )
                tmp.write(
                    f"{domain}\tTRUE\t"
                    f"{c.get('path', '/')}\t"
                    f"{'TRUE' if c.get('secure') else 'FALSE'}\t"
                    f"{expires}\t"
                    f"{c['name']}\t{c['value']}\n"
                )
            tmp.close()

            if Path(tmp.name).stat().st_size > 200:
                logger.info(f'Auto-extracted {browser_name} cookies ({Path(tmp.name).stat().st_size} bytes)')
                return tmp.name
            Path(tmp.name).unlink(missing_ok=True)

        except Exception as e:
            logger.debug(f'rookiepy {browser_name}: {e}')

    return ''


def _add_browser_cookies(opts: dict) -> None:
    """
    Automatically configure YouTube authentication — no manual steps needed.

    Priority:
      1. cookies.txt  (if user manually placed it next to the script)
      2. rookiepy     (auto-extracts Chrome/Edge/Opera, handles Chrome 127+ ABE)
      3. web_creator / tv_embedded player clients (no cookies or PO tokens needed)
    """
    global _SESSION_COOKIES_PATH

    # 1. Manually-placed cookies.txt
    cookies_file = Path(__file__).parent / 'cookies.txt'
    if cookies_file.exists() and cookies_file.stat().st_size > 100:
        opts['cookiefile'] = str(cookies_file)
        logger.info('Auth: cookies.txt')
        return

    # 2. Cached auto-cookies from this session
    if _SESSION_COOKIES_PATH and Path(_SESSION_COOKIES_PATH).exists():
        opts['cookiefile'] = _SESSION_COOKIES_PATH
        return

    # 3. rookiepy auto-extract (handles Chrome 127+ App-Bound Encryption)
    path = _rookiepy_export()
    if path:
        _SESSION_COOKIES_PATH = path
        opts['cookiefile'] = path
        logger.info('Auth: auto-extracted browser cookies')
        return

    # 4. yt-dlp built-in browser extraction (Opera/Edge work; Chrome 127+ may still fail)
    for browser in ('opera', 'edge', 'chrome'):
        path = _ytdlp_browser_cookies(browser)
        if path:
            _SESSION_COOKIES_PATH = path
            opts['cookiefile'] = path
            logger.info(f'Auth: yt-dlp {browser} cookies')
            return

    # 5. OAuth2 — use cached token silently if available; device-code only first time
    opts['username'] = 'oauth2'
    opts['password'] = ''
    logger.info('Auth: OAuth2 (cached token or one-time Google login)')


# ── Helpers ────────────────────────────────────────────────────────────────────

def detect_platform(url: str) -> Tuple[str, str]:
    """Return (platform_name, icon_class) for a URL."""
    lower = url.lower()
    for domain, (name, _color, icon) in SUPPORTED_PLATFORMS.items():
        if domain in lower:
            return name, icon
    return 'Unknown', 'bi-globe'


def _notify(title: str, message: str) -> None:
    if not NOTIFICATION_ENABLED:
        return
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name='nginsec', timeout=5)
    except Exception:
        pass


def _time_to_seconds(t: str) -> float:
    """Convert HH:MM:SS / MM:SS / raw seconds string to float."""
    if not t or not t.strip():
        return 0.0
    parts = t.strip().split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except (ValueError, IndexError):
        return 0.0


# ── History DB ─────────────────────────────────────────────────────────────────

class HistoryDB:
    """Thread-safe SQLite download history (new connection per call)."""

    def __init__(self, path: Path):
        self.path = str(path)
        self._init_schema()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_schema(self):
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    url           TEXT,
                    title         TEXT,
                    platform      TEXT,
                    format_type   TEXT,
                    quality       TEXT,
                    filepath      TEXT,
                    status        TEXT,
                    downloaded_at TEXT
                )
            ''')
            conn.commit()

    def add(self, url: str, title: str, platform: str,
            format_type: str, quality: str, filepath: str,
            status: str = 'complete') -> None:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO downloads '
                '(url,title,platform,format_type,quality,filepath,status,downloaded_at) '
                'VALUES (?,?,?,?,?,?,?,?)',
                (url, title, platform, format_type, quality, filepath, status, ts),
            )
            conn.commit()

    def get_all(self, limit: int = 300) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT id,url,title,platform,format_type,quality,filepath,status,downloaded_at '
                'FROM downloads ORDER BY downloaded_at DESC LIMIT ?',
                (limit,),
            ).fetchall()
        keys = ('id', 'url', 'title', 'platform', 'format_type',
                'quality', 'filepath', 'status', 'downloaded_at')
        return [dict(zip(keys, row)) for row in rows]

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute('DELETE FROM downloads')
            conn.commit()


# ── Download Manager ───────────────────────────────────────────────────────────

class DownloadManager:
    """Handles video/audio downloads with queue, history, clip extraction and subtitles."""

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.is_downloading = False
        self.cancel_flag = False
        self.lock = threading.Lock()
        self.queue: List[Dict] = []
        self.history = HistoryDB(DB_PATH)

    # ── Progress hook ──────────────────────────────────────────────────────────

    def _progress_hook(self, d: Dict) -> None:
        if self.cancel_flag:
            raise ValueError("Download cancelled by user")
        if not self.progress_callback:
            return

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            self.progress_callback({
                'status':           'downloading',
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes':      total,
                'filename':         d.get('filename', ''),
                'speed':            d.get('speed', 0),
                'elapsed':          d.get('elapsed', 0),
                'eta':              d.get('eta', 0),
            })
        elif d['status'] == 'finished':
            self.progress_callback({'status': 'finished', 'filename': d.get('filename', '')})

    # ── Video info ─────────────────────────────────────────────────────────────

    def get_video_info(self, url: str) -> Optional[Dict]:
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            return self._format_video_info(info)
        except Exception as e:
            logger.error(f"Error fetching info: {e}")
            if self.progress_callback:
                self.progress_callback({'status': 'error', 'error': str(e)})
            return None

    def _format_video_info(self, info: Dict) -> Dict:
        resolutions = sorted(
            {f"{f.get('height')}p" for f in info.get('formats', []) if f.get('height')},
            key=lambda s: int(s[:-1]), reverse=True,
        )
        source_url = info.get('webpage_url') or info.get('url', '')
        platform, _ = detect_platform(source_url)
        return {
            'title':             info.get('title', 'Unknown'),
            'duration':          info.get('duration', 0),
            'uploader':          info.get('uploader', 'Unknown'),
            'upload_date':       info.get('upload_date', ''),
            'description':       info.get('description', ''),
            'thumbnail':         info.get('thumbnail', ''),
            'view_count':        info.get('view_count', 0),
            'like_count':        info.get('like_count', 0),
            'subtitles':         list(info.get('subtitles', {}).keys()),
            'auto_captions':     list(info.get('automatic_captions', {}).keys()),
            'formats_available': resolutions,
            'is_live':           info.get('is_live', False),
            'platform':          platform,
        }

    # ── Format string ──────────────────────────────────────────────────────────

    def _get_format_string(self, quality: str) -> str:
        heights = {
            "4K (2160p)":      2160,
            "1080p (Full HD)": 1080,
            "720p (HD)":       720,
            "480p":            480,
            "360p":            360,
            "240p":            240,
        }
        h = heights.get(quality, 1080)
        # Prefer H.264 (avc1) — avoids VP9/AV1 DASH streams that get 403
        return (
            f"bestvideo[vcodec^=avc1][height<={h}]+bestaudio[acodec^=mp4a]"
            f"/bestvideo[vcodec^=avc1][height<={h}]+bestaudio"
            f"/bestvideo[height<={h}]+bestaudio"
            f"/best[height<={h}]/best"
        )

    # ── Download video ─────────────────────────────────────────────────────────

    def download_video(self, url: str, quality: str = "1080p (Full HD)",
                       clip_start: str = '', clip_end: str = '',
                       embed_subs: bool = False) -> bool:
        with self.lock:
            if self.is_downloading:
                return False
            self.is_downloading = True
            self.cancel_flag = False
        threading.Thread(
            target=self._video_thread,
            args=(url, quality, clip_start, clip_end, embed_subs),
            daemon=False,
        ).start()
        return True

    def _video_thread(self, url: str, quality: str,
                      clip_start: str, clip_end: str, embed_subs: bool) -> None:
        title = 'Unknown'
        try:
            ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_tpl = str(DOWNLOADS_DIR / f"{ts}_%(title)s.%(ext)s")
            platform, _ = detect_platform(url)

            opts = dict(YT_DLP_OPTS_BASE)
            opts['postprocessor_args'] = dict(YT_DLP_OPTS_BASE.get('postprocessor_args', {}))
            opts['outtmpl']            = out_tpl
            opts['progress_hooks']     = [self._progress_hook]
            opts['logger']             = _YtDlpLogger(cb=self.progress_callback)
            opts['format']             = self._get_format_string(quality)
            opts['merge_output_format']= 'mp4'
            opts['http_headers']       = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
            if _NODE:
                opts['js_runtimes'] = {'node': {'path': _NODE}}
            _add_browser_cookies(opts)

            # Clip extraction
            if clip_start or clip_end:
                from yt_dlp.utils import download_range_func
                s = _time_to_seconds(clip_start)
                e = _time_to_seconds(clip_end)
                if e > s:
                    opts['download_ranges']        = download_range_func(None, [(s, e)])
                    opts['force_keyframes_at_cuts'] = True

            # Subtitle embedding
            if embed_subs:
                opts['writesubtitles']    = True
                opts['writeautomaticsub'] = True
                opts['subtitleslangs']    = DEFAULT_SUBTITLE_LANGS
                opts['embedsubtitles']    = True
                opts.setdefault('postprocessors', [])
                opts['postprocessors'].append({
                    'key': 'FFmpegEmbedSubtitle',
                    'already_have_subtitle': False,
                })

            if self.progress_callback:
                self.progress_callback({'status': 'started', 'message': f'Downloading {quality}…'})

            def _run_download(dl_opts):
                with yt_dlp.YoutubeDL(dl_opts) as ydl:
                    i = ydl.extract_info(url, download=True)
                    return (i or {}).get('title', 'Unknown')

            try:
                title = _run_download(opts)
            except Exception as first_err:
                err_s = str(first_err)
                is_auth = any(x in err_s for x in ('403', 'Forbidden', 'HTTP Error 400',
                                                     'Please sign in', 'Sign in', 'Bad Request'))
                if is_auth:
                    logger.warning('Auth error — clearing stale token and retrying OAuth2')
                    _clear_stale_oauth2_token()   # only clear on confirmed auth failure
                    if self.progress_callback:
                        self.progress_callback({'status': 'started',
                                                'message': 'OAuth2 ile tekrar deneniyor…'})
                    opts.pop('cookiesfrombrowser', None)
                    opts.pop('cookiefile', None)
                    opts.pop('extractor_args', None)
                    opts['username'] = 'oauth2'
                    opts['password'] = ''
                    title = _run_download(opts)
                else:
                    raise

            candidates = sorted(
                [f for f in DOWNLOADS_DIR.iterdir()
                 if f.name.startswith(ts) and f.suffix != '.part'],
                key=lambda f: f.stat().st_mtime, reverse=True,
            )
            filepath = str(candidates[0]) if candidates else ''
            self.history.add(url, title, platform, 'video', quality, filepath)

            if self.progress_callback:
                self.progress_callback({'status': 'completed', 'message': 'Video saved.'})
            _notify('Download Complete', f'{title}')

        except Exception as e:
            logger.error(f"Video download failed: {e}")
            if self.progress_callback:
                self.progress_callback({'status': 'error', 'error': str(e)})
        finally:
            with self.lock:
                self.is_downloading = False

    # ── Download audio ─────────────────────────────────────────────────────────

    def download_audio(self, url: str, quality_kbps: int = 320) -> bool:
        with self.lock:
            if self.is_downloading:
                return False
            self.is_downloading = True
            self.cancel_flag = False
        threading.Thread(
            target=self._audio_thread,
            args=(url, quality_kbps),
            daemon=False,
        ).start()
        return True

    def _audio_thread(self, url: str, quality_kbps: int) -> None:
        title = 'Unknown'
        try:
            ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_tpl = str(MUSIC_DIR / f"{ts}_%(title)s.%(ext)s")
            platform, _ = detect_platform(url)

            opts = dict(YT_DLP_OPTS_BASE)
            opts['outtmpl']        = out_tpl
            opts['progress_hooks'] = [self._progress_hook]
            opts['logger']         = _YtDlpLogger(cb=self.progress_callback)
            opts['format']         = 'bestaudio/best'
            opts['http_headers']   = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
            if _NODE:
                opts['js_runtimes'] = {'node': {'path': _NODE}}
            _add_browser_cookies(opts)
            opts['postprocessors'] = [{
                'key':              'FFmpegExtractAudio',
                'preferredcodec':   'mp3',
                'preferredquality': str(quality_kbps),
            }]

            if self.progress_callback:
                self.progress_callback({'status': 'started', 'message': f'Extracting MP3 {quality_kbps}kbps…'})

            def _run_audio(dl_opts):
                with yt_dlp.YoutubeDL(dl_opts) as ydl:
                    i = ydl.extract_info(url, download=True)
                    return (i or {}).get('title', 'Unknown')

            try:
                title = _run_audio(opts)
            except Exception as first_err:
                err_s = str(first_err)
                is_auth = any(x in err_s for x in ('403', 'Forbidden', 'HTTP Error 400',
                                                     'Please sign in', 'Sign in', 'Bad Request'))
                if is_auth:
                    logger.warning('Auth error — clearing stale token and retrying OAuth2')
                    _clear_stale_oauth2_token()
                    if self.progress_callback:
                        self.progress_callback({'status': 'started',
                                                'message': 'OAuth2 ile tekrar deneniyor…'})
                    opts.pop('cookiesfrombrowser', None)
                    opts.pop('cookiefile', None)
                    opts.pop('extractor_args', None)
                    opts['username'] = 'oauth2'
                    opts['password'] = ''
                    title = _run_audio(opts)
                else:
                    raise

            candidates = sorted(
                [f for f in MUSIC_DIR.iterdir()
                 if f.name.startswith(ts) and f.suffix != '.part'],
                key=lambda f: f.stat().st_mtime, reverse=True,
            )
            filepath = str(candidates[0]) if candidates else ''
            self.history.add(url, title, platform, 'audio', f'{quality_kbps} kbps MP3', filepath)

            if self.progress_callback:
                self.progress_callback({'status': 'completed', 'message': 'Audio saved.'})
            _notify('Audio Ready', f'{title}.mp3')

        except Exception as e:
            logger.error(f"Audio download failed: {e}")
            if self.progress_callback:
                self.progress_callback({'status': 'error', 'error': str(e)})
        finally:
            with self.lock:
                self.is_downloading = False

    # ── Metadata ───────────────────────────────────────────────────────────────

    def download_metadata(self, url: str, video_title: str) -> bool:
        try:
            info = self.get_video_info(url)
            if not info:
                return False
            safe = "".join(c for c in video_title
                           if c.isalnum() or c in (' ', '-', '_')).rstrip() or 'unknown'
            out = METADATA_DIR / safe
            out.mkdir(parents=True, exist_ok=True)

            if info.get('description'):
                (out / 'description.txt').write_text(info['description'], encoding='utf-8')

            if info.get('thumbnail'):
                try:
                    r = requests.get(info['thumbnail'], timeout=10)
                    if r.status_code == 200:
                        (out / 'thumbnail.jpg').write_bytes(r.content)
                except Exception as e:
                    logger.warning(f"Thumbnail failed: {e}")

            (out / 'metadata.json').write_text(
                json.dumps(
                    {k: info[k] for k in ('title', 'uploader', 'upload_date',
                                          'duration', 'view_count', 'like_count')
                     if k in info},
                    indent=2, ensure_ascii=False,
                ),
                encoding='utf-8',
            )
            return True
        except Exception as e:
            logger.error(f"Metadata failed: {e}")
            return False

    # ── Queue ──────────────────────────────────────────────────────────────────

    def add_to_queue(self, url: str, mode: str, quality: str) -> None:
        """mode: 'video' | 'audio'"""
        self.queue.append({'url': url, 'mode': mode, 'quality': quality})

    def remove_from_queue(self, index: int) -> None:
        if 0 <= index < len(self.queue):
            self.queue.pop(index)

    def clear_queue(self) -> None:
        self.queue.clear()

    def process_queue(self, done_callback: Optional[Callable] = None) -> None:
        """Process queue items sequentially in a background thread."""
        def _run():
            for item in list(self.queue):
                self.queue.remove(item)
                if item['mode'] == 'audio':
                    kbps = AUDIO_QUALITIES.get(item['quality'], 320)
                    self.download_audio(item['url'], kbps)
                else:
                    self.download_video(item['url'], item['quality'])
                # Wait for current download to finish
                while self.is_downloading:
                    import time; time.sleep(0.3)
            if done_callback:
                done_callback()

        threading.Thread(target=_run, daemon=True).start()

    # ── Cancel ─────────────────────────────────────────────────────────────────

    def cancel_download(self) -> None:
        self.cancel_flag = True
        with self.lock:
            self.is_downloading = False
