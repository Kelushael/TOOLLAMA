# TOOLLAMA Windows/PowerShell Installer
# Requires: Git, WSL2, and Ollama installed

param(
    [string]$InstallDir = "."
)

function Write-Step($message) {
    Write-Host "`n$message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "✓ $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "⚠ $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "✗ $message" -ForegroundColor Red
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🚀 TOOLLAMA WINDOWS INSTALLER (PowerShell)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Check prerequisites
Write-Step "1️⃣  Checking prerequisites..."

$gitInstalled = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
if ($gitInstalled) {
    Write-Success "Git found"
} else {
    Write-Error "Git not found. Install from: https://git-scm.com"
    exit 1
}

# Check WSL
$wslInstalled = $null -ne (Get-Command wsl -ErrorAction SilentlyContinue)
if ($wslInstalled) {
    Write-Success "WSL found"
} else {
    Write-Warning "WSL not found. You'll need WSL2 to run the system."
    Write-Host "  Install from: https://learn.microsoft.com/en-us/windows/wsl/install"
}

# Check Ollama
$ollamaInstalled = Test-Path "$env:APPDATA\..\Local\Programs\Ollama\ollama.exe" -ErrorAction SilentlyContinue
if ($ollamaInstalled -or $null -ne (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Success "Ollama found"
} else {
    Write-Warning "Ollama not found"
    Write-Host "  Install from: https://ollama.com"
}

# Clone repository
Write-Step "2️⃣  Cloning TOOLLAMA..."

if (Test-Path "$InstallDir\TOOLLAMA") {
    Write-Host "  Directory exists, pulling latest..."
    Push-Location "$InstallDir\TOOLLAMA"
    git pull origin main
    Pop-Location
} else {
    git clone https://github.com/Kelushael/TOOLLAMA.git "$InstallDir\TOOLLAMA"
}

Write-Success "Repository cloned"

# Check for Python (optional on Windows)
$pythonInstalled = $null -ne (Get-Command python -ErrorAction SilentlyContinue) -or $null -ne (Get-Command python3 -ErrorAction SilentlyContinue)

if ($pythonInstalled) {
    Write-Step "3️⃣  Installing Python dependencies..."
    Push-Location "$InstallDir\TOOLLAMA"
    python -m pip install -q -r requirements.txt 2>$null
    Pop-Location
    Write-Success "Python dependencies installed"
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ TOOLLAMA READY" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host ""
Write-Host "📁 Location: $((Get-Item "$InstallDir\TOOLLAMA").FullName)"

Write-Host ""
Write-Host "🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Open WSL terminal:"
Write-Host "     wsl"
Write-Host ""
Write-Host "  2. Navigate to TOOLLAMA:"
Write-Host "     cd /mnt/c/path/to/TOOLLAMA"
Write-Host ""
Write-Host "  3. Start the system:"
Write-Host "     ./launch-ollama-tmux qwen:7b"
Write-Host ""

Write-Host "📚 DOCUMENTATION:" -ForegroundColor Yellow
Write-Host "  README.md     - Overview"
Write-Host "  QUICKSTART.md - Getting started"
Write-Host "  TMUX_LAUNCH.md - Usage guide"
Write-Host ""

Write-Host "✨ Ready!" -ForegroundColor Green
