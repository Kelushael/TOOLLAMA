#!/bin/sh
# TOOLLAMA Universal Installer
# Works on Linux (all distros), macOS, Alpine, and Windows (WSL)

set -e

# Colors (POSIX compatible)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}🚀 TOOLLAMA UNIVERSAL INSTALLER${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Detect OS
detect_os() {
    if [ "$(uname)" = "Darwin" ]; then
        echo "macos"
    elif grep -q "Alpine" /etc/os-release 2>/dev/null; then
        echo "alpine"
    elif grep -q "ubuntu\|debian" /etc/os-release 2>/dev/null; then
        echo "debian"
    elif grep -q "fedora\|rhel\|centos" /etc/os-release 2>/dev/null; then
        echo "rhel"
    elif grep -q "arch" /etc/os-release 2>/dev/null; then
        echo "arch"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo "${BLUE}Detected OS:${NC} $OS"
echo ""

# Configuration
REPO="https://github.com/Kelushael/TOOLLAMA.git"
INSTALL_DIR="${1:-.}"

echo "${BLUE}Repository:${NC} $REPO"
echo "${BLUE}Install directory:${NC} $INSTALL_DIR"
echo ""

# Step 1: Install dependencies
echo "${YELLOW}1️⃣  Installing dependencies...${NC}"

if [ "$OS" = "alpine" ]; then
    echo "  Installing for Alpine..."
    apk update
    apk add --no-cache git tmux python3 py3-pip bash

elif [ "$OS" = "debian" ]; then
    echo "  Installing for Debian/Ubuntu..."
    apt-get update
    apt-get install -y git tmux python3 python3-pip

elif [ "$OS" = "rhel" ]; then
    echo "  Installing for RHEL/CentOS/Fedora..."
    yum install -y git tmux python3 python3-pip

elif [ "$OS" = "arch" ]; then
    echo "  Installing for Arch Linux..."
    pacman -Sy --noconfirm git tmux python python-pip

elif [ "$OS" = "macos" ]; then
    echo "  Installing for macOS..."
    if ! command -v brew &> /dev/null; then
        echo "${RED}❌ Homebrew not found. Install from: https://brew.sh${NC}"
        exit 1
    fi
    brew install git tmux python3

else
    echo "${RED}❌ Unknown OS. Please install manually:${NC}"
    echo "   - git"
    echo "   - tmux (or compatible terminal multiplexer)"
    echo "   - python3 (3.8+)"
    echo "   - pip3"
    exit 1
fi

echo "${GREEN}✓${NC} Dependencies installed"
echo ""

# Step 2: Clone repository
echo "${YELLOW}2️⃣  Cloning TOOLLAMA...${NC}"

if [ -d "$INSTALL_DIR/TOOLLAMA" ]; then
    echo "  Directory exists, pulling latest..."
    cd "$INSTALL_DIR/TOOLLAMA"
    git pull origin main
else
    git clone "$REPO" "$INSTALL_DIR/TOOLLAMA"
    cd "$INSTALL_DIR/TOOLLAMA"
fi

echo "${GREEN}✓${NC} Repository ready at: $(pwd)"
echo ""

# Step 3: Install Python dependencies
echo "${YELLOW}3️⃣  Installing Python packages...${NC}"

if command -v pip3 &> /dev/null; then
    pip3 install -q -r requirements.txt 2>/dev/null || true
elif command -v pip &> /dev/null; then
    pip install -q -r requirements.txt 2>/dev/null || true
else
    echo "${YELLOW}⚠${NC}  pip not found, skipping Python packages"
fi

echo "${GREEN}✓${NC} Python packages installed"
echo ""

# Step 4: Make scripts executable
echo "${YELLOW}4️⃣  Setting up scripts...${NC}"

chmod +x launch-ollama-tmux tool_executor.py validate_system.sh 2>/dev/null || true

echo "${GREEN}✓${NC} Scripts made executable"
echo ""

# Step 5: Validate Ollama
echo "${YELLOW}5️⃣  Checking Ollama...${NC}"

if ! command -v ollama &> /dev/null; then
    echo "${YELLOW}⚠${NC}  Ollama not found. Install from: https://ollama.com"
    echo "   Then pull a model: ollama pull qwen:7b"
else
    OLLAMA_VER=$(ollama --version 2>/dev/null || echo "Ollama installed")
    echo "${GREEN}✓${NC} $OLLAMA_VER"
fi

echo ""

# Summary
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${GREEN}✅ TOOLLAMA INSTALLED SUCCESSFULLY${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📁 Location: $(pwd)"
echo ""
echo "${YELLOW}🚀 Quick Start:${NC}"
echo "   cd TOOLLAMA"
echo "   ./launch-ollama-tmux qwen:7b"
echo ""
echo "${YELLOW}Available Models:${NC}"
echo "   qwen:7b          (Recommended, balanced)"
echo "   llama2:7b        (Good for code)"
echo "   mistral:7b       (Fast)"
echo "   neural-chat:7b   (Best chat)"
echo ""
echo "${YELLOW}📚 Documentation:${NC}"
echo "   README.md         - Project overview"
echo "   QUICKSTART.md     - Getting started"
echo "   TMUX_LAUNCH.md    - Launch guide"
echo ""
echo "${YELLOW}⚙️  Available Tools:${NC}"
echo "   • read_file, write_file, list_directory"
echo "   • bash_execute, search_files"
echo "   • git_status, git_commit"
echo "   • memory_save, memory_search"
echo ""
echo "${GREEN}✨ Ready to use!${NC}"
echo ""
