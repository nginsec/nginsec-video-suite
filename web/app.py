"""
nginsec Video Cloud Suite — Web Edition v2
Flask + Socket.io · Download history · Clip extraction · Subtitle embedding · Multi-platform
"""

import os
import re
import uuid
import sqlite3
import threading
import logging
from pathlib import Path
from functools import wraps
from datetime import datetime

import requests as req_lib
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_socketio import SocketIO
import yt_dlp

# ── Configuration ──────────────────────────────────────────────────────────────

SYSTEM_ACCESS_KEY = os.environ.get('ACCESS_KEY', 'nginsec2024')
SECRET_KEY        = os.environ.get('SECRET_KEY', 'nginsec-vcs-x7k2m9p4-secret')
WEB_DIR           = Path(__file__).parent
DOWNLOADS_DIR     = WEB_DIR / 'downloads'
DOWNLOADS_DIR.mkdir(exist_ok=True)
HISTORY_DB_PATH   = DOWNLOADS_DIR / 'history.db'

DEFAULT_SUBTITLE_LANGS = ['tr', 'en']

PLATFORM_MAP = {
    'youtube.com':   'YouTube',
    'youtu.be':      'YouTube',
    'instagram.com': 'Instagram',
    'tiktok.com':    'TikTok',
    'twitter.com':   'Twitter/X',
    'x.com':         'Twitter/X',
    'twitch.tv':     'Twitch',
    'vimeo.com':     'Vimeo',
    'soundcloud.com':'SoundCloud',
}

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
)
log = logging.getLogger('nginsec')

# ── Flask & Socket.io ──────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

jobs: dict = {}


# ── History DB ─────────────────────────────────────────────────────────────────

