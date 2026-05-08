"""
nginsec Video Cloud Suite v2 — Desktop GUI
GitHub-inspired dark theme · Sidebar navigation · CustomTkinter
"""
import subprocess
import sys
import threading
from datetime import timedelta
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from config import (
    APP_NAME, APP_VERSION, BRANDING_TEXT, COLORS,
    WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH,
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_MONO,
    OUTPUT_DIR, VIDEO_QUALITIES, AUDIO_QUALITIES,
)
from download_manager import DownloadManager, detect_platform


# ── App ────────────────────────────────────────────────────────────────────────

class NginsecApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.dm = DownloadManager(progress_callback=self._on_progress)
        self._video_info = None
        self._active_tab = ''
        self._queue_widgets: list = []
        self._oauth2_win = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self._setup_window()
        self._build_layout()
        self._show_tab('download')

    # ── Window ─────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(960, 640)
        self.configure(fg_color=COLORS['primary_bg'])

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar
        self._sidebar = ctk.CTkFrame(
            self, fg_color=COLORS['sidebar_bg'],
            width=SIDEBAR_WIDTH, corner_radius=0,
        )
        self._sidebar.pack(side='left', fill='y')
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Separator line
        sep = ctk.CTkFrame(self, fg_color=COLORS['border'], width=1, corner_radius=0)
        sep.pack(side='left', fill='y')

        # Content
        self._content = ctk.CTkFrame(self, fg_color=COLORS['primary_bg'], corner_radius=0)
        self._content.pack(side='left', fill='both', expand=True)

        self._frames: dict = {}
        self._build_tab_download()
        self._build_tab_queue()
        self._build_tab_history()
        self._build_tab_settings()

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        # Logo
        logo = ctk.CTkFrame(self._sidebar, fg_color='transparent')
        logo.pack(fill='x', padx=16, pady=(20, 28))

        ctk.CTkLabel(
            logo, text='nginsec',
            font=('Segoe UI', 17, 'bold'),
            text_color=COLORS['accent'],
        ).pack(side='left')
        ctk.CTkLabel(
            logo, text=f'v{APP_VERSION}',
            font=FONT_SMALL,
            text_color=COLORS['text_secondary'],
        ).pack(side='left', padx=(5, 0), pady=(5, 0))

        # Nav items
        self._nav_btns: dict = {}
        nav_items = [
            ('download', 'Download'),
            ('queue',    'Queue'),
            ('history',  'History'),
            ('settings', 'Settings'),
        ]
        for tab_id, label in nav_items:
            btn = ctk.CTkButton(
                self._sidebar,
                text=label,
                anchor='w',
                fg_color='transparent',
                hover_color=COLORS['tertiary_bg'],
                text_color=COLORS['text_secondary'],
                font=FONT_MEDIUM,
                height=38,
                corner_radius=6,
                command=lambda t=tab_id: self._show_tab(t),
            )
            btn.pack(fill='x', padx=10, pady=2)
            self._nav_btns[tab_id] = btn

        # Queue badge label (updated dynamically)
        self._queue_badge = ctk.CTkLabel(
            self._sidebar, text='',
            font=FONT_SMALL, text_color=COLORS['warning'],
        )
        self._queue_badge.place_forget()  # hidden until items added

        # Bottom branding
        ctk.CTkLabel(
            self._sidebar, text='nginsec',
            font=FONT_SMALL, text_color=COLORS['text_secondary'],
        ).pack(side='bottom', pady=(0, 8))
        ctk.CTkFrame(self._sidebar, fg_color=COLORS['border'], height=1).pack(
            side='bottom', fill='x', padx=16, pady=(0, 4),
        )

    def _show_tab(self, tab_id: str):
        for fid, frame in self._frames.items():
            frame.pack_forget()
        self._frames[tab_id].pack(fill='both', expand=True)
        self._active_tab = tab_id

        for tid, btn in self._nav_btns.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=COLORS['tertiary_bg'],
                    text_color=COLORS['accent'],
                )
            else:
                btn.configure(
                    fg_color='transparent',
                    text_color=COLORS['text_secondary'],
                )

        if tab_id == 'history':
            threading.Thread(target=self._refresh_history, daemon=True).start()

    # ── Card helper ────────────────────────────────────────────────────────────

    def _card(self, parent, title: str = '') -> ctk.CTkFrame:
        outer = ctk.CTkFrame(
            parent,
            fg_color=COLORS['secondary_bg'],
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border'],
        )
        outer.pack(fill='x', pady=(0, 10))
        if title:
            ctk.CTkLabel(
                outer, text=title.upper(),
                font=('Segoe UI', 9, 'bold'),
                text_color=COLORS['text_secondary'],
            ).pack(anchor='w', padx=14, pady=(10, 3))
        return outer

    # ── Download tab ───────────────────────────────────────────────────────────

    def _build_tab_download(self):
        scroll = ctk.CTkScrollableFrame(
            self._content, fg_color='transparent',
            scrollbar_button_color=COLORS['border'],
        )
        self._frames['download'] = scroll
        p = scroll  # shorthand

        # URL card
        url_card = self._card(p, 'Video URL')

        row = ctk.CTkFrame(url_card, fg_color='transparent')
        row.pack(fill='x', padx=14, pady=(4, 4))

        self._url_entry = ctk.CTkEntry(
            row,
            placeholder_text='Paste URL — YouTube, Instagram, TikTok, Twitch, Vimeo, SoundCloud…',
            fg_color=COLORS['tertiary_bg'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            height=40, font=FONT_MEDIUM,
        )
        self._url_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self._url_entry.bind('<Return>', lambda e: self._fetch_info())

        self._platform_lbl = ctk.CTkLabel(
            row, text='', font=FONT_SMALL,
            text_color=COLORS['accent'], width=90,
        )
        self._platform_lbl.pack(side='left', padx=(0, 8))

        self._fetch_btn = ctk.CTkButton(
            row, text='Analyze',
            command=self._fetch_info,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color='#0d1117',
            font=FONT_MEDIUM, height=40, width=96,
        )
        self._fetch_btn.pack(side='left')

        # Video info
        info_card = self._card(p, 'Video Info')
        self._info_lbl = ctk.CTkLabel(
            info_card,
            text='Paste a URL above and click Analyze.',
            font=FONT_SMALL,
            text_color=COLORS['text_secondary'],
            wraplength=560, justify='left',
        )
        self._info_lbl.pack(anchor='w', padx=14, pady=(4, 12))

        # Quality card
        q_card = self._card(p, 'Format')
        q_row = ctk.CTkFrame(q_card, fg_color='transparent')
        q_row.pack(fill='x', padx=14, pady=(4, 12))

        ctk.CTkLabel(q_row, text='Video', font=FONT_SMALL,
                     text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 6))
        self._quality_var = ctk.StringVar(value='1080p (Full HD)')
        ctk.CTkOptionMenu(
            q_row, values=VIDEO_QUALITIES, variable=self._quality_var,
            fg_color=COLORS['tertiary_bg'], button_color=COLORS['tertiary_bg'],
            button_hover_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONT_SMALL, width=180,
        ).pack(side='left', padx=(0, 24))

        ctk.CTkLabel(q_row, text='Audio', font=FONT_SMALL,
                     text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 6))
        self._audio_var = ctk.StringVar(value=list(AUDIO_QUALITIES.keys())[0])
        ctk.CTkOptionMenu(
            q_row, values=list(AUDIO_QUALITIES.keys()), variable=self._audio_var,
            fg_color=COLORS['tertiary_bg'], button_color=COLORS['tertiary_bg'],
            button_hover_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONT_SMALL, width=170,
        ).pack(side='left')

        # Advanced card
        adv_card = self._card(p, 'Advanced Options')

        clip_row = ctk.CTkFrame(adv_card, fg_color='transparent')
        clip_row.pack(fill='x', padx=14, pady=(4, 6))

        ctk.CTkLabel(clip_row, text='Clip start', font=FONT_SMALL,
                     text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 6))
        self._clip_start = ctk.CTkEntry(
            clip_row, placeholder_text='HH:MM:SS',
            fg_color=COLORS['tertiary_bg'], border_color=COLORS['border'],
            text_color=COLORS['text_primary'], height=34, width=120, font=FONT_SMALL,
        )
        self._clip_start.pack(side='left', padx=(0, 18))

        ctk.CTkLabel(clip_row, text='Clip end', font=FONT_SMALL,
                     text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 6))
        self._clip_end = ctk.CTkEntry(
            clip_row, placeholder_text='HH:MM:SS',
            fg_color=COLORS['tertiary_bg'], border_color=COLORS['border'],
            text_color=COLORS['text_primary'], height=34, width=120, font=FONT_SMALL,
        )
        self._clip_end.pack(side='left')

        check_row = ctk.CTkFrame(adv_card, fg_color='transparent')
        check_row.pack(fill='x', padx=14, pady=(2, 12))

        self._embed_subs_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            check_row, text='Embed subtitles (TR / EN)',
            variable=self._embed_subs_var,
            checkmark_color=COLORS['accent'], fg_color=COLORS['accent'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONT_SMALL,
        ).pack(side='left', padx=(0, 24))

        self._meta_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            check_row, text='Save metadata',
            variable=self._meta_var,
            checkmark_color=COLORS['accent'], fg_color=COLORS['accent'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONT_SMALL,
        ).pack(side='left')

        # Action buttons
        btn_card = self._card(p)
        btn_row = ctk.CTkFrame(btn_card, fg_color='transparent')
        btn_row.pack(fill='x', padx=14, pady=12)

        self._dl_vid_btn = ctk.CTkButton(
            btn_row, text='Download Video',
            command=self._start_video,
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            text_color='#0d1117', font=FONT_MEDIUM, height=40,
        )
        self._dl_vid_btn.pack(side='left', expand=True, fill='x', padx=(0, 6))

        self._dl_mp3_btn = ctk.CTkButton(
            btn_row, text='Download MP3',
            command=self._start_audio,
            fg_color=COLORS['secondary_bg'], hover_color=COLORS['tertiary_bg'],
            border_color=COLORS['border'], border_width=1,
            text_color=COLORS['text_primary'], font=FONT_MEDIUM, height=40,
        )
        self._dl_mp3_btn.pack(side='left', expand=True, fill='x', padx=(0, 6))

        self._queue_btn = ctk.CTkButton(
            btn_row, text='+ Queue',
            command=self._add_to_queue,
            fg_color=COLORS['secondary_bg'], hover_color=COLORS['tertiary_bg'],
            border_color=COLORS['border'], border_width=1,
            text_color=COLORS['text_secondary'], font=FONT_SMALL, height=40, width=84,
        )
        self._queue_btn.pack(side='left', padx=(0, 6))

        self._cancel_btn = ctk.CTkButton(
            btn_row, text='Cancel',
            command=self._cancel,
            fg_color=COLORS['secondary_bg'], hover_color='#2d1a1a',
            border_color=COLORS['error'], border_width=1,
            text_color=COLORS['error'], font=FONT_SMALL, height=40, width=76,
            state='disabled',
        )
        self._cancel_btn.pack(side='left')

        # Progress card
        prog_card = self._card(p, 'Progress')

        prog_top = ctk.CTkFrame(prog_card, fg_color='transparent')
        prog_top.pack(fill='x', padx=14, pady=(4, 4))

        self._prog_status = ctk.CTkLabel(
            prog_top, text='Ready',
            font=FONT_SMALL, text_color=COLORS['text_secondary'],
        )
        self._prog_status.pack(side='left')

        self._prog_pct = ctk.CTkLabel(
            prog_top, text='',
            font=('Segoe UI', 13, 'bold'), text_color=COLORS['accent'],
        )
        self._prog_pct.pack(side='right')

        self._prog_bar = ctk.CTkProgressBar(
            prog_card,
            fg_color=COLORS['tertiary_bg'],
            progress_color=COLORS['accent'],
            height=6,
        )
        self._prog_bar.pack(fill='x', padx=14, pady=(0, 6))
        self._prog_bar.set(0)

        stats_row = ctk.CTkFrame(prog_card, fg_color='transparent')
        stats_row.pack(fill='x', padx=14, pady=(0, 12))

        self._spd_lbl  = self._stat_label(stats_row, 'Speed: —')
        self._eta_lbl  = self._stat_label(stats_row, 'ETA: —')
        self._size_lbl = self._stat_label(stats_row, '')

    def _stat_label(self, parent, text: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(parent, text=text, font=FONT_SMALL,
                           text_color=COLORS['text_secondary'])
        lbl.pack(side='left', padx=(0, 16))
        return lbl

    # ── Queue tab ──────────────────────────────────────────────────────────────

    def _build_tab_queue(self):
        frame = ctk.CTkFrame(self._content, fg_color='transparent', corner_radius=0)
        self._frames['queue'] = frame

        header = ctk.CTkFrame(frame, fg_color='transparent')
        header.pack(fill='x', padx=20, pady=(18, 10))

        ctk.CTkLabel(header, text='Download Queue', font=FONT_LARGE,
                     text_color=COLORS['text_primary']).pack(side='left')
        self._queue_count_lbl = ctk.CTkLabel(
            header, text='0 items', font=FONT_SMALL,
            text_color=COLORS['text_secondary'],
        )
        self._queue_count_lbl.pack(side='left', padx=(8, 0), pady=(4, 0))

        ctrl = ctk.CTkFrame(frame, fg_color='transparent')
        ctrl.pack(fill='x', padx=20, pady=(0, 10))

        ctk.CTkButton(
            ctrl, text='Start Queue',
            command=self._start_queue,
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            text_color='#0d1117', font=FONT_MEDIUM, height=36, width=120,
        ).pack(side='left', padx=(0, 8))
        ctk.CTkButton(
            ctrl, text='Clear Queue',
            command=self._clear_queue,
            fg_color=COLORS['secondary_bg'], hover_color=COLORS['tertiary_bg'],
            border_color=COLORS['border'], border_width=1,
            text_color=COLORS['text_secondary'], font=FONT_SMALL, height=36, width=106,
        ).pack(side='left')

        self._queue_scroll = ctk.CTkScrollableFrame(
            frame,
            fg_color=COLORS['secondary_bg'],
            border_color=COLORS['border'], border_width=1,
            corner_radius=8,
        )
        self._queue_scroll.pack(fill='both', expand=True, padx=20, pady=(0, 16))

        self._queue_empty_lbl = ctk.CTkLabel(
            self._queue_scroll,
            text='Queue is empty. Add items from the Download tab.',
            font=FONT_SMALL, text_color=COLORS['text_secondary'],
        )
        self._queue_empty_lbl.pack(pady=28)

    # ── History tab ────────────────────────────────────────────────────────────

    def _build_tab_history(self):
        frame = ctk.CTkFrame(self._content, fg_color='transparent', corner_radius=0)
        self._frames['history'] = frame

        header = ctk.CTkFrame(frame, fg_color='transparent')
        header.pack(fill='x', padx=20, pady=(18, 10))

        ctk.CTkLabel(header, text='Download History', font=FONT_LARGE,
                     text_color=COLORS['text_primary']).pack(side='left')

        ctrl = ctk.CTkFrame(frame, fg_color='transparent')
        ctrl.pack(fill='x', padx=20, pady=(0, 10))

        ctk.CTkButton(
            ctrl, text='Refresh',
            command=lambda: threading.Thread(target=self._refresh_history, daemon=True).start(),
            fg_color=COLORS['secondary_bg'], hover_color=COLORS['tertiary_bg'],
            border_color=COLORS['border'], border_width=1,
            text_color=COLORS['text_secondary'], font=FONT_SMALL, height=34, width=88,
        ).pack(side='left', padx=(0, 8))
        ctk.CTkButton(
            ctrl, text='Clear History',
            command=self._clear_history,
            fg_color=COLORS['secondary_bg'], hover_color='#2d1a1a',
            border_color=COLORS['error'], border_width=1,
            text_color=COLORS['error'], font=FONT_SMALL, height=34, width=110,
        ).pack(side='left', padx=(0, 8))
        ctk.CTkButton(
            ctrl, text='Open Folder',
            command=self._open_folder,
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            text_color='#0d1117', font=FONT_SMALL, height=34, width=100,
        ).pack(side='right')

        self._hist_scroll = ctk.CTkScrollableFrame(
            frame,
            fg_color=COLORS['secondary_bg'],
            border_color=COLORS['border'], border_width=1,
            corner_radius=8,
        )
        self._hist_scroll.pack(fill='both', expand=True, padx=20, pady=(0, 16))

        self._hist_empty_lbl = ctk.CTkLabel(
            self._hist_scroll,
            text='No downloads yet.',
            font=FONT_SMALL, text_color=COLORS['text_secondary'],
        )
        self._hist_empty_lbl.pack(pady=28)

    # ── Settings tab ───────────────────────────────────────────────────────────

    def _build_tab_settings(self):
        scroll = ctk.CTkScrollableFrame(
            self._content, fg_color='transparent',
            scrollbar_button_color=COLORS['border'],
        )
        self._frames['settings'] = scroll
        p = scroll

        ctk.CTkLabel(p, text='Settings', font=FONT_LARGE,
                     text_color=COLORS['text_primary']).pack(
            anchor='w', padx=20, pady=(16, 12),
        )

        notif_card = self._card(p, 'Notifications')
        self._notif_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            notif_card,
            text='Desktop notification when download completes',
            variable=self._notif_var,
            checkmark_color=COLORS['accent'], fg_color=COLORS['accent'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONT_SMALL,
        ).pack(anchor='w', padx=14, pady=(6, 14))

        folder_card = self._card(p, 'Output Folder')
        ctk.CTkLabel(
            folder_card, text=str(OUTPUT_DIR),
            font=FONT_SMALL, text_color=COLORS['text_secondary'],
        ).pack(anchor='w', padx=14, pady=(4, 6))
        ctk.CTkButton(
            folder_card, text='Open Folder',
            command=self._open_folder,
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            text_color='#0d1117', font=FONT_SMALL, height=32, width=110,
        ).pack(anchor='w', padx=14, pady=(0, 12))

        about_card = self._card(p, 'About')
        ctk.CTkLabel(
            about_card,
            text=f'{APP_NAME}  ·  v{APP_VERSION}\n{BRANDING_TEXT}',
            font=FONT_SMALL, text_color=COLORS['text_secondary'], justify='left',
        ).pack(anchor='w', padx=14, pady=(6, 14))

    # ── Fetch info ─────────────────────────────────────────────────────────────

    def _fetch_info(self):
        url = self._url_entry.get().strip()
        if not url:
            return
        platform, _ = detect_platform(url)
        self._platform_lbl.configure(
            text=platform if platform != 'Unknown' else '',
        )
        self._fetch_btn.configure(state='disabled', text='…')
        self._info_lbl.configure(text='Fetching…', text_color=COLORS['text_secondary'])

        def _run():
            info = self.dm.get_video_info(url)
            self.after(0, lambda: self._on_info(info))

        threading.Thread(target=_run, daemon=True).start()

    def _on_info(self, info):
        self._fetch_btn.configure(state='normal', text='Analyze')
        if not info:
            self._info_lbl.configure(
                text='Could not fetch info. Check the URL and try again.',
                text_color=COLORS['error'],
            )
            return
        self._video_info = info
        dur     = self._fmt_dur(info.get('duration', 0))
        views   = self._fmt_num(info.get('view_count', 0))
        qualities = ', '.join(info.get('formats_available', []) or ['—'])
        subs    = ', '.join(info.get('subtitles', []) or []) or 'none'
        text = (
            f"{info['title']}\n"
            f"Channel: {info.get('uploader', '—')}   "
            f"Duration: {dur}   Views: {views}\n"
            f"Quality: {qualities}   Subtitles: {subs}"
        )
        self._info_lbl.configure(text=text, text_color=COLORS['text_primary'])

    # ── Download actions ───────────────────────────────────────────────────────

    def _start_video(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning('URL Required', 'Paste a URL first.')
            return
        self._set_buttons_downloading(True)
        quality = self._quality_var.get()
        clip_s  = self._clip_start.get().strip()
        clip_e  = self._clip_end.get().strip()
        subs    = self._embed_subs_var.get()

        def _run():
            self.dm.download_video(url, quality, clip_s, clip_e, subs)
            if self._meta_var.get() and self._video_info:
                self.dm.download_metadata(url, self._video_info.get('title', 'video'))

        threading.Thread(target=_run, daemon=True).start()

    def _start_audio(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning('URL Required', 'Paste a URL first.')
            return
        self._set_buttons_downloading(True)
        kbps = AUDIO_QUALITIES[self._audio_var.get()]
        threading.Thread(target=lambda: self.dm.download_audio(url, kbps), daemon=True).start()

    def _cancel(self):
        self.dm.cancel_download()
        self._prog_status.configure(text='Cancelled', text_color=COLORS['warning'])
        self._set_buttons_downloading(False)

    def _add_to_queue(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning('URL Required', 'Paste a URL first.')
            return
        self.dm.add_to_queue(url, 'video', self._quality_var.get())
        self._refresh_queue_tab()
        self._show_tab('queue')

    def _start_queue(self):
        if not self.dm.queue:
            return
        self.dm.process_queue(done_callback=lambda: self.after(0, self._refresh_queue_tab))

    def _clear_queue(self):
        self.dm.clear_queue()
        self._refresh_queue_tab()

    # ── Progress callback ──────────────────────────────────────────────────────

    def _on_progress(self, d: dict):
        self.after(0, lambda: self._apply_progress(d))

    def _apply_progress(self, d: dict):
        status = d.get('status')

        if status == 'started':
            self._prog_status.configure(text=d.get('message', 'Starting…'),
                                        text_color=COLORS['text_secondary'])
            self._prog_bar.set(0)
            self._cancel_btn.configure(state='normal')

        elif status == 'downloading':
            self._close_oauth2_dialog()
            downloaded = d.get('downloaded_bytes', 0)
            total      = d.get('total_bytes', 0)
            speed      = d.get('speed') or 0
            eta        = d.get('eta') or 0
            if total > 0:
                pct = downloaded / total
                self._prog_bar.set(pct)
                self._prog_pct.configure(text=f'{pct*100:.0f}%')
            dl_mb  = downloaded / 1048576
            tot_mb = total / 1048576 if total else 0
            spd_mb = speed / 1048576
            eta_s  = str(timedelta(seconds=int(eta))) if eta else '—'
            self._prog_status.configure(
                text=f'{dl_mb:.1f} / {tot_mb:.1f} MB' if tot_mb else f'{dl_mb:.1f} MB',
                text_color=COLORS['text_secondary'],
            )
            self._spd_lbl.configure(text=f'Speed: {spd_mb:.2f} MB/s')
            self._eta_lbl.configure(text=f'ETA: {eta_s}')

        elif status in ('finished', 'completed'):
            self._prog_bar.set(1.0)
            self._prog_pct.configure(text='100%')
            self._prog_status.configure(
                text=d.get('message', 'Done'),
                text_color=COLORS['success'],
            )
            self._set_buttons_downloading(False)
            self._close_oauth2_dialog()

        elif status == 'oauth2_prompt':
            self._show_oauth2_dialog(d.get('message', ''))

        elif status == 'error':
            self._prog_bar.set(0)
            self._prog_pct.configure(text='')
            self._prog_status.configure(
                text=d.get('error', 'Error'),
                text_color=COLORS['error'],
            )
            self._set_buttons_downloading(False)
            self._close_oauth2_dialog()

    def _show_oauth2_dialog(self, message: str):
        """Show (or update) the OAuth2 setup popup when yt-dlp needs authentication."""
        if self._oauth2_win and self._oauth2_win.winfo_exists():
            self._oauth2_win.append(message)
            return

        self._oauth2_win = _OAuth2Dialog(self, message)

    def _close_oauth2_dialog(self):
        if self._oauth2_win and self._oauth2_win.winfo_exists():
            self._oauth2_win.destroy()
        self._oauth2_win = None

    def _set_buttons_downloading(self, downloading: bool):
        state = 'disabled' if downloading else 'normal'
        self._dl_vid_btn.configure(state=state)
        self._dl_mp3_btn.configure(state=state)
        self._cancel_btn.configure(state='normal' if downloading else 'disabled')

    # ── History helpers ────────────────────────────────────────────────────────

    def _refresh_history(self):
        rows = self.dm.history.get_all()
        self.after(0, lambda: self._render_history(rows))

    def _render_history(self, rows: list):
        for w in self._hist_scroll.winfo_children():
            w.destroy()

        if not rows:
            ctk.CTkLabel(
                self._hist_scroll,
                text='No downloads yet.',
                font=FONT_SMALL, text_color=COLORS['text_secondary'],
            ).pack(pady=28)
            return

        # Header row
        hdr = ctk.CTkFrame(self._hist_scroll, fg_color='transparent')
        hdr.pack(fill='x', padx=4, pady=(4, 0))
        for col, w in [('#', 36), ('Title', 260), ('Platform', 90), ('Format', 100), ('Date', 150)]:
            ctk.CTkLabel(hdr, text=col, font=('Segoe UI', 9, 'bold'),
                         text_color=COLORS['text_secondary'], width=w, anchor='w').pack(
                side='left', padx=(0, 4),
            )

        ctk.CTkFrame(self._hist_scroll, fg_color=COLORS['border'], height=1).pack(
            fill='x', padx=4, pady=(4, 4),
        )

        for i, row in enumerate(rows):
            r = ctk.CTkFrame(self._hist_scroll, fg_color='transparent')
            r.pack(fill='x', padx=4, pady=1)

            title_short = (row['title'] or '—')[:42] + ('…' if len(row['title'] or '') > 42 else '')
            status_color = COLORS['success'] if row['status'] == 'complete' else COLORS['error']

            for text, width in [
                (str(i + 1),          36),
                (title_short,         260),
                (row['platform'] or '—', 90),
                (row['format_type'] or '—', 100),
                (row['downloaded_at'] or '—', 150),
            ]:
                ctk.CTkLabel(r, text=text, font=FONT_SMALL,
                             text_color=COLORS['text_primary'], width=width, anchor='w').pack(
                    side='left', padx=(0, 4),
                )

            ctk.CTkLabel(r, text='●', font=('Segoe UI', 8),
                         text_color=status_color, width=16).pack(side='left')

    def _clear_history(self):
        if messagebox.askyesno('Clear History', 'Delete all download history?'):
            self.dm.history.clear()
            threading.Thread(target=self._refresh_history, daemon=True).start()

    # ── Queue helpers ──────────────────────────────────────────────────────────

    def _refresh_queue_tab(self):
        for w in self._queue_scroll.winfo_children():
            w.destroy()

        n = len(self.dm.queue)
        self._queue_count_lbl.configure(text=f'{n} item{"s" if n != 1 else ""}')

        if n == 0:
            ctk.CTkLabel(
                self._queue_scroll,
                text='Queue is empty. Add items from the Download tab.',
                font=FONT_SMALL, text_color=COLORS['text_secondary'],
            ).pack(pady=28)
            return

        for i, item in enumerate(self.dm.queue):
            row = ctk.CTkFrame(self._queue_scroll, fg_color=COLORS['tertiary_bg'],
                               corner_radius=6)
            row.pack(fill='x', pady=2, padx=4)

            url_short = item['url'][:55] + ('…' if len(item['url']) > 55 else '')
            ctk.CTkLabel(row, text=f"{i+1}. {url_short}",
                         font=FONT_SMALL, text_color=COLORS['text_primary'],
                         anchor='w').pack(side='left', padx=10, pady=8, fill='x', expand=True)
            ctk.CTkLabel(row, text=f"{item['mode']} · {item['quality']}",
                         font=FONT_SMALL, text_color=COLORS['text_secondary']).pack(
                side='left', padx=(0, 8),
            )
            ctk.CTkButton(
                row, text='✕', width=30, height=26,
                fg_color='transparent', hover_color='#2d1a1a',
                text_color=COLORS['error'], font=FONT_SMALL,
                command=lambda idx=i: self._remove_queue_item(idx),
            ).pack(side='right', padx=4)

    def _remove_queue_item(self, idx: int):
        self.dm.remove_from_queue(idx)
        self._refresh_queue_tab()

    # ── Misc ───────────────────────────────────────────────────────────────────

    def _open_folder(self):
        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'explorer "{OUTPUT_DIR}"')
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(OUTPUT_DIR)])
            else:
                subprocess.Popen(['xdg-open', str(OUTPUT_DIR)])
        except Exception as e:
            messagebox.showerror('Error', str(e))

    @staticmethod
    def _fmt_dur(seconds: int) -> str:
        if not seconds:
            return '—'
        h, rem = divmod(int(seconds), 3600)
        m, s   = divmod(rem, 60)
        return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'

    @staticmethod
    def _fmt_num(n: int) -> str:
        if not n:
            return '—'
        if n >= 1_000_000_000:
            return f'{n/1e9:.1f}B'
        if n >= 1_000_000:
            return f'{n/1e6:.1f}M'
        if n >= 1_000:
            return f'{n/1e3:.1f}K'
        return str(n)


# ── OAuth2 setup dialog ────────────────────────────────────────────────────────

class _OAuth2Dialog(ctk.CTkToplevel):
    """
    Popup shown when YouTube requires Google authentication (first time only).
    yt-dlp-youtube-oauth2 outputs a URL and a code — user opens the URL,
    enters the code, and the token is cached. Future downloads need no interaction.
    """

    def __init__(self, parent, first_message: str):
        super().__init__(parent)
        self.title('YouTube Authentication')
        self.geometry('520x340')
        self.resizable(False, False)
        self.configure(fg_color='#0d1117')
        self.lift()
        self.focus()
        self.grab_set()
        self._url = ''
        self._build(first_message)

    def _build(self, message: str):
        ctk.CTkLabel(
            self, text='YouTube — Bir kez giriş yapın',
            font=('Segoe UI', 15, 'bold'), text_color='#58a6ff',
        ).pack(pady=(22, 4))

        ctk.CTkLabel(
            self,
            text='Token ilk kurulumdan sonra kaydedilir.\nSonraki indirmelerde hiçbir işlem gerekmez.',
            font=('Segoe UI', 11), text_color='#8b949e', justify='center',
        ).pack(pady=(0, 12))

        self._textbox = ctk.CTkTextbox(
            self, height=110, font=('Consolas', 11),
            fg_color='#161b22', text_color='#c9d1d9', border_color='#30363d', border_width=1,
            state='normal',
        )
        self._textbox.pack(fill='x', padx=20, pady=(0, 10))
        self._textbox.insert('end', message + '\n')

        self._open_btn = ctk.CTkButton(
            self, text='Tarayıcıda Aç', height=34,
            fg_color='#238636', hover_color='#2ea043',
            command=self._open_browser,
        )
        self._open_btn.pack(pady=(0, 6))

        ctk.CTkLabel(
            self, text='Tarayıcıda kodu girin → bu pencere otomatik kapanır.',
            font=('Segoe UI', 10), text_color='#8b949e',
        ).pack()

        self._parse_url(message)

    def append(self, message: str):
        self._textbox.configure(state='normal')
        self._textbox.insert('end', message + '\n')
        self._textbox.see('end')
        self._parse_url(message)

    def _parse_url(self, text: str):
        import re
        m = re.search(r'https?://\S+', text)
        if m:
            self._url = m.group(0)

    def _open_browser(self):
        if self._url:
            import webbrowser
            webbrowser.open(self._url)
