#!/bin/bash
set -e

echo "🔍 VALIDATING OLLAMA TMUX TOOL EXECUTION SYSTEM"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

test_component() {
    local name=$1
    local cmd=$2
    echo -n "Testing $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((passed++))
    else
        echo -e "${RED}✗${NC}"
        ((failed++))
    fi
}

# 1. System dependencies
echo "1. System Dependencies"
echo "─────────────────────"
test_component "Ollama installed" "which ollama"
test_component "Ollama version" "ollama --version"
test_component "tmux installed" "which tmux"
test_component "Python3 installed" "python3 --version"
test_component "Python asyncio" "python3 -c 'import asyncio'"
echo ""

# 2. Script validity
echo "2. Script Validity"
echo "──────────────────"
test_component "launch-ollama-tmux syntax" "bash -n launch-ollama-tmux"
test_component "tool_executor.py syntax" "python3 -m py_compile tool_executor.py"
test_component "test_tool_executor.py syntax" "python3 -m py_compile test_tool_executor.py"
echo ""

# 3. Python imports
echo "3. Python Dependencies"
echo "──────────────────────"
test_component "OllamaMCPHub module" "python3 -c 'from ollama_mcp_hub import OllamaMCPHub'"
test_component "Tool parsing logic" "python3 -c 'import re, json'"
test_component "asyncio support" "python3 -c 'import asyncio; import sys; sys.path.insert(0, \".\"); from ollama_mcp_hub import OllamaMCPHub'"
echo ""

# 4. Ollama models
echo "4. Available Models"
echo "───────────────────"
MODELS=$(ollama list 2>/dev/null | grep -v NAME | wc -l)
if [ "$MODELS" -gt 0 ]; then
    echo "✓ Found $MODELS model(s):"
    ollama list 2>/dev/null | grep -v NAME | awk '{print "  - " $1}' | head -5
    ((passed++))
else
    echo "✗ No models found"
    ((failed++))
fi
echo ""

# 5. File structure
echo "5. Project Files"
echo "────────────────"
test_component "launch-ollama-tmux exists" "test -f launch-ollama-tmux"
test_component "tool_executor.py exists" "test -f tool_executor.py"
test_component "ollama_mcp_hub.py exists" "test -f ollama_mcp_hub.py"
test_component "test_tool_executor.py exists" "test -f test_tool_executor.py"
echo ""

# 6. Tool executor unit tests
echo "6. Unit Tests"
echo "─────────────"
if python3 test_tool_executor.py 2>&1 | grep -q "ALL TESTS PASSED"; then
    echo -e "${GREEN}✓${NC} Tool executor tests passed"
    ((passed++))
else
    echo -e "${RED}✗${NC} Tool executor tests failed"
    ((failed++))
fi
echo ""

# 7. Integration readiness
echo "7. Integration Readiness"
echo "────────────────────────"

# Check if we can create a test tmux session
TEST_SESSION="test-ollama-$$"
if tmux new-session -d -s "$TEST_SESSION" -c "$(pwd)" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Can create tmux session"
    ((passed++))

    # Try to send a command to the session
    if tmux send-keys -t "$TEST_SESSION" "echo test" Enter 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Can send commands to tmux panes"
        ((passed++))
    else
        echo -e "${RED}✗${NC} Cannot send commands to tmux"
        ((failed++))
    fi

    # Try to capture pane output
    if tmux capture-pane -t "$TEST_SESSION" -p 2>/dev/null | grep -q "test"; then
        echo -e "${GREEN}✓${NC} Can capture pane output"
        ((passed++))
    else
        echo -e "${RED}✗${NC} Cannot capture pane output"
        ((failed++))
    fi

    # Cleanup
    tmux kill-session -t "$TEST_SESSION" 2>/dev/null
else
    echo -e "${RED}✗${NC} Cannot create tmux session"
    ((failed+=3))
fi
echo ""

# 8. Permissions
echo "8. File Permissions"
echo "───────────────────"
test_component "launch-ollama-tmux executable" "test -x launch-ollama-tmux"
test_component "tool_executor.py executable" "test -x tool_executor.py"
echo ""

# Summary
echo "=================================================="
echo "VALIDATION SUMMARY"
echo "=================================================="
TOTAL=$((passed + failed))
echo -e "Total: ${TOTAL} checks"
echo -e "${GREEN}Passed: ${passed}${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed: ${failed}${NC}"
else
    echo -e "${GREEN}Failed: 0${NC}"
fi
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ SYSTEM VALIDATION PASSED${NC}"
    echo ""
    echo "Ready to launch! Try:"
    echo "  ./launch-ollama-tmux gemma4:e4b"
    echo ""
    echo "Or with another model:"
    ollama list 2>/dev/null | grep -v NAME | head -3 | awk '{print "  ./launch-ollama-tmux " $1}'
    exit 0
else
    echo -e "${RED}❌ SYSTEM VALIDATION FAILED${NC}"
    echo "Please fix the issues above"
    exit 1
fi
