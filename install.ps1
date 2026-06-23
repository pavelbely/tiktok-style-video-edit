# Auto-install dependencies on Windows: ffmpeg (via winget/choco) + the Python packages
# (faster-whisper, Pillow). Does NOT install the AI agent or model — see SETUP.md.
# Run in PowerShell:   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
function Say($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }

Say "Installing ffmpeg"
if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
} elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    choco install ffmpeg -y
} else {
    Write-Host "!! Neither winget nor choco found. Install ffmpeg from https://ffmpeg.org/download.html and add it to PATH." -ForegroundColor Yellow
}

Say "Installing Python packages (faster-whisper, Pillow)"
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { Write-Host "!! Python not found. Install Python 3.9+ from https://python.org (check 'Add to PATH')." -ForegroundColor Yellow; exit 1 }
& $py.Source -m pip install --upgrade pip
& $py.Source -m pip install -r "$PSScriptRoot\requirements.txt"

Say "Verifying"
try { (ffmpeg -version | Select-Object -First 1) } catch { Write-Host "!! ffmpeg not on PATH yet — open a new terminal." -ForegroundColor Yellow }
& $py.Source -c "import faster_whisper, PIL; print('Python deps OK')"

Say "Done. Windows already ships Arial Bold. Next: see SETUP.md for OpenCode + a model that works from Belarus."
Write-Host "Note: on Windows the scripts run with 'python' (not 'python3')." -ForegroundColor DarkGray
