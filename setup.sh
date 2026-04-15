#!/bin/bash

# Ollama MCP Hub Setup Script
# This script prepares the environment and provides quick start commands

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           OLLAMA MCP HUB - Setup Script                        ║"
echo "║    Local Claude Code with Any Ollama Model                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "✓ Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "  Found Python $PYTHON_VERSION"

# Check Ollama
echo "✓ Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "✗ Ollama not found. Download from https://ollama.com"
    exit 1
fi
echo "  ✓ Ollama installed"

# Create virtual environment
echo "✓ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
else
    echo "  Virtual environment already exists"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "  ✓ Dependencies installed"

# Create data directory
echo "✓ Creating data directory..."
mkdir -p data
echo "  ✓ Data directory ready"

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete!                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Make sure Ollama is running:"
echo "   $ ollama serve"
echo ""
echo "2. In another terminal, pull a model:"
echo "   $ ollama pull qwen:7b"
echo ""
echo "3. Start the MCP server:"
echo "   $ source venv/bin/activate"
echo "   $ python mcp_server.py"
echo ""
echo "4. In yet another terminal, start the agent:"
echo "   $ olcp --mcp-server http://127.0.0.1:8000 --model qwen:7b"
echo ""
echo "5. Start coding! Try:"
echo "   > Create a Python script that prints hello world"
echo ""
echo "For more info, see README.md"
echo ""
