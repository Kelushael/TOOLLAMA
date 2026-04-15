#!/usr/bin/env python3
"""
Tool Proxy - Intercepts model tool calls and executes them

Sits between ollama output and stdin/stdout, parsing <tool_use> blocks
and executing them via the OllamaMCPHub.
"""

import sys
import json
import re
import asyncio
from ollama_mcp_hub import OllamaMCPHub

hub = OllamaMCPHub()

def parse_tool_calls(text):
    """Extract all <tool_use>...</tool_use> blocks from text."""
    pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
    matches = []
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            tool_call = json.loads(match.group(1))
            matches.append((match.group(0), tool_call))
        except json.JSONDecodeError:
            pass
    return matches

async def execute_tool_call(tool_name, args):
    """Execute a single tool call."""
    try:
        result = await hub.executor.execute(tool_name, args)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

async def process_tool_calls(text):
    """Find and execute tool calls in text, return results."""
    tool_calls = parse_tool_calls(text)

    if not tool_calls:
        return text, []

    results = []
    for block, tool_call in tool_calls:
        tool_name = tool_call.get("name")
        args = tool_call.get("input", {})

        print(f"[TOOL] Executing: {tool_name}", file=sys.stderr)
        result = await execute_tool_call(tool_name, args)

        # Format result for model
        result_text = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
        results.append({
            "tool": tool_name,
            "result": result_text
        })
        print(f"[TOOL] Result: {result_text[:100]}...", file=sys.stderr)

    return text, results

async def main():
    """Read from stdin, execute tools, output results."""
    try:
        # Read all input from the model
        input_text = sys.stdin.read()

        # Process any tool calls
        output_text, results = await process_tool_calls(input_text)

        # Output the original text plus results
        print(output_text)

        # Append tool results as context for next model iteration
        if results:
            print("\n[TOOL RESULTS]")
            for r in results:
                print(f"\n{r['tool']}:")
                print(r['result'])

    except Exception as e:
        print(f"Error in tool proxy: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
