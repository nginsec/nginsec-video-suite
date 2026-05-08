"""
Custom Tkinter UI - nginsec YouTube Video Suite
Professional dark mode GUI with neon green accents
"""
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import threading
from pathlib import Path
from datetime import datetime, timedelta
from config import (
    APP_NAME, APP_VERSION, BRANDING_TEXT, COLORS, WINDOW_WIDTH, WINDOW_HEIGHT,
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, OUTPUT_DIR, VIDEO_QUALITIES, AUDIO_QUALITIES
)
from download_manager import DownloadManager


class NginsecApp(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.download_manager = DownloadManager(progress_callback=self._on_download_progress)
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        """Configure main window"""
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(800, 600)

        # Set color scheme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Configure window background
        self.configure(fg_color=COLORS["primary_bg"])

    def setup_ui(self):
        """Build the complete UI"""
        # Main container
        main_container = ctk.CTkFrame(self, fg_color=COLORS["primary_bg"])
        main_container.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Header
        self._build_header(main_container)

        # Content area with two columns
        content_frame = ctk.CTkFrame(main_container, fg_color=COLORS["primary_bg"])
        content_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Left column - Input and options
        left_column = ctk.CTkFrame(content_frame, fg_color=COLORS["primary_bg"])
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self._build_input_section(left_column)
        self._build_download_options(left_column)

        # Right column - Console and stats
        right_column = ctk.CTkFrame(content_frame, fg_color=COLORS["primary_bg"])
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self._build_console_section(right_column)

        # Footer
        self._build_footer(main_container)

    def _build_header(self, parent):
        """Build application header with branding"""
        header_frame = ctk.CTkFrame(parent, fg_color=COLORS["secondary_bg"], corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 10))

        # Title and version
        title_label = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=FONT_LARGE,
            text_color=COLORS["accent"]
        )
        title_label.pack(side="left", padx=15, pady=10)

        version_label = ctk.CTkLabel(
            header_frame,
            text=f"v{APP_VERSION}",
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"]
        )
        version_label.pack(side="left", padx=5, pady=10)

        # Branding
        branding_label = ctk.CTkLabel(
            header_frame,
            text=BRANDING_TEXT,
            font=FONT_SMALL,
            text_color=COLORS["accent"]
        )
        branding_label.pack(side="right", padx=15, pady=10)

    def _build_input_section(self, parent):
        """Build URL input section"""
        section_frame = ctk.CTkFrame(parent, fg_color=COLORS["secondary_bg"], corner_radius=8)
        section_frame.pack(fill="x", pady=(0, 10))

        label = ctk.CTkLabel(
            section_frame,
            text="YouTube URL",
            font=FONT_MEDIUM,
            text_color=COLORS["accent"]
        )
        label.pack(anchor="w", padx=15, pady=(10, 5))

        self.url_entry = ctk.CTkEntry(
            section_frame,
            placeholder_text="Paste YouTube URL here...",
            fg_color=COLORS["tertiary_bg"],
            border_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            border_width=2,
            height=40
        )
        self.url_entry.pack(fill="x", padx=15, pady=(5, 10))
        self.url_entry.bind("<Return>", lambda e: self._fetch_video_info())

        # Fetch button
        fetch_btn = ctk.CTkButton(
            section_frame,
            text="Fetch Video Info",
            command=self._fetch_video_info,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["primary_bg"],
            font=FONT_MEDIUM,
            height=35
        )
        fetch_btn.pack(fill="x", padx=15, pady=(0, 10))

        # Video info display
        self.video_info_frame = ctk.CTkFrame(section_frame, fg_color=COLORS["tertiary_bg"], corner_radius=6)
        self.video_info_frame.pack(fill="both", padx=15, pady=10, expand=True)

        self.video_info_label = ctk.CTkLabel(
            self.video_info_frame,
            text="Video information will appear here",
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"],
            wraplength=300,
            justify="left"
        )
        self.video_info_label.pack(padx=10, pady=10, anchor="nw")

    def _build_download_options(self, parent):
        """Build download options section"""
        section_frame = ctk.CTkFrame(parent, fg_color=COLORS["secondary_bg"], corner_radius=8)
        section_frame.pack(fill="x")

        label = ctk.CTkLabel(
            section_frame,
            text="Download Options",
            font=FONT_MEDIUM,
            text_color=COLORS["accent"]
        )
        label.pack(anchor="w", padx=15, pady=(10, 5))

        # Video quality selection
        quality_label = ctk.CTkLabel(
            section_frame,
            text="Video Quality:",
            font=FONT_SMALL,
            text_color=COLORS["text_primary"]
        )
        quality_label.pack(anchor="w", padx=15, pady=(5, 2))

        self.quality_var = ctk.StringVar(value=VIDEO_QUALITIES[0])
        quality_dropdown = ctk.CTkOptionMenu(
            section_frame,
            values=VIDEO_QUALITIES,
            variable=self.quality_var,
            fg_color=COLORS["tertiary_bg"],
            button_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            font=FONT_SMALL
        )
        quality_dropdown.pack(fill="x", padx=15, pady=2)

        # Audio quality selection
        audio_label = ctk.CTkLabel(
            section_frame,
            text="Audio Quality (MP3):",
            font=FONT_SMALL,
            text_color=COLORS["text_primary"]
        )
        audio_label.pack(anchor="w", padx=15, pady=(10, 2))

        self.audio_quality_var = ctk.StringVar(value=list(AUDIO_QUALITIES.keys())[0])
        audio_dropdown = ctk.CTkOptionMenu(
            section_frame,
            values=list(AUDIO_QUALITIES.keys()),
            variable=self.audio_quality_var,
            fg_color=COLORS["tertiary_bg"],
            button_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            font=FONT_SMALL
        )
        audio_dropdown.pack(fill="x", padx=15, pady=2)

        # Download buttons frame
        buttons_frame = ctk.CTkFrame(section_frame, fg_color=COLORS["secondary_bg"])
        buttons_frame.pack(fill="x", padx=15, pady=10)

        self.download_video_btn = ctk.CTkButton(
            buttons_frame,
            text="Download Video",
            command=self._start_video_download,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["primary_bg"],
            font=FONT_MEDIUM,
            height=35
        )
        self.download_video_btn.pack(fill="x", pady=(0, 8))

        self.download_audio_btn = ctk.CTkButton(
            buttons_frame,
            text="Download Audio (MP3)",
            command=self._start_audio_download,
            fg_color=COLORS["info"],
            hover_color="#0099cc",
            text_color=COLORS["primary_bg"],
            font=FONT_MEDIUM,
            height=35
        )
        self.download_audio_btn.pack(fill="x", pady=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel Download",
            command=self._cancel_download,
            fg_color=COLORS["error"],
            hover_color="#cc0000",
            text_color=COLORS["primary_bg"],
            font=FONT_MEDIUM,
            height=35,
            state="disabled"
        )
        self.cancel_btn.pack(fill="x")

        # Metadata options
        self.metadata_var = ctk.BooleanVar(value=True)
        metadata_check = ctk.CTkCheckBox(
            section_frame,
            text="Download Metadata (Description, Thumbnail, Tags)",
            variable=self.metadata_var,
            text_color=COLORS["text_primary"],
            font=FONT_SMALL,
            checkmark_color=COLORS["accent"],
            fg_color=COLORS["accent"]
        )
        metadata_check.pack(anchor="w", padx=15, pady=(10, 10))

    def _build_console_section(self, parent):
        """Build console and progress section"""
        section_frame = ctk.CTkFrame(parent, fg_color=COLORS["secondary_bg"], corner_radius=8)
        section_frame.pack(fill="both", expand=True)

        label = ctk.CTkLabel(
            section_frame,
            text="Download Console",
            font=FONT_MEDIUM,
            text_color=COLORS["accent"]
        )
        label.pack(anchor="w", padx=15, pady=(10, 5))

        # Console output
        self.console = scrolledtext.ScrolledText(
            section_frame,
            height=15,
            width=40,
            bg=COLORS["tertiary_bg"],
            fg=COLORS["accent"],
            insertbackground=COLORS["accent"],
            font=("Courier", 9),
            relief="flat",
            borderwidth=0
        )
        self.console.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # Progress bar
        progress_label = ctk.CTkLabel(
            section_frame,
            text="Progress",
            font=FONT_SMALL,
            text_color=COLORS["text_primary"]
        )
        progress_label.pack(anchor="w", padx=15, pady=(0, 2))

        self.progress_bar = ctk.CTkProgressBar(
            section_frame,
            fg_color=COLORS["tertiary_bg"],
            progress_color=COLORS["accent"],
            height=8
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_bar.set(0)

        # Stats label
        self.stats_label = ctk.CTkLabel(
            section_frame,
            text="Ready to download",
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"]
        )
        self.stats_label.pack(anchor="w", padx=15, pady=(0, 10))

    def _build_footer(self, parent):
        """Build footer with output directory link"""
        footer_frame = ctk.CTkFrame(parent, fg_color=COLORS["secondary_bg"], corner_radius=8)
        footer_frame.pack(fill="x", pady=(10, 0))

        info_text = f"Downloads saved to: {OUTPUT_DIR}"
        footer_label = ctk.CTkLabel(
            footer_frame,
            text=info_text,
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"]
        )
        footer_label.pack(anchor="w", padx=15, pady=10)

        open_btn = ctk.CTkButton(
            footer_frame,
            text="Open Download Folder",
            command=self._open_output_folder,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["primary_bg"],
            font=FONT_SMALL,
            height=30,
            width=150
        )
        open_btn.pack(side="right", padx=15, pady=10)

    def _fetch_video_info(self):
        """Fetch and display video information"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a YouTube URL")
            return

        self._log("🔍 Fetching video information...")
        self.video_info_label.configure(text="Loading...")

        def fetch_thread():
            info = self.download_manager.get_video_info(url)
            if info:
                self._display_video_info(info)
            else:
                self._log("❌ Failed to fetch video information")

        threading.Thread(target=fetch_thread, daemon=True).start()

    def _display_video_info(self, info):
        """Display fetched video information"""
        info_text = f"""
📺 Title: {info.get('title', 'N/A')}
👤 Uploader: {info.get('uploader', 'N/A')}
⏱️  Duration: {self._format_duration(info.get('duration', 0))}
📅 Uploaded: {info.get('upload_date', 'N/A')}
👁️  Views: {info.get('view_count', 0):,}
👍 Likes: {info.get('like_count', 0):,}

📹 Available Qualities: {', '.join(info.get('formats_available', ['N/A']))}
📝 Subtitles: {', '.join(info.get('subtitles', ['None'])) or 'None'}
        """
        self.video_info_label.configure(text=info_text)
        self._log(f"✅ Video info loaded: {info['title']}")

    def _start_video_download(self):
        """Start video download"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a YouTube URL")
            return

        quality = self.quality_var.get()
        self._log(f"⬇️  Starting video download: {quality}")
        self.cancel_btn.configure(state="normal")
        self.download_video_btn.configure(state="disabled")
        self.download_audio_btn.configure(state="disabled")

        def download_thread():
            try:
                self.download_manager.download_video(url, quality)
                if self.metadata_var.get():
                    info = self.download_manager.get_video_info(url)
                    if info:
                        self.download_manager.download_metadata(url, info['title'])
                        self._log("📦 Metadata downloaded")
            finally:
                self.cancel_btn.configure(state="disabled")
                self.download_video_btn.configure(state="normal")
                self.download_audio_btn.configure(state="normal")

        threading.Thread(target=download_thread, daemon=True).start()

    def _start_audio_download(self):
        """Start audio download"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a YouTube URL")
            return

        audio_quality_text = self.audio_quality_var.get()
        audio_quality_kbps = AUDIO_QUALITIES[audio_quality_text]
        self._log(f"🎵 Starting audio extraction: {audio_quality_kbps}kbps MP3")
        self.cancel_btn.configure(state="normal")
        self.download_video_btn.configure(state="disabled")
        self.download_audio_btn.configure(state="disabled")

        def download_thread():
            try:
                self.download_manager.download_audio(url, audio_quality_kbps)
                if self.metadata_var.get():
                    info = self.download_manager.get_video_info(url)
                    if info:
                        self.download_manager.download_metadata(url, info['title'])
                        self._log("📦 Metadata downloaded")
            finally:
                self.cancel_btn.configure(state="disabled")
                self.download_video_btn.configure(state="normal")
                self.download_audio_btn.configure(state="normal")

        threading.Thread(target=download_thread, daemon=True).start()

    def _cancel_download(self):
        """Cancel current download"""
        self.download_manager.cancel_download()
        self._log("⚠️  Download cancelled by user")

    def _on_download_progress(self, progress_data):
        """Handle download progress updates"""
        status = progress_data.get('status')

        if status == 'started':
            self._log(f"▶️  {progress_data.get('message', 'Started')}")
        elif status == 'downloading':
            downloaded = progress_data.get('downloaded_bytes', 0)
            total = progress_data.get('total_bytes_estimate', 0) or progress_data.get('total_bytes', 0)
            speed = progress_data.get('speed', 0)
            eta = progress_data.get('eta', 0)

            if total > 0:
                progress = downloaded / total
                self.progress_bar.set(progress)

                # Format stats
                size_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                speed_mbps = speed / (1024 * 1024) if speed else 0
                eta_str = str(timedelta(seconds=int(eta))) if eta else "N/A"

                stats = f"Progress: {size_mb:.1f}/{total_mb:.1f} MB | Speed: {speed_mbps:.2f} MB/s | ETA: {eta_str}"
                self.stats_label.configure(text=stats)
        elif status == 'finished':
            self.progress_bar.set(1.0)
            self._log(f"✅ {progress_data.get('message', 'Finished')}")
        elif status == 'error':
            self._log(f"❌ Error: {progress_data.get('error', 'Unknown error')}")
            self.progress_bar.set(0)

    def _log(self, message):
        """Add message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        console_message = f"[{timestamp}] {message}\n"
        self.console.insert("end", console_message)
        self.console.see("end")
        self.update()

    def _format_duration(self, seconds):
        """Format duration in seconds to readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def _open_output_folder(self):
        """Open the output directory"""
        import subprocess
        import sys
        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'explorer "{OUTPUT_DIR}"')
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(OUTPUT_DIR)])
            else:
                subprocess.Popen(['xdg-open', str(OUTPUT_DIR)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
