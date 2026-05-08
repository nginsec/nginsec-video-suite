@echo off
chcp 65001 >nul
title nginsec Video Cloud Suite - Kurulum / Setup

echo.
echo  ============================================================
echo   nginsec Video Cloud Suite - Kurulum / Setup
echo  ============================================================
echo.
echo  [TR] Bu script gerekli tum bagimliliklari otomatik kurar.
echo  [EN] This script automatically installs all dependencies.
echo.
pause

:: ── Python kontrolü / Python check ──────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [TR] HATA: Python bulunamadi! Lutfen python.org adresinden Python 3.8+ kurun.
    echo  [EN] ERROR: Python not found! Please install Python 3.8+ from python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% bulundu / found

:: ── Sanal ortam / Virtual environment ────────────────────────────────────────
echo.
echo  [TR] Sanal ortam olusturuluyor...
echo  [EN] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo  [OK] .venv olusturuldu / created
) else (
    echo  [OK] .venv zaten mevcut / already exists
)

:: ── Bağımlılıklar / Dependencies ─────────────────────────────────────────────
echo.
echo  [TR] Python kutuphaneleri kuruluyor (bu 1-2 dakika surabilir)...
echo  [EN] Installing Python packages (this may take 1-2 minutes)...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo  [OK] Masa ustu bagimliliklar / Desktop dependencies installed

pip install -r web\requirements.txt --quiet
echo  [OK] Web bagimliliklar / Web dependencies installed

:: ── FFmpeg kontrolü / FFmpeg check ──────────────────────────────────────────
echo.
echo  [TR] FFmpeg kontrol ediliyor...
echo  [EN] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!!] FFmpeg bulunamadi. Winget ile kuruluyor / FFmpeg not found. Installing via winget...
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo  [TR] Winget ile kurulamadi. Manuel kurun: https://ffmpeg.org/download.html
        echo  [EN] Could not install via winget. Install manually: https://ffmpeg.org/download.html
    ) else (
        echo  [OK] FFmpeg kuruldu / installed
    )
) else (
    for /f "tokens=3" %%v in ('ffmpeg -version 2^>^&1 ^| findstr "version"') do (
        echo  [OK] FFmpeg %%v bulundu / found
        goto :ffmpeg_done
    )
    :ffmpeg_done
)

:: ── Özet / Summary ───────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   [TR] KURULUM TAMAMLANDI!
echo   [EN] SETUP COMPLETE!
echo  ============================================================
echo.
echo  [TR] Uygulamayi baslatmak icin:
echo  [EN] To start the application:
echo.
echo    Masa Ustu Uygulamasi / Desktop App:
echo      python main.py
echo.
echo    Web Uygulamasi / Web App:
echo      cd web
echo      python app.py
echo      Tarayicida ac / Open browser: http://localhost:5000
echo      Varsayilan sifre / Default password: nginsec2024
echo.
echo    Ngrok ile paylas / Share via Ngrok:
echo      ngrok http 5000
echo.
echo  ============================================================
echo.
pause
