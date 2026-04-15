#!/bin/sh
# TOOLLAMA Alpine Linux Installer
# Minimal, pure sh (POSIX) - works with Alpine's musl libc

set -e

# Colors (basic ANSI)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}🚀 TOOLLAMA ALPINE INSTALLER${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

REPO="https://github.com/Kelushael/TOOLLAMA.git"
INSTALL_DIR="${1:-.}"

echo "${BLUE}Repository:${NC} $REPO"
echo "${BLUE}Install directory:${NC} $INSTALL_DIR"
echo ""

# Step 1: Update and install base packages
echo "${YELLOW}1️⃣  Installing Alpine packages...${NC}"
echo "  (requires root or sudo)"

# Core packages - Alpine minimal
apk update
apk add --no-cache \
    git \
    tmux \
    python3 \
    py3-pip \
    bash \
    curl \
    ca-certificates

# Optional: for better compatibility
apk add --no-cache gcompat 2>/dev/null || true

echo "${GREEN}✓${NC} Alpine packages installed"
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

pip3 install --no-cache-dir -q -r requirements.txt 2>/dev/null || {
    echo "${YELLOW}⚠${NC}  Some packages may not install on Alpine (musl)"
    echo "     Running: pip3 install -r requirements.txt"
    pip3 install -r requirements.txt || true
}

echo "${GREEN}✓${NC} Python packages installed"
echo ""

# Step 4: Make scripts executable
echo "${YELLOW}4️⃣  Setting up scripts...${NC}"

chmod +x launch-ollama-tmux tool_executor.py validate_system.sh 2>/dev/null || true

echo "${GREEN}✓${NC} Scripts made executable"
echo ""

# Step 5: Check Ollama
echo "${YELLOW}5️⃣  Checking Ollama...${NC}"

if ! command -v ollama >/dev/null 2>&1; then
    echo "${YELLOW}⚠${NC}  Ollama not found"
    echo "     Install from: https://ollama.com"
    echo "     Or build for Alpine: https://github.com/jmorganca/ollama/wiki/Docker"
else
    OLLAMA_VER=$(ollama --version 2>/dev/null || echo "Ollama installed")
    echo "${GREEN}✓${NC} $OLLAMA_VER"
fi

echo ""

# Summary
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${GREEN}✅ TOOLLAMA INSTALLED FOR ALPINE${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📁 Location: $(pwd)"
echo ""
echo "${YELLOW}🚀 Quick Start:${NC}"
echo "   ./launch-ollama-tmux qwen:7b"
echo ""
echo "${YELLOW}Alpine Notes:${NC}"
echo "   • Uses musl libc (some Python packages may need compilation)"
echo "   • Ollama may need to be built from source"
echo "   • Try Docker image: ollama/ollama:latest"
echo ""
echo "${YELLOW}Docker Alternative:${NC}"
echo "   docker run -it -v /root/ollama-mcp-hub:/app ollama/ollama:latest"
echo ""
echo "${GREEN}✨ Ready!${NC}"
echo ""
