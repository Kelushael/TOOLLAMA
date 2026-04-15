#!/usr/bin/env python3
"""
Interactive Ollama Wrapper with Tool Proxy

Runs ollama interactively, intercepts tool calls, executes them.
"""

import subprocess
import sys
import json
import re
import asyncio
from pathlib import Path

# Add hub to path
sys.path.insert(0, str(Path(__file__).parent))
from ollama_mcp_hub import OllamaMCPHub

hub = OllamaMCPHub()

TOOL_SYSTEM = """You are a helpful AI assistant with full access to developer tools.

AVAILABLE TOOLS:
1. read_file - Read file contents (param: path)
2. write_file - Create/write files (params: path, content)
3. bash_execute - Run shell commands (param: command)
4. list_directory - List directory contents (param: path)
5. search_files - Find files with glob/grep (params: pattern, path, search_type)
6. git_status - Check git status (param: repo_path)
7. git_commit - Create git commit (params: repo_path, message)
8. memory_save - Save to persistent memory (params: category, content, tags)
9. memory_search - Search memory (param: query)

WHEN YOU NEED TO USE A TOOL, RESPOND WITH:
<tool_use>
{"name": "tool_name", "input": {"param": "value"}}
</tool_use>

EXAMPLES:
- List files: <tool_use>{"name": "list_directory", "input": {"path": "."}</tool_use>
- Read file: <tool_use>{"name": "read_file", "input": {"path": "script.py"}</tool_use>
- Run command: <tool_use>{"name": "bash_execute", "input": {"command": "ls -la"}</tool_use>

You can use multiple tools in one response. Always explain what you're doing."""


def parse_tool_calls(text):
    """Extract tool calls from model output."""
    pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
    matches = []
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            tool_call = json.loads(match.group(1))
            matches.append(tool_call)
        except json.JSONDecodeError:
            pass
    return matches


async def execute_tool(name, args):
    """Execute a tool and return result."""
    try:
        result = await hub.executor.execute(name, args)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "gemma4:e4b"

    print(f"🚀 Starting {model} with full tool access...")
    print("Tools: read_file, write_file, bash_execute, list_directory, search_files, git_status, git_commit, memory_save, memory_search\n")

    # Start ollama process
    proc = subprocess.Popen(
        ["ollama", "run", model],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    # Send system prompt
    proc.stdin.write(TOOL_SYSTEM + "\n")
    proc.stdin.flush()

    # Interactive loop
    try:
        while True:
            # Get user input
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Send to ollama
            proc.stdin.write(user_input + "\n")
            proc.stdin.flush()

            # Read response until we see a tool call or EOF
            response = ""
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                response += line
                # Check if we have a complete response (for now, just accumulate)
                if "\n\n" in response or "<tool_use>" in response:
                    break

            print(f"\nAssistant: {response}\n")

            # Check for tool calls
            tool_calls = parse_tool_calls(response)
            if tool_calls:
                for tool_call in tool_calls:
                    name = tool_call.get("name")
                    args = tool_call.get("input", {})
                    print(f"[Executing tool: {name}]")
                    result = await execute_tool(name, args)
                    print(f"[Result: {json.dumps(result)[:100]}...]\n")

                    # Send result back to ollama for context
                    result_prompt = f"Tool {name} returned: {json.dumps(result)}\n"
                    proc.stdin.write(result_prompt)
                    proc.stdin.flush()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    asyncio.run(main())
