<div align="center">

<img src="https://img.shields.io/badge/nginsec-Video%20Cloud%20Suite-06b6d4?style=for-the-badge&labelColor=0a0e1a" />

# nginsec Video Cloud Suite

### Professional YouTube Downloader · Desktop & Web Edition

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Latest-FF0000?style=flat-square&logo=youtube&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?style=flat-square&logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Version](https://img.shields.io/badge/Version-1.0.0-brightgreen?style=flat-square)

</div>

---

## 🇹🇷 Kurulum (Türkçe) · 🇬🇧 Setup (English) → [aşağıda / below](#-kurulum--setup)

---

## Özellikler / Features

| Özellik / Feature | Desktop | Web |
|---|:---:|:---:|
| 4K / 1080p / 720p video indirme | ✓ | ✓ |
| MP3 320 kbps ses çıkarma | ✓ | ✓ |
| Gerçek zamanlı ilerleme çubuğu | ✓ | ✓ (Socket.io) |
| Şifreli erişim (Access Key) | — | ✓ |
| Ngrok ile paylaşım | — | ✓ |
| Thumbnail + metadata indirme | ✓ | — |
| Karanlık tema arayüz | ✓ | ✓ |

---

## Proje Yapısı / Project Structure

```
nginsec-video-suite/
│
├── main.py                 # Desktop başlangıç noktası / entry point
├── ui.py                   # CustomTkinter GUI
├── download_manager.py     # yt-dlp motoru / engine
├── config.py               # Ayarlar / configuration
├── requirements.txt        # Desktop bağımlılıkları / dependencies
│
├── setup.bat               # Windows kurulum scripti / setup script
├── setup.sh                # macOS/Linux kurulum scripti / setup script
│
└── web/                    # Web Sürümü / Web Edition
    ├── app.py              # Flask + Socket.io backend
    ├── requirements.txt    # Web bağımlılıkları / dependencies
    └── templates/
        └── index.html      # Dark-theme SPA frontend
```

---

## 🚀 Kurulum / Setup

### ⚡ Tek Komutla Otomatik Kurulum / One-Command Auto Setup

> **Windows** — Sadece çift tıkla / Just double-click:
> ```
> setup.bat
> ```

> **macOS / Linux** — Terminalde çalıştır / Run in terminal:
> ```bash
> chmod +x setup.sh && ./setup.sh
> ```

Script şunları otomatik yapar / The script automatically:
- ✅ Python sürümünü kontrol eder / Checks Python version
- ✅ Sanal ortam (`.venv`) oluşturur / Creates virtual environment
- ✅ Tüm bağımlılıkları kurar / Installs all dependencies
- ✅ FFmpeg'i kurar (yoksa) / Installs FFmpeg (if missing)
- ✅ Başlatma komutlarını gösterir / Shows start commands

---

### 📋 Manuel Kurulum / Manual Setup

**Gereksinimler / Requirements:**
- Python 3.8 veya üstü / Python 3.8 or higher → [python.org](https://www.python.org/downloads/)
- FFmpeg → `winget install Gyan.FFmpeg` (Windows) · `brew install ffmpeg` (Mac) · `sudo apt install ffmpeg` (Linux)
- Git → [git-scm.com](https://git-scm.com)

```bash
# 1. Repoyu klonla / Clone the repo
git clone https://github.com/nginsec/nginsec-video-suite.git
cd nginsec-video-suite

# 2. Sanal ortam oluştur / Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Bağımlılıkları kur / Install dependencies
pip install -r requirements.txt          # Desktop
pip install -r web/requirements.txt      # Web Edition
```

---

## ▶️ Kullanım / Usage

### Masa Üstü Uygulaması / Desktop App

```bash
# Sanal ortamı etkinleştir / Activate virtual environment
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

python main.py
```

1. YouTube URL'sini yapıştır / Paste the YouTube URL
2. **"Fetch Video Info"** butonuna tıkla / Click **"Fetch Video Info"**
3. Kalite seç / Select quality (4K, 1080p, 720p… veya MP3)
4. **"Download Video"** veya **"Download Audio (MP3)"** tıkla
5. Dosyalar şuraya kaydedilir / Files saved to: `~/Downloads/nginsec_downloads/`

---

### Web Uygulaması / Web App

```bash
# Sanal ortamı etkinleştir / Activate virtual environment
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

cd web
python app.py
```

Tarayıcıda aç / Open browser: **http://localhost:5000**

**Varsayılan şifre / Default password:** `nginsec2024`

> Şifreyi değiştirmek için / To change the password:
> ```bash
> # Başlatırken / At startup:
> ACCESS_KEY=yeni_sifre python app.py      # macOS/Linux
> $env:ACCESS_KEY="yeni_sifre"; python app.py   # Windows PowerShell
> ```

---

### 🌐 Ngrok ile Paylaşım / Share via Ngrok

Arkadaşınla paylaşmak için / To share with your friend:

```bash
# 1. Web uygulamasını başlat / Start the web app
python web/app.py

# 2. Yeni bir terminal aç ve Ngrok'u çalıştır / Open new terminal and run Ngrok
ngrok http 5000
```

Ngrok çıktısındaki `https://xxxx.ngrok.io` linkini paylaş.  
Share the `https://xxxx.ngrok.io` link from the Ngrok output.

> Arkadaşın bu linke girdiğinde şifreyi isteyecek.  
> Your friend will be prompted for the access key when visiting the link.

---

## ⚙️ Yapılandırma / Configuration

### Masa Üstü — `config.py`

```python
# Çıktı klasörleri / Output directories
OUTPUT_DIR    = Path.home() / "Downloads" / "nginsec_downloads"
DOWNLOADS_DIR = OUTPUT_DIR / "videos"
MUSIC_DIR     = OUTPUT_DIR / "music"

# Pencere boyutu / Window size
WINDOW_WIDTH  = 1200
WINDOW_HEIGHT = 750
```

### Web — Ortam değişkenleri / Environment variables

| Değişken / Variable | Varsayılan / Default | Açıklama / Description |
|---|---|---|
| `ACCESS_KEY` | `nginsec2024` | Web arayüz şifresi / UI password |
| `SECRET_KEY` | *(dahili / internal)* | Flask session şifresi |

---

## 🛠️ Sorun Giderme / Troubleshooting

| Hata / Error | Neden / Cause | Çözüm / Fix |
|---|---|---|
| `ffmpeg is not installed` | FFmpeg yok / missing | `winget install Gyan.FFmpeg` |
| `No module named 'yt_dlp'` | Bağımlılık eksik | `pip install -r requirements.txt` |
| `No module named 'customtkinter'` | Bağımlılık eksik | `pip install customtkinter` |
| `Unauthorized` (web) | Yanlış şifre / Wrong key | `ACCESS_KEY` env değişkenini kontrol et |
| İndirme çok yavaş / Slow download | Normal — büyük dosya | Bekle veya düşük kalite seç (1080p) |
| `Error: requested merging but ffmpeg not installed` | FFmpeg PATH'te yok | Terminali yeniden başlat, FFmpeg'i yeniden kur |

---

## ⚖️ Yasal Uyarı / Legal Notice

Bu araç yalnızca **kişisel ve eğitim amaçlıdır**.  
This tool is for **personal and educational use only**.

Telif hakkı yasalarına ve YouTube Hizmet Şartlarına saygı gösterin.  
Respect copyright laws and YouTube's Terms of Service.

---

## 📝 Lisans / License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built & maintained by**

[![nginsec](https://img.shields.io/badge/github-nginsec-06b6d4?style=for-the-badge&logo=github)](https://github.com/nginsec/nginsec-video-suite)

*nginsec Video Cloud Suite · Secure Video Retrieval System*

</div>
