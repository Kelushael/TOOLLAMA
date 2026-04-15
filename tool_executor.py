#!/usr/bin/env python3
"""
Tool Executor - Monitors tmux left pane for tool calls, executes silently on right

Runs in right pane, watches left pane output, executes tools, sends results back.
"""

import subprocess
import sys
import json
import re
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ollama_mcp_hub import OllamaMCPHub

hub = OllamaMCPHub()

SESSION = sys.argv[1] if len(sys.argv) > 1 else "ollama-tools"

def get_pane_output(session, pane):
    """Get all output from a tmux pane."""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", f"{session}.{pane}", "-p"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except:
        return ""

def send_to_pane(session, pane, text):
    """Send text to tmux pane."""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", f"{session}.{pane}", text, "Enter"],
            capture_output=True
        )
    except:
        pass

def parse_tool_calls(text):
    """Extract tool calls from text - supports multiple formats."""

    # Format 1: JSON tool_use blocks (standard format)
    pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            yield json.loads(match.group(1))
            continue
        except:
            pass

    # Format 2: Natural language tool calls (for any model)
    # Detect patterns like: "read file X", "execute Y", "search Z"
    text_lower = text.lower()

    # Multi-word patterns first (more specific)
    nlp_patterns = [
        (r'(?:git\s+(?:commit|push)|commit\s+)', 'git_commit'),
        (r'(?:git\s+status|check\s+git)', 'git_status'),
        (r'(?:search\s+memory|recall)', 'memory_search'),
        (r'(?:save\s+memory|remember)', 'memory_save'),
        (r'(?:read\s+(?:the\s+)?file|open\s+(?:the\s+)?file|view\s+(?:the\s+)?file)', 'read_file'),
        (r'(?:write\s+(?:to\s+)?file|create\s+(?:a\s+)?file|save\s+(?:to\s+)?file)', 'write_file'),
        (r'(?:list\s+(?:the\s+)?(?:directory|dir|files)|show\s+files)', 'list_directory'),
        (r'(?:search\s+for|find\s+|grep\s+)', 'search_files'),
        (r'(?:execute\s+|run\s+|bash\s+|execute\s+command|run\s+command)', 'bash_execute'),
    ]

    found_tools = {}

    for pattern, tool_name in nlp_patterns:
        if re.search(pattern, text_lower) and tool_name not in found_tools:
            found_tools[tool_name] = True

            # Extract arguments based on tool type
            args = {}

            # Try quoted strings first
            quoted = re.findall(r'"([^"]+)"', text)

            if tool_name == 'read_file':
                # Extract path: "read file /path/to/file" or in quotes
                path_match = re.search(r'(?:read|open|view)\s+(?:the\s+)?(?:file\s+)?([^\s;,\)]+)', text)
                if path_match:
                    args = {'path': path_match.group(1).rstrip('.,;')}
                elif quoted:
                    args = {'path': quoted[0]}

            elif tool_name == 'write_file':
                if len(quoted) >= 1:
                    args = {'path': quoted[0], 'content': quoted[1] if len(quoted) > 1 else ''}

            elif tool_name == 'bash_execute':
                # Extract command: "execute ls -la /tmp" or "run grep test"
                cmd_match = re.search(r'(?:execute|run|bash)\s+(.+?)(?:\s+(?:in|at)\s+|$)', text)
                if cmd_match:
                    args = {'command': cmd_match.group(1).strip().rstrip('.,;')}
                elif quoted:
                    args = {'command': quoted[0]}

            elif tool_name == 'search_files':
                search_match = re.search(r'(?:search|find|grep)\s+(?:for\s+)?(.+?)(?:\s+(?:in|at)\s+|$)', text)
                if search_match:
                    args = {'path': search_match.group(1).strip().rstrip('.,;')}
                elif quoted:
                    args = {'path': quoted[0]}

            elif tool_name in ['list_directory', 'memory_search']:
                dir_match = re.search(r'(?:in|at|directory)\s+([^\s;,\)]+)', text)
                if dir_match:
                    args = {'path': dir_match.group(1).rstrip('.,;')}
                elif quoted:
                    args = {'path': quoted[0]}

            elif tool_name == 'git_status':
                # git status doesn't need arguments usually
                args = {'path': '.'}

            elif tool_name == 'git_commit':
                msg_match = re.search(r'(?:commit|push).*?["\']([^"\']+)["\']', text)
                if msg_match:
                    args = {'message': msg_match.group(1)}

            elif tool_name == 'memory_save':
                args = {'content': text}  # Save the whole statement

            if args:
                yield {
                    'name': tool_name,
                    'input': args,
                    'confidence': 'medium'  # Mark as detected, not explicit
                }

async def execute_tool(name, args):
    """Execute a tool."""
    try:
        return await hub.executor.execute(name, args)
    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    """Monitor left pane and execute tools on the right."""

    print("🔧 Tool Executor Active")
    print("Monitoring ollama chat for tool calls...")
    print("")

    seen_calls = set()

    try:
        while True:
            # Get output from left pane (ollama)
            left_output = get_pane_output(SESSION, 0)

            # Look for tool calls
            for tool_call in parse_tool_calls(left_output):
                name = tool_call.get("name")
                args = tool_call.get("input", {})
                call_id = f"{name}:{json.dumps(args, sort_keys=True)}"

                # Skip if we've already executed this
                if call_id in seen_calls:
                    continue

                seen_calls.add(call_id)

                # Execute tool
                print(f"\n⚙️  Executing: {name}")
                result = await execute_tool(name, args)

                if result.get("success"):
                    print(f"✓ Success")
                else:
                    print(f"✗ Error: {result.get('error', 'Unknown')}")

                # Format result as markdown
                result_md = f"\n**[Tool Result: {name}]**\n```json\n{json.dumps(result, indent=2)}\n```\n"

                # Send result back to left pane
                # Note: This is tricky - we send it as if the user typed it
                send_to_pane(SESSION, 0, result_md)

                print(f"→ Result sent to chat")

            # Small delay to avoid busy-waiting
            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 Tool executor stopped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
