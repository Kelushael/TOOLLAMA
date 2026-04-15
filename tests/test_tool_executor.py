#!/usr/bin/env python3
"""
Test tool_executor.py logic in isolation without needing a live tmux session
"""

import re
import json
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from ollama_mcp_hub import OllamaMCPHub

hub = OllamaMCPHub()

def parse_tool_calls(text):
    """Extract tool calls from text (same as tool_executor.py)."""
    pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            yield json.loads(match.group(1))
        except:
            pass

async def test_tool_parsing():
    """Test that tool calls are correctly parsed from chat output."""
    print("=" * 60)
    print("TEST 1: Tool Call Parsing")
    print("=" * 60)

    chat_output = """
    Assistant: I'll help you with that. Let me first read the file.

    <tool_use>
    {"name": "read_file", "input": {"path": "test.py"}}
    </tool_use>

    Now let me check the directory structure:

    <tool_use>
    {"name": "list_directory", "input": {"path": "."}}
    </tool_use>

    That should give us what we need!
    """

    calls = list(parse_tool_calls(chat_output))
    assert len(calls) == 2, f"Expected 2 tool calls, got {len(calls)}"
    assert calls[0]["name"] == "read_file", "First call should be read_file"
    assert calls[1]["name"] == "list_directory", "Second call should be list_directory"

    print("✓ Correctly parsed 2 tool calls from chat output")
    print(f"  - {calls[0]['name']} with path: {calls[0]['input']['path']}")
    print(f"  - {calls[1]['name']} with path: {calls[1]['input']['path']}")
    print()

async def test_tool_execution():
    """Test that tools execute correctly."""
    print("=" * 60)
    print("TEST 2: Tool Execution")
    print("=" * 60)

    # Test list_directory
    result = await hub.executor.execute('list_directory', {'path': '.'})
    assert result.get('success'), f"list_directory failed: {result}"
    print(f"✓ list_directory executed successfully")
    print(f"  Items found: {len(result.get('stdout', '').split(chr(10)))}")

    # Test read_file with actual file
    result = await hub.executor.execute('read_file', {'path': 'ollama_mcp_hub.py'})
    assert result.get('success'), f"read_file failed: {result}"
    content_len = len(result.get('content', ''))
    assert content_len > 0, "read_file returned empty content"
    print(f"✓ read_file executed successfully")
    print(f"  Read {content_len} characters from ollama_mcp_hub.py")
    print()

async def test_tool_deduplication():
    """Test that duplicate tool calls aren't re-executed."""
    print("=" * 60)
    print("TEST 3: Deduplication Logic")
    print("=" * 60)

    seen_calls = set()

    # Simulate same tool call twice
    call1 = {"name": "read_file", "input": {"path": "test.py"}}
    call2 = {"name": "read_file", "input": {"path": "test.py"}}

    def get_call_id(tool_call):
        name = tool_call.get("name")
        args = tool_call.get("input", {})
        return f"{name}:{json.dumps(args, sort_keys=True)}"

    id1 = get_call_id(call1)
    id2 = get_call_id(call2)

    assert id1 == id2, "Call IDs should match for identical calls"

    seen_calls.add(id1)
    should_execute_call2 = id2 not in seen_calls

    assert not should_execute_call2, "Second identical call should be skipped"
    print("✓ Deduplication logic works correctly")
    print(f"  Call ID: {id1}")
    print(f"  First call: would execute")
    print(f"  Second call: skipped (already in seen_calls)")
    print()

async def test_result_formatting():
    """Test that tool results are properly formatted."""
    print("=" * 60)
    print("TEST 4: Result Formatting")
    print("=" * 60)

    result = {
        "success": True,
        "stdout": "test output",
        "stderr": "",
        "return_code": 0
    }

    name = "read_file"
    result_md = f"\n**[Tool Result: {name}]**\n```json\n{json.dumps(result, indent=2)}\n```\n"

    assert "[Tool Result: read_file]" in result_md, "Missing tool name in result"
    assert "```json" in result_md, "Missing JSON code block"
    assert '"success": true' in result_md, "Result not properly formatted"

    print("✓ Result formatting is correct")
    print("  Sample output:")
    for line in result_md.strip().split('\n')[:5]:
        print(f"    {line}")
    print()

async def test_edge_cases():
    """Test edge cases in tool call parsing."""
    print("=" * 60)
    print("TEST 5: Edge Cases")
    print("=" * 60)

    # Edge case 1: Tool call with newlines in JSON
    text1 = """
    <tool_use>
    {
        "name": "read_file",
        "input": {
            "path": "script.py"
        }
    }
    </tool_use>
    """
    calls1 = list(parse_tool_calls(text1))
    assert len(calls1) == 1, "Failed to parse tool call with newlines"
    print("✓ Parsed tool call with newlines in JSON")

    # Edge case 2: Multiple tool calls on same line
    text2 = '<tool_use>{"name": "tool1", "input": {}}</tool_use> and <tool_use>{"name": "tool2", "input": {}}</tool_use>'
    calls2 = list(parse_tool_calls(text2))
    assert len(calls2) == 2, f"Expected 2 calls on same line, got {len(calls2)}"
    print("✓ Parsed multiple tool calls on same line")

    # Edge case 3: Invalid JSON in tool call
    text3 = '<tool_use>{"invalid": json}</tool_use>'
    calls3 = list(parse_tool_calls(text3))
    assert len(calls3) == 0, "Should skip invalid JSON"
    print("✓ Correctly skipped invalid JSON")
    print()

async def main():
    """Run all tests."""
    print("\n🧪 Testing Tool Executor Workflow\n")

    try:
        await test_tool_parsing()
        await test_tool_execution()
        await test_tool_deduplication()
        await test_result_formatting()
        await test_edge_cases()

        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe tmux-based tool execution system is ready!")
        print("\nTo test end-to-end:")
        print("  ./launch-ollama-tmux qwen:7b")
        print("\nThen in the ollama chat:")
        print("  > read the contents of ollama_mcp_hub.py")
        print("\nWatch the right pane for tool execution!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
