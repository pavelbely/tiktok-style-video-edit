#!/usr/bin/env bash
# Auto-install dependencies for the tiktok-style-video-edit toolkit:
#   ffmpeg (with libx264), a bold sans font, and the Python packages (faster-whisper, Pillow).
# Does NOT install the AI agent or model — see SETUP.md for OpenCode + a Belarus-reachable model.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

say "Detecting OS"
OS="$(uname -s)"

install_linux() {
  if command -v apt-get >/dev/null 2>&1; then
    say "ffmpeg + fonts + pip via apt"
    sudo apt-get update -qq
    sudo apt-get install -y ffmpeg fonts-liberation python3-pip
  elif command -v dnf >/dev/null 2>&1; then
    say "ffmpeg + fonts + pip via dnf"
    sudo dnf install -y ffmpeg liberation-sans-fonts python3-pip
  elif command -v pacman >/dev/null 2>&1; then
    say "ffmpeg + fonts + pip via pacman"
    sudo pacman -Sy --noconfirm ffmpeg ttf-liberation python-pip
  else
    echo "!! Unknown Linux package manager. Install ffmpeg + a bold sans font + pip manually."
  fi
}

install_mac() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "!! Homebrew not found — install it from https://brew.sh then re-run."; exit 1
  fi
  say "ffmpeg via Homebrew (macOS already ships Arial Bold)"
  brew install ffmpeg
}

case "$OS" in
  Linux)  install_linux ;;
  Darwin) install_mac ;;
  *) echo "!! Unsupported OS '$OS'. Install ffmpeg + the Python deps manually." ;;
esac

say "Python packages (faster-whisper, Pillow)"
python3 -m pip install --upgrade pip
python3 -m pip install -r "$HERE/requirements.txt"

say "Verifying"
command -v ffmpeg >/dev/null 2>&1 && ffmpeg -version | head -1 || echo "!! ffmpeg not on PATH"
python3 -c "import faster_whisper, PIL; print('Python deps OK')"

say "Done. Next: see SETUP.md to install OpenCode + a model that works from Belarus (DeepSeek / GLM / Ollama)."
