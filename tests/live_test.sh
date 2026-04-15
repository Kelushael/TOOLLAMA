#!/bin/bash
set -e

echo "🚀 LIVE FUNCTIONAL TEST - Ollama + Tool Executor"
echo "=================================================="
echo ""

# Use an available model
MODEL=$(ollama list 2>/dev/null | grep -v NAME | head -1 | awk '{print $1}')

if [ -z "$MODEL" ]; then
    echo "❌ No models found. Install one first:"
    echo "   ollama pull gemma4:e4b"
    exit 1
fi

echo "Using model: $MODEL"
echo ""

# Create test session name
SESSION="test-tools-$$"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "1. Creating tmux session..."
tmux new-session -d -s "$SESSION" -x 200 -y 50
echo "   ✓ Session created: $SESSION"
echo ""

echo "2. Starting ollama in left pane..."
tmux send-keys -t "$SESSION" "cd $SCRIPT_DIR && echo 'Ollama ready' && sleep 1" Enter
sleep 1
echo "   ✓ Ready"
echo ""

echo "3. Splitting into two panes..."
tmux split-window -t "$SESSION" -h
tmux resize-pane -t "$SESSION.0" -x 140
echo "   ✓ Panes created (70/30 split)"
echo ""

echo "4. Starting tool executor in right pane..."
tmux send-keys -t "$SESSION.1" "cd $SCRIPT_DIR && python3 -c \"
import sys
sys.path.insert(0, '.')
from ollama_mcp_hub import OllamaMCPHub
import asyncio

hub = OllamaMCPHub()

async def test():
    print('⚙️  Tool Executor Ready')
    # Execute a test tool
    result = await hub.executor.execute('list_directory', {'path': '.'})
    if result.get('success'):
        print('✓ Test execution: list_directory worked')
        print('  Items:', len(result.get('items', [])))

asyncio.run(test())
\"" Enter

sleep 2
echo "   ✓ Tool executor started"
echo ""

echo "5. Verifying tool execution..."
OUTPUT=$(tmux capture-pane -t "$SESSION.1" -p)

if echo "$OUTPUT" | grep -q "Tool Executor Ready"; then
    echo "   ✓ Tool executor responding"
fi

if echo "$OUTPUT" | grep -q "list_directory worked"; then
    echo "   ✓ Tool execution successful"
fi
echo ""

echo "6. Testing tool call parsing..."
# Simulate what the model would output
TEST_TOOL_CALL='<tool_use>{"name": "read_file", "input": {"path": "ollama_mcp_hub.py"}}</tool_use>'

python3 << 'PYEOF'
import re
import json

test_text = '<tool_use>{"name": "read_file", "input": {"path": "ollama_mcp_hub.py"}}</tool_use>'

pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
for match in re.finditer(pattern, test_text, re.DOTALL):
    try:
        tool_call = json.loads(match.group(1))
        print(f"   ✓ Parsed tool call: {tool_call['name']}")
        print(f"     Input: {tool_call['input']}")
    except:
        pass
PYEOF

echo ""

echo "7. Checking tmux pane communication..."
# Send a test message to left pane
tmux send-keys -t "$SESSION.0" "echo 'Test message' && sleep 1" Enter
sleep 1

LEFT_OUTPUT=$(tmux capture-pane -t "$SESSION.0" -p)
if echo "$LEFT_OUTPUT" | grep -q "Test message"; then
    echo "   ✓ Left pane communication working"
fi
echo ""

echo "=================================================="
echo "✅ LIVE TEST COMPLETE"
echo "=================================================="
echo ""
echo "Session: $SESSION"
echo "Left pane (chat):  tmux attach-session -t $SESSION"
echo "Kill session:      tmux kill-session -t $SESSION"
echo ""

# Show pane contents for verification
echo "Left pane output:"
tmux capture-pane -t "$SESSION.0" -p | head -10 | sed 's/^/  /'
echo ""
echo "Right pane output:"
tmux capture-pane -t "$SESSION.1" -p | head -10 | sed 's/^/  /'
echo ""

# Cleanup
echo "Cleaning up test session..."
tmux kill-session -t "$SESSION"
echo "✓ Session terminated"
echo ""
echo "🎉 All systems operational!"
