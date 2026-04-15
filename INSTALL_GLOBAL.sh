#!/bin/bash

# Install the Ollama wrapper globally
# After running this, ALL ollama commands will have tools available

echo "Installing Ollama wrapper globally..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "Need sudo. Running with sudo..."
    sudo bash "$0"
    exit $?
fi

# Find the actual ollama binary
ACTUAL_OLLAMA=$(which ollama 2>/dev/null)

if [[ -z "$ACTUAL_OLLAMA" ]]; then
    echo "❌ Ollama not found. Make sure Ollama is installed."
    exit 1
fi

echo "✓ Found Ollama at: $ACTUAL_OLLAMA"

# Backup original
if [[ ! -f "${ACTUAL_OLLAMA}.bak" ]]; then
    cp "$ACTUAL_OLLAMA" "${ACTUAL_OLLAMA}.bak"
    echo "✓ Backed up original to: ${ACTUAL_OLLAMA}.bak"
fi

# Copy wrapper to ollama location
cp "$(dirname "$0")/ollama-wrapper" "$ACTUAL_OLLAMA"
chmod +x "$ACTUAL_OLLAMA"

echo "✓ Installed wrapper"
echo ""
echo "════════════════════════════════════════════════════"
echo "DONE! Now when you run:"
echo ""
echo "  $ ollama run qwen:7b"
echo "  $ ollama run llama2"
echo "  $ ollama run any_model"
echo ""
echo "It will AUTOMATICALLY have ALL TOOLS available!"
echo "════════════════════════════════════════════════════"
echo ""
echo "To restore: sudo cp ${ACTUAL_OLLAMA}.bak $ACTUAL_OLLAMA"
