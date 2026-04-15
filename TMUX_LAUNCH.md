# Tmux-Based Tool Execution Guide

## Quick Start

```bash
./launch-ollama-tmux qwen:7b
```

This creates a tmux session with two panes:
- **Left pane (70%)**: Normal `ollama run` chat interface
- **Right pane (30%)**: Silent tool executor daemon

## What Happens

1. **Left pane**: You chat with the model normally
   ```
   > Read the file ollama_mcp_hub.py
   
   Assistant: I'll read that file for you.
   <tool_use>{"name": "read_file", "input": {"path": "ollama_mcp_hub.py"}}</tool_use>
   ```

2. **Right pane**: Tool executor detects the tool call
   ```
   ⚙️  Executing: read_file
   ✓ Success
   → Result sent to chat
   ```

3. **Left pane**: Model receives the result and responds
   ```
   Here's the content of ollama_mcp_hub.py:
   #!/usr/bin/env python3
   ...
   ```

## Features

✅ **Transparent**: No special syntax needed in chat  
✅ **Silent**: Tool execution doesn't clutter the chat  
✅ **Automatic**: Works with ANY Ollama model  
✅ **Persistent**: Memory survives model switches  
✅ **Safe**: Timeout protection and error handling  

## Available Tools

- **read_file** - Read file contents
- **write_file** - Create/write files  
- **list_directory** - List directory contents
- **bash_execute** - Run shell commands
- **search_files** - Find files with glob/grep
- **git_status** - Check git status
- **git_commit** - Create git commits
- **memory_save** - Save to persistent memory
- **memory_search** - Search memory

## Multiple Models

All models share the same memory system:

```bash
# Terminal 1
./launch-ollama-tmux qwen:7b

# Terminal 2 (different window)
./launch-ollama-tmux llama2

# Both have access to the same persistent memory
# and can reference previous tool executions
```

## Internals

- **Tool calls format**: `<tool_use>{JSON}</tool_use>` in model output
- **Parsing**: Regex-based extraction with deduplication
- **Execution**: Via OllamaMCPHub with async support
- **Memory**: SQLite FTS5 with full-text search
- **IPC**: Tmux pane text capture and send-keys

## Testing

```bash
python3 test_tool_executor.py
```

Tests verify:
- Tool call parsing (single and multiple)
- Tool execution (read, list)
- Deduplication logic
- Result formatting
- Edge cases (multiline JSON, invalid JSON)
