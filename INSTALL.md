# 📦 TOOLLAMA Installation Guide

Choose your operating system below to get started.

---

## 🐧 Linux (All Distributions)

### Ubuntu / Debian
```bash
curl -fsSL https://raw.githubusercontent.com/Kelushael/TOOLLAMA/main/install.sh | sh
```

Or manually:
```bash
git clone https://github.com/Kelushael/TOOLLAMA.git
cd TOOLLAMA
chmod +x install.sh
./install.sh
```

### Alpine Linux
Alpine uses musl instead of glibc. Use the Alpine-specific installer:

```bash
wget https://raw.githubusercontent.com/Kelushael/TOOLLAMA/main/install-alpine.sh
chmod +x install-alpine.sh
./install-alpine.sh
```

Or with curl:
```bash
curl -fsSL https://raw.githubusercontent.com/Kelushael/TOOLLAMA/main/install-alpine.sh | sh
```

### Red Hat / CentOS / Fedora
```bash
curl -fsSL https://raw.githubusercontent.com/Kelushael/TOOLLAMA/main/install.sh | sh
```

### Arch Linux
```bash
curl -fsSL https://raw.githubusercontent.com/Kelushael/TOOLLAMA/main/install.sh | sh
```

---

## 🍎 macOS

### Using Homebrew
```bash
# Install dependencies first (if needed)
brew install git tmux python3

# Then clone and run installer
git clone https://github.com/Kelushael/TOOLLAMA.git
cd TOOLLAMA
chmod +x install.sh
./install.sh
```

---

## 🪟 Windows

### Option 1: PowerShell (Recommended)
```powershell
# Clone repository
git clone https://github.com/Kelushael/TOOLLAMA.git
cd TOOLLAMA

# Run PowerShell installer
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Option 2: WSL2 (Full Feature Support)
1. Install WSL2: https://learn.microsoft.com/en-us/windows/wsl/install
2. Open WSL terminal
3. Run Linux installer:
```bash
git clone https://github.com/Kelushael/TOOLLAMA.git
cd TOOLLAMA
chmod +x install.sh
./install.sh
```

### Option 3: Git Bash
Use the Linux installer under Git Bash:
```bash
git clone https://github.com/Kelushael/TOOLLAMA.git
cd TOOLLAMA
chmod +x install.sh
bash install.sh
```

---

## 🐳 Docker

### Run in Docker (Any OS)
```bash
# Build image
docker build -t toollama:latest .

# Run container
docker run -it -v /path/to/ollama:/ollama toollama:latest

# Inside container
./launch-ollama-tmux qwen:7b
```

### Alpine Docker
```bash
docker run -it --rm \
  -v /root/ollama-mcp-hub:/app \
  -w /app \
  alpine:latest \
  sh install-alpine.sh
```

---

## ✅ What Each Installer Does

### `install.sh` (Universal Linux/macOS)
- ✅ Auto-detects OS (Debian, Alpine, RHEL, Arch, macOS)
- ✅ Installs dependencies (git, tmux, python3)
- ✅ Clones TOOLLAMA repository
- ✅ Installs Python packages
- ✅ Validates system setup
- ✅ Shows quick start instructions

**Works on:**
- Ubuntu, Debian, Mint
- RHEL, CentOS, Fedora
- Arch, Manjaro
- macOS (with Homebrew)
- Most Linux distributions

### `install-alpine.sh` (Alpine-Specific)
- ✅ Optimized for Alpine Linux (musl libc)
- ✅ Minimal dependencies
- ✅ Pure POSIX sh (no bash required)
- ✅ Handles Alpine's package manager (apk)
- ⚠️ Notes about Python compilation needs

**Works on:**
- Alpine Linux
- Alpine Docker images
- Minimal container images

### `install.ps1` (Windows PowerShell)
- ✅ Checks prerequisites (Git, WSL, Ollama)
- ✅ Clones repository to Windows
- ✅ Installs Python dependencies (if available)
- ✅ Provides WSL integration instructions

**Works on:**
- Windows 10/11 (with PowerShell 5.0+)
- Can integrate with WSL2
- Git for Windows required

---

## 📋 Prerequisites

### Minimum Requirements
- **Git** - for cloning repository
- **Python 3.8+** - for tool execution
- **tmux** - for split-pane interface

### Optional but Recommended
- **Ollama** - for running LLMs locally (https://ollama.com)
- **bash** - for better script compatibility (Alpine provides it)

### For Windows
- **WSL2** - for full Linux support
- **Git for Windows** - for git commands
- **Ollama for Windows** - to run models

---

## 🚀 After Installation

### Quick Start
```bash
cd TOOLLAMA
./launch-ollama-tmux qwen:7b
```

### Choose Your Model
```bash
./launch-ollama-tmux qwen:7b          # Balanced, recommended
./launch-ollama-tmux llama2:7b        # Good for code
./launch-ollama-tmux mistral:7b       # Fast
./launch-ollama-tmux neural-chat:7b   # Best chat
```

### Using TOOLLAMA
Once launched, the interface splits into:
- **Left pane (70%):** Chat with model
- **Right pane (30%):** Tool execution

The model automatically gets access to:
- `read_file`, `write_file`, `list_directory`
- `bash_execute`, `search_files`
- `git_status`, `git_commit`
- `memory_save`, `memory_search`

---

## 🐛 Troubleshooting

### "tmux: command not found"
Install tmux for your system:
```bash
# Ubuntu/Debian
sudo apt install tmux

# Alpine
apk add tmux

# macOS
brew install tmux

# Red Hat/Fedora
sudo yum install tmux
```

### "ollama: command not found"
Install Ollama from https://ollama.com, then pull a model:
```bash
ollama pull qwen:7b
```

### "Python packages failed to install" (Alpine)
Alpine uses musl libc. Some Python packages need compilation:
```bash
# Install build tools
apk add build-base python3-dev

# Retry install
pip3 install -r requirements.txt
```

### "Permission denied" on scripts
Make scripts executable:
```bash
chmod +x install.sh install-alpine.sh launch-ollama-tmux tool_executor.py
```

### Windows: "Running scripts is disabled"
In PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📚 Documentation

- **README.md** - Project overview and features
- **QUICKSTART.md** - 5-minute quick start guide
- **ARCHITECTURE.md** - How it works under the hood
- **TMUX_LAUNCH.md** - Detailed launch guide
- **SYSTEM_VALIDATION.md** - Test results and validation

---

## 🆘 Need Help?

1. Check **README.md** for common questions
2. Review **SYSTEM_VALIDATION.md** for test output
3. Open an issue: https://github.com/Kelushael/TOOLLAMA/issues
4. Check discussions: https://github.com/Kelushael/TOOLLAMA/discussions

---

## ✨ That's it!

You're ready to use TOOLLAMA. Enjoy building with local AI!
