# nginsec YouTube Video Suite - Setup & Installation Guide

## 1. System Requirements

### Operating System
- **Windows 10/11** (Recommended)
- **macOS 10.14+**
- **Linux (Ubuntu 18.04+, Fedora, etc.)**

### Software Requirements
- Python 3.8 or higher
- FFmpeg (required for video/audio processing)
- pip (Python package manager)

## 2. Installation Steps

### Step 1: Install Python
Download from https://www.python.org/downloads/
- **Important**: During installation, check "Add Python to PATH"
- Verify installation:
  ```bash
  python --version
  ```

### Step 2: Install FFmpeg

#### Windows
```bash
# Using Chocolatey (recommended)
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
# Add FFmpeg to system PATH
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Step 3: Install Python Dependencies
Navigate to your project directory and run:
```bash
pip install -r requirements.txt
```

This installs:
- `yt-dlp`: YouTube downloading engine
- `customtkinter`: Modern UI framework
- `pillow`: Image processing
- `requests`: HTTP requests for metadata

## 3. Running the Application

### Option 1: Direct Python Execution
```bash
python main.py
```

### Option 2: On Windows (Double-click)
Create a file named `launch.bat` in your project directory:
```batch
@echo off
python main.py
pause
```
Then double-click `launch.bat` to run the application.

### Option 3: Create Python Shortcut (Windows)
Create a `.vbs` file named `run_app.vbs`:
```vbs
CreateObject("WScript.Shell").Run("python main.py"), 0
```
Double-click to run without console window.

## 4. Project Structure

```
youtube-video-indir/
├── main.py                 # Entry point
├── ui.py                   # CustomTkinter GUI
├── download_manager.py     # Backend download logic
├── config.py               # Configuration and constants
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── obfuscation_guide.md   # Code protection guide
```

## 5. Usage Instructions

### Basic Download
1. **Paste URL**: Enter a YouTube URL in the input field
2. **Fetch Info**: Click "Fetch Video Info" to load video details
3. **Select Quality**: Choose video quality (360p - 4K)
4. **Download**: Click "Download Video"

### Audio Extraction
1. Select desired audio quality (128-320 kbps)
2. Click "Download Audio (MP3)"
3. File saved to: `~/Downloads/nginsec_downloads/music/`

### Metadata Download
- Automatically downloads when checkbox is enabled:
  - Video description (description.txt)
  - Thumbnail image
  - Video metadata (metadata.json)
- Saved to: `~/Downloads/nginsec_downloads/metadata/`

## 6. Output Directories

After first run, the following directories are created:

```
~/Downloads/nginsec_downloads/
├── videos/       # Downloaded videos
├── music/        # Downloaded audio (MP3)
├── metadata/     # Video metadata, descriptions, thumbnails
└── .temp/        # Temporary processing files
```

## 7. Troubleshooting

### Issue: "yt-dlp not found"
**Solution**: Reinstall dependencies
```bash
pip install --upgrade yt-dlp
```

### Issue: "FFmpeg not found"
**Solution**:
- Command line test: `ffmpeg -version`
- If not found, reinstall FFmpeg and add to PATH
- Windows: Restart computer after installing FFmpeg

### Issue: "CustomTkinter import error"
**Solution**:
```bash
pip install --upgrade customtkinter
```

### Issue: Downloads are very slow
**Solution**:
- Check your internet connection
- Close other bandwidth-heavy applications
- Try downloading with lower quality

### Issue: Video/audio format errors
**Solution**:
- Ensure FFmpeg is properly installed
- The video format might not be supported by yt-dlp
- Try with a different YouTube video

## 8. Performance Tips

1. **Disable metadata download** if you only need videos (faster)
2. **Use lower qualities** (360p, 480p) for faster downloads
3. **Close unnecessary programs** to free up system resources
4. **Check internet speed**: Download speed = available bandwidth

## 9. Important Notes

### Legal Considerations
- Only download content you have permission to download
- Respect copyright and fair use laws in your jurisdiction
- Do not download copyrighted content for redistribution
- Some YouTube content may have regional restrictions

### Privacy
- This application does not collect or transmit any user data
- All downloads are stored locally on your computer
- No tracking or analytics

### Video Quality Info
- **360p**: ~50-100 MB per hour
- **720p**: ~300-500 MB per hour
- **1080p**: ~800-1200 MB per hour
- **4K**: ~2-4 GB per hour

## 10. Advanced Configuration

Edit `config.py` to customize:

```python
# Change default output directory
OUTPUT_DIR = Path("/custom/path/here")

# Modify color scheme
COLORS = {
    "accent": "#00ff00",  # Change neon green
    "primary_bg": "#0f0f0f",  # Background color
    # ... other colors
}

# Adjust window size
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
```

## 11. Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify FFmpeg installation
3. Try with a different YouTube URL
4. Ensure Python and all packages are updated

---

**Powered by nginsec**
Version 1.0.0
