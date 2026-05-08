#!/usr/bin/env python3
"""
nginsec YouTube Video Suite - Main Entry Point
Professional YouTube video/audio downloader with modern UI
"""
import sys
import os
from pathlib import Path

# Ensure we're in the correct directory
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ui import NginsecApp
except ImportError as e:
    print(f"Error: Missing required module. {str(e)}")
    print("\nPlease install dependencies first:")
    print("  pip install -r requirements.txt")
    print("\nMake sure you have FFmpeg installed:")
    print("  Windows: choco install ffmpeg")
    print("  macOS: brew install ffmpeg")
    print("  Linux: sudo apt-get install ffmpeg")
    sys.exit(1)


def main():
    """Main application entry point"""
    try:
        app = NginsecApp()
        app.mainloop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
