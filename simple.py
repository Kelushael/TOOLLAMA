#!/usr/bin/env python3
"""
ULTRA SIMPLE: Run ollama with tools access

This is literally just a wrapper that adds tool context to ollama run.

Usage:
    python3 simple.py qwen:7b
"""

import subprocess
import json
from pathlib import Path
from ollama_mcp_hub import OllamaMCPHub

hub = OllamaMCPHub()

# Build the system prompt with all tools
tools_list = "\n".join([
    f"- {tool['name']}: {tool['description']}"
    for tool in hub.get_tools()
])

system_prompt = f"""You are a helpful coding assistant with access to the following tools:

{tools_list}

When you need to use a tool, respond with:
<tool_use>
{{"name": "tool_name", "input": {{"param": "value"}}}}
</tool_use>

For example, to read a file:
<tool_use>
{{"name": "read_file", "input": {{"path": "/path/to/file"}}}}
</tool_use>

You can use multiple tools in one response. Always explain what you're doing before using tools."""

model = "qwen:7b" if len(__import__("sys").argv) < 2 else __import__("sys").argv[1]

print(f"Starting {model}...")
print("Type exit to quit\n")

# Just run ollama with the enhanced prompt
cmd = ["ollama", "run", model, system_prompt]

try:
    subprocess.run(cmd)
except FileNotFoundError:
    print("Error: ollama not found. Make sure Ollama is installed and in PATH")
    print("Download from: https://ollama.com")
