#!/usr/bin/env bash
# nginsec Video Cloud Suite - Kurulum / Setup (macOS / Linux)

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${CYAN} ============================================================${NC}"
echo -e "${CYAN}  nginsec Video Cloud Suite - Kurulum / Setup${NC}"
echo -e "${CYAN} ============================================================${NC}"
echo ""
echo " [TR] Bu script gerekli tum bagimliliklari otomatik kurar."
echo " [EN] This script automatically installs all dependencies."
echo ""

# ── Python check ─────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo -e "${RED} [HATA/ERROR] Python3 bulunamadi! / Python3 not found!${NC}"
    echo " macOS: brew install python3"
    echo " Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
PYVER=$(python3 --version)
echo -e "${GREEN} [OK] $PYVER bulundu / found${NC}"

# ── Virtual environment ───────────────────────────────────────────────────────
echo ""
echo " [TR] Sanal ortam olusturuluyor..."
echo " [EN] Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN} [OK] .venv olusturuldu / created${NC}"
else
    echo -e "${GREEN} [OK] .venv zaten mevcut / already exists${NC}"
fi

source .venv/bin/activate

# ── Dependencies ──────────────────────────────────────────────────────────────
echo ""
echo " [TR] Python kutuphaneleri kuruluyor..."
echo " [EN] Installing Python packages..."
pip install -r requirements.txt --quiet
echo -e "${GREEN} [OK] Masa ustu bagimliliklar / Desktop dependencies installed${NC}"

pip install -r web/requirements.txt --quiet
echo -e "${GREEN} [OK] Web bagimliliklar / Web dependencies installed${NC}"

# ── FFmpeg ────────────────────────────────────────────────────────────────────
echo ""
echo " [TR] FFmpeg kontrol ediliyor..."
echo " [EN] Checking FFmpeg..."
if ! command -v ffmpeg &>/dev/null; then
    echo -e "${YELLOW} [!!] FFmpeg bulunamadi / not found. Kuruluyor / Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ffmpeg
    else
        echo -e "${RED} [HATA/ERROR] Lutfen ffmpeg'i manuel kurun / Please install ffmpeg manually${NC}"
        echo " https://ffmpeg.org/download.html"
    fi
else
    FF_VER=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
    echo -e "${GREEN} [OK] FFmpeg $FF_VER bulundu / found${NC}"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN} ============================================================${NC}"
echo -e "${GREEN}  [TR] KURULUM TAMAMLANDI! / [EN] SETUP COMPLETE!${NC}"
echo -e "${CYAN} ============================================================${NC}"
echo ""
echo " [TR] Uygulamayi baslatmak icin:"
echo " [EN] To start the application:"
echo ""
echo "   Masa Ustu / Desktop App:"
echo "     source .venv/bin/activate"
echo "     python main.py"
echo ""
echo "   Web Uygulamasi / Web App:"
echo "     source .venv/bin/activate"
echo "     cd web && python app.py"
echo "     Tarayicida / Open browser: http://localhost:5000"
echo "     Varsayilan sifre / Default password: nginsec2024"
echo ""
echo "   Ngrok ile paylas / Share via Ngrok:"
echo "     ngrok http 5000"
echo ""
echo -e "${CYAN} ============================================================${NC}"
echo ""
