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
    """Extract tool calls from text."""
    pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            yield json.loads(match.group(1))
        except:
            pass

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