class HistoryDB:
    def __init__(self, path: Path):
        self.path = str(path)
        self._init()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._conn() as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    url           TEXT,
                    title         TEXT,
                    platform      TEXT,
                    format_type   TEXT,
                    quality       TEXT,
                    filename      TEXT,
                    status        TEXT,
                    downloaded_at TEXT
                )
            ''')
            c.commit()

    def add(self, url, title, platform, format_type, quality, filename, status='complete'):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._conn() as c:
            c.execute(
                'INSERT INTO downloads '
                '(url,title,platform,format_type,quality,filename,status,downloaded_at) '
                'VALUES (?,?,?,?,?,?,?,?)',
                (url, title, platform, format_type, quality, filename, status, ts),
            )
            c.commit()

    def get_all(self, limit=300):
        with self._conn() as c:
            rows = c.execute(
                'SELECT id,url,title,platform,format_type,quality,filename,status,downloaded_at '
                'FROM downloads ORDER BY downloaded_at DESC LIMIT ?',
                (limit,),
            ).fetchall()
        keys = ('id', 'url', 'title', 'platform', 'format_type',
                'quality', 'filename', 'status', 'downloaded_at')
        return [dict(zip(keys, r)) for r in rows]

    def clear(self):
        with self._conn() as c:
            c.execute('DELETE FROM downloads')
            c.commit()


history_db = HistoryDB(HISTORY_DB_PATH)


# ── Helpers ────────────────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    lower = url.lower()
    for domain, name in PLATFORM_MAP.items():
        if domain in lower:
            return name
    return 'Unknown'


def _parse_pct(s: str) -> float:
    try:
        return float(re.sub(r'[^\d.]', '', s or '0'))
    except ValueError:
        return 0.0


def _time_to_seconds(t: str) -> float:
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


# ── Auth decorator ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapped


# ── yt-dlp progress hook ───────────────────────────────────────────────────────

def _make_hook(job_id: str, sid: str):
    def hook(d):
        if d['status'] == 'downloading':
            pct = _parse_pct(d.get('_percent_str', '0'))
            socketio.emit('progress', {
                'job_id':  job_id,
                'percent': min(pct, 99),
                'pct_str': (d.get('_percent_str') or '0%').strip(),
                'speed':   (d.get('_speed_str')   or '—').strip(),
                'eta':     (d.get('_eta_str')      or '—').strip(),
                'done':    (d.get('_downloaded_bytes_str') or '—').strip(),
                'total':   (d.get('_total_bytes_str') or
                            d.get('_total_bytes_estimate_str') or '—').strip(),
            }, room=sid)
        elif d['status'] == 'finished':
            socketio.emit('progress', {
                'job_id': job_id, 'percent': 99, 'pct_str': '99%',
                'speed': '—', 'eta': 'Finalizing…', 'done': '—', 'total': '—',
            }, room=sid)
    return hook


# ── Download worker ────────────────────────────────────────────────────────────

def _worker(job_id: str, url: str, fmt: str, is_audio: bool, sid: str,
            clip_start: str = '', clip_end: str = '', embed_subs: bool = False):
    prefix  = job_id[:8]
    out_tpl = str(DOWNLOADS_DIR / f'{prefix}_%(title)s.%(ext)s')
    platform = detect_platform(url)

    opts = {
        'format':            fmt,
        'outtmpl':           out_tpl,
        'progress_hooks':    [_make_hook(job_id, sid)],
        'noplaylist':        True,
        'restrictfilenames': True,
        'quiet':             True,
        'no_warnings':       True,
        'socket_timeout':    30,
        'retries':           3,
    }

    if is_audio:
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
        format_type = 'audio'
        quality     = 'MP3 320 kbps'
    else:
        opts['merge_output_format'] = 'mp4'
        format_type = 'video'
        quality     = fmt.split('[')[0] if '[' in fmt else fmt

        # Clip extraction
        if clip_start or clip_end:
            try:
                from yt_dlp.utils import download_range_func
                s = _time_to_seconds(clip_start)
                e = _time_to_seconds(clip_end)
                if e > s > 0 or (e > 0 and not clip_start):
                    opts['download_ranges']         = download_range_func(None, [(s, e)])
                    opts['force_keyframes_at_cuts']  = True
            except Exception as ex:
                log.warning(f'Clip setup failed: {ex}')

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

    title = 'Unknown'
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info  = ydl.download([url])
            # Try to extract title via a second info call
            try:
                meta  = ydl.extract_info(url, download=False)
                title = (meta or {}).get('title', 'Unknown')
            except Exception:
                pass

        candidates = [
            f for f in DOWNLOADS_DIR.iterdir()
            if f.name.startswith(prefix) and f.suffix != '.part'
        ]
        if not candidates:
            raise FileNotFoundError('Output file not found after download.')

        target = max(candidates, key=lambda f: f.stat().st_mtime)
        jobs[job_id].update(status='complete', filepath=str(target))
        history_db.add(url, title, platform, format_type, quality, target.name)

        socketio.emit('complete', {
            'job_id':   job_id,
            'filename': target.name,
        }, room=sid)
        log.info(f'Done [{prefix}] → {target.name}')

    except Exception as exc:
        jobs[job_id].update(status='error', error=str(exc))
        history_db.add(url, title, platform, format_type, quality, '', status='error')
        socketio.emit('dl_error', {'job_id': job_id, 'error': str(exc)}, room=sid)
        log.error(f'Error [{prefix}]: {exc}')


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auth', methods=['POST'])
def auth():
    key = (request.get_json() or {}).get('key', '')
    if key == SYSTEM_ACCESS_KEY:
        session['authenticated'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Invalid access key'}), 401


@app.route('/info', methods=['POST'])
@login_required
def get_info():
    url = (request.get_json() or {}).get('url', '').strip()
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            meta = ydl.extract_info(url, download=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    heights = {
        f.get('height')
        for f in meta.get('formats', [])
        if f.get('height') and f.get('vcodec', 'none') != 'none'
    }

    RES_LABELS = {
        2160: '4K Ultra HD (2160p)',
        1440: '2K QHD (1440p)',
        1080: '1080p Full HD',
        720:  '720p HD',
        480:  '480p',
        360:  '360p',
        240:  '240p',
    }
    formats = [
        {
            'value': f'bestvideo[height<={h}]+bestaudio/best[height<={h}]',
            'label': RES_LABELS.get(h, f'{h}p'),
            'type':  'video',
        }
        for h in (2160, 1440, 1080, 720, 480, 360, 240)
        if any(a >= h for a in heights)
    ]
    if not formats:
        formats.append({'value': 'best', 'label': 'Best Available', 'type': 'video'})
    formats.append({'value': 'bestaudio/best', 'label': 'MP3 ~320 kbps', 'type': 'audio'})

    subs = list((meta.get('subtitles') or {}).keys())
    auto = list((meta.get('automatic_captions') or {}).keys())
    dur  = meta.get('duration', 0)

    return jsonify({
        'title':      meta.get('title', 'Unknown'),
        'thumbnail':  meta.get('thumbnail', ''),
        'duration':   meta.get('duration_string') or (f'{dur//60}:{dur%60:02d}' if dur else '—'),
        'uploader':   meta.get('uploader', 'Unknown'),
        'view_count': meta.get('view_count', 0),
        'platform':   detect_platform(url),
        'subtitles':  subs + [f'{a} (auto)' for a in auto if a not in subs],
        'formats':    formats,
    })


@app.route('/download', methods=['POST'])
@login_required
def start_download():
    body      = request.get_json() or {}
    url       = body.get('url', '').strip()
    fmt       = body.get('format', 'bestvideo+bestaudio/best')
    is_audio  = bool(body.get('is_audio', False))
    sid       = body.get('socket_id', '')
    clip_start= body.get('clip_start', '').strip()
    clip_end  = body.get('clip_end', '').strip()
    embed_subs= bool(body.get('embed_subs', False))

    if not url or not sid:
        return jsonify({'error': 'Missing url or socket_id'}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'starting'}

    threading.Thread(
        target=_worker,
        args=(job_id, url, fmt, is_audio, sid, clip_start, clip_end, embed_subs),
        daemon=True,
    ).start()

    return jsonify({'job_id': job_id})


@app.route('/file/<job_id>')
@login_required
def serve_file(job_id):
    entry = jobs.get(job_id)
    if not entry or entry.get('status') != 'complete':
        return jsonify({'error': 'File not ready'}), 404
    fp = Path(entry.get('filepath', ''))
    if not fp.exists():
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(fp, as_attachment=True, download_name=fp.name)


@app.route('/history')
@login_required
def get_history():
    return jsonify(history_db.get_all())


@app.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    history_db.clear()
    return jsonify({'ok': True})


@app.route('/ngrok_url')
@login_required
def get_ngrok_url():
    try:
        r = req_lib.get('http://127.0.0.1:4040/api/tunnels', timeout=1)
        tunnels = r.json().get('tunnels', [])
        for t in tunnels:
            if t.get('proto') == 'https':
                return jsonify({'url': t['public_url']})
        if tunnels:
            return jsonify({'url': tunnels[0]['public_url']})
    except Exception:
        pass
    return jsonify({'url': None})


# ── Socket.io events ───────────────────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    log.info(f'WS connected: {request.sid}')


@socketio.on('disconnect')
def on_disconnect():
    log.info(f'WS disconnected: {request.sid}')


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Check Ngrok at startup
    ngrok_url = None
    try:
        r = req_lib.get('http://127.0.0.1:4040/api/tunnels', timeout=1)
        tunnels = r.json().get('tunnels', [])
        for t in tunnels:
            if t.get('proto') == 'https':
                ngrok_url = t['public_url']
                break
        if not ngrok_url and tunnels:
            ngrok_url = tunnels[0]['public_url']
    except Exception:
        pass

    print()
    print('  ┌──────────────────────────────────────────────────┐')
    print('  │      nginsec Video Cloud Suite · Web Edition     │')
    print('  ├──────────────────────────────────────────────────┤')
    print(f'  │  Local  : http://localhost:5000                  │')
    if ngrok_url:
        print(f'  │  Public : {ngrok_url:<40}│')
    print(f'  │  Key    : {SYSTEM_ACCESS_KEY:<40}│')
    print('  └──────────────────────────────────────────────────┘')
    print()

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
