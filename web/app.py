"""
nginsec Video Cloud Suite - Web Edition
Secure YouTube/video downloader powered by yt-dlp + Flask + Socket.io
"""

import os
import re
import uuid
import threading
import logging
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_socketio import SocketIO
import yt_dlp

# ── Configuration ──────────────────────────────────────────────────────────────
SYSTEM_ACCESS_KEY = os.environ.get('ACCESS_KEY', 'nginsec2024')
SECRET_KEY        = os.environ.get('SECRET_KEY', 'nginsec-vcs-x7k2m9p4-secret')
DOWNLOADS_DIR     = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
log = logging.getLogger('nginsec')

# ── Flask & Socket.io ──────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# job_id → { status, filepath, error }
jobs: dict = {}


# ── Auth decorator ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapped


# ── yt-dlp progress hook ───────────────────────────────────────────────────────
def _parse_pct(s: str) -> float:
    try:
        return float(re.sub(r'[^\d.]', '', s or '0'))
    except ValueError:
        return 0.0


def _make_hook(job_id: str, sid: str):
    """Returns a yt-dlp progress hook that emits Socket.io events to `sid`."""
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


# ── Background download worker ─────────────────────────────────────────────────
def _worker(job_id: str, url: str, fmt: str, is_audio: bool, sid: str):
    prefix  = job_id[:8]
    out_tpl = str(DOWNLOADS_DIR / f'{prefix}_%(title)s.%(ext)s')

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
    else:
        opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the produced file (ignore .part temporaries)
        candidates = [
            f for f in DOWNLOADS_DIR.iterdir()
            if f.name.startswith(prefix) and f.suffix != '.part'
        ]
        if not candidates:
            raise FileNotFoundError('Output file not found after download.')

        target = max(candidates, key=lambda f: f.stat().st_mtime)
        jobs[job_id].update(status='complete', filepath=str(target))

        socketio.emit('complete', {
            'job_id':   job_id,
            'filename': target.name,
        }, room=sid)
        log.info(f'Done [{prefix}] → {target.name}')

    except Exception as exc:
        jobs[job_id].update(status='error', error=str(exc))
        socketio.emit('dl_error', {
            'job_id': job_id,
            'error':  str(exc),
        }, room=sid)
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
    formats.append({
        'value': 'bestaudio/best',
        'label': 'Audio Only (MP3 ~320 kbps)',
        'type':  'audio',
    })

    dur = meta.get('duration', 0)
    return jsonify({
        'title':      meta.get('title', 'Unknown'),
        'thumbnail':  meta.get('thumbnail', ''),
        'duration':   meta.get('duration_string') or (f'{dur//60}:{dur%60:02d}' if dur else '—'),
        'uploader':   meta.get('uploader', 'Unknown'),
        'view_count': meta.get('view_count', 0),
        'formats':    formats,
    })


@app.route('/download', methods=['POST'])
@login_required
def start_download():
    body     = request.get_json() or {}
    url      = body.get('url', '').strip()
    fmt      = body.get('format', 'bestvideo+bestaudio/best')
    is_audio = bool(body.get('is_audio', False))
    sid      = body.get('socket_id', '')

    if not url or not sid:
        return jsonify({'error': 'Missing url or socket_id'}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'starting'}

    threading.Thread(
        target=_worker,
        args=(job_id, url, fmt, is_audio, sid),
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


# ── Socket.io ──────────────────────────────────────────────────────────────────
@socketio.on('connect')
def on_connect():
    log.info(f'WS connected: {request.sid}')


@socketio.on('disconnect')
def on_disconnect():
    log.info(f'WS disconnected: {request.sid}')


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print()
    print('  ┌─────────────────────────────────────────┐')
    print('  │   nginsec Video Cloud Suite · Web Ed.   │')
    print('  ├─────────────────────────────────────────┤')
    print(f'  │   URL  : http://0.0.0.0:5000            │')
    print(f'  │   Key  : {SYSTEM_ACCESS_KEY:<32}│')
    print('  └─────────────────────────────────────────┘')
    print()
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
