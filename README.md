# Ollama MCP Hub - Universal Developer Agent

**Run Claude Code locally with ANY Ollama model. No configuration needed.**

This integrates the Model Context Protocol (MCP) with Ollama, giving any local model:
- Complete filesystem access (read/write/edit files)
- Shell command execution (bash, Python, etc.)
- Git operations
- Persistent memory system (remembers across sessions & model swaps)
- Works with **ANY** Ollama model (swap anytime without losing context)

## Quick Start

### 1. Install Ollama
Download from [ollama.com](https://ollama.com) and install.

### 2. Pull a Model
```bash
ollama pull qwen:7b
# or any other model: llama2, mistral, neural-chat, etc.
```

### 3. Clone & Setup This Project
```bash
git clone <this-repo>
cd ollama-mcp-hub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start the MCP Server
```bash
python mcp_server.py
```

You should see:
```
============================================================
OLLAMA MCP HUB - HTTP Server
============================================================
✓ Server running on http://127.0.0.1:8000
✓ Tools available: 11
✓ Memory persisted to: ./data/ollama_memory.db
============================================================

Usage:
  olcp --mcp-server http://127.0.0.1:8000 --model <any_ollama_model>
```

### 5. In Another Terminal, Start the Agent
```bash
# Install olcp if needed
pip install ollama-mcp-client  # or: uvx ollama-mcp-client

# Run the agent
olcp --mcp-server http://127.0.0.1:8000 --model qwen:7b
```

Now you can chat with your local agent:
```
> Create a Python script that calculates fibonacci numbers
[Agent reads files, creates script, shows preview]

> Add a function to print the numbers
[Agent edits the file]

> Run the script
[Agent executes it]
```

## Features

### Available Tools

- **read_file** - Read file contents
- **write_file** - Create/overwrite files  
- **list_directory** - List files and directories
- **bash_execute** - Run shell commands with timeout
- **search_files** - Find files using glob or grep
- **git_status** - Check git repository status
- **git_commit** - Create commits with messages
- **memory_save** - Save information to persistent memory
- **memory_search** - Search past memory
- *(More coming: process management, env variables)*

### Persistent Memory System

The agent remembers everything:
```
> Remember that I prefer Python over JavaScript
[Saved to memory]

> What's my preference?
[Agent searches memory and tells you]

> (Switch to a different model)
/model llama2

> What did we just talk about?
[New model retrieves from same memory]
```

### Model Swapping (Zero Context Loss)

Switch models anytime without losing conversation or memory:
```
> /model mistral:7b
[Switches immediately, keeps all context]
```

## Commands in olcp

Once inside the olcp interface:

```
/model <name>        - Switch to different model (qwen:7b, llama2, etc.)
/memory              - Show memory statistics
/search <query>      - Search your memory
/exit                - Exit the agent
/help                - Show all commands
```

## Example Usage

### Create a Full Web App

```
> Create a Flask web app with:
  - HTML form for user input
  - Backend that processes the input
  - Save to app.py

[Agent creates the file]

> Now create a requirements.txt

> Run it with python app.py

[Agent executes it]

> The form isn't styled nicely. Add CSS styling

[Agent edits the HTML]

> Push to git
```

### Debug and Fix Code

```
> I have a Python script called process.py that's broken
> Can you debug it?

[Agent reads the file, identifies issues, fixes them]

> Run it and show me the output

[Agent executes and shows results]
```

### Remember Your Workflow

```
> I always add type hints and docstrings to my Python code

[Memory saves this]

> Create a function that...

[Agent creates code with type hints and docstrings automatically]
```

## System Architecture

```
┌─────────────────────────────────────────┐
│     Ollama Local Model                  │
│  (qwen, llama, mistral, neural-chat...) │
└────────────────┬────────────────────────┘
                 │
                 │ HTTP JSON-RPC
                 ↓
┌─────────────────────────────────────────┐
│      olcp Bridge (stdio/HTTP)           │
│   Handles model ↔ MCP communication     │
└────────────────┬────────────────────────┘
                 │
                 │ MCP Protocol
                 ↓
┌─────────────────────────────────────────┐
│  Ollama MCP Hub (mcp_server.py)         │
│  ├─ Tool Executor                       │
│  ├─ Memory System (SQLite)              │
│  ├─ System Prompt Manager               │
│  └─ 11+ Developer Tools                 │
└─────────────────────────────────────────┘
```

**Key Advantage:** The memory and tools are in the Hub, not the model. So switching models doesn't lose anything.

## Configuration

Create `.env` file to customize:

```bash
# Default values shown below

# Memory storage
MEMORY_DB_PATH=./data/ollama_memory.db

# Server
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000

# Timeouts
BASH_TIMEOUT_SECONDS=30
FILE_READ_TIMEOUT_SECONDS=30

# Safety flags (coming soon)
ALLOW_BASH=true
ALLOW_FILE_WRITE=true
```

## Troubleshooting

### "Connection refused" when starting olcp
- Make sure `python mcp_server.py` is running in another terminal
- Check that port 8000 is not in use: `lsof -i :8000`

### Model not found
- Make sure you've pulled the model: `ollama pull qwen:7b`
- Check available models: `ollama list`

### Memory not persisting
- Check that `./data/` directory exists and is writable
- Check permissions: `ls -la data/ollama_memory.db`

### Tools not working
- Check the server logs for errors
- Try a simpler command first: `/bash "echo hello"`

## Supported Models

Tested and working:
- ✅ qwen:7b, qwen:14b, qwen:32b
- ✅ llama2:7b, llama2:13b
- ✅ mistral:7b
- ✅ neural-chat:7b
- ✅ dolphin-mixtral:8x7b

Any model that supports tool/function calling should work!

## Advanced: Running with Multiple MCP Servers

You can run multiple MCP servers and connect them all:

```bash
# Terminal 1: Official filesystem server
python -m mcp.servers.filesystem

# Terminal 2: Official git server  
python -m mcp.servers.git

# Terminal 3: Our Ollama hub
python mcp_server.py

# Terminal 4: Connect to hub (which can also access the others)
olcp --mcp-server http://127.0.0.1:8000 --model qwen:7b
```

## Development

### Add New Tools

Edit `ollama_mcp_hub.py` in the `ToolExecutor` class:

```python
def _my_new_tool(self, arg1: str) -> Dict:
    """Do something useful"""
    try:
        # Your implementation
        return {"success": True, "result": "..."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _load_tools(self) -> Dict[str, Dict]:
    return {
        # ... existing tools ...
        "my_new_tool": {
            "description": "Description of what it does",
            "input_schema": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"}
                },
                "required": ["arg1"]
            }
        }
    }
```

Then add handler in `execute()` method.

### Integrate Official MCP Servers

The goal is to eventually run all of these:
- `filesystem` - Advanced file operations
- `git` - Full git integration
- `fetch` - Web scraping and HTTP
- `memory` - Advanced memory features
- `sequentialthinking` - Multi-step reasoning

These will be integrated as sub-servers in the hub.

## Privacy & Security

- ✅ Everything runs locally on your machine
- ✅ No data sent to cloud services
- ✅ Models run on your hardware
- ✅ Memory stored in local SQLite database
- ✅ No API keys or authentication needed

## Performance Tips

1. **Model Size:** Smaller models run faster
   - 7B parameters: Fast, good for most tasks
   - 13B parameters: Better quality, slower
   - 32B+: High quality but slow on consumer hardware

2. **Hardware:** More VRAM = faster execution
   - 8GB RAM: Works, may be slow
   - 16GB RAM: Comfortable for 7B-13B models
   - 32GB RAM: Great for larger models

3. **Context Length:** Balance speed vs quality
   - Longer context = more memory but slower
   - Start with default, increase if needed

## Contributing

Improvements welcome! Areas to work on:
- [ ] Integrate official MCP servers (filesystem, git, fetch)
- [ ] Process management tools
- [ ] Environment variable tools
- [ ] Improved error messages
- [ ] Web UI for memory/status
- [ ] Performance optimizations
- [ ] More safety checks

## License

MIT - Use freely!

## Support

Having issues? 
1. Check logs: `tail -f mcp_server.log`
2. Try a different model
3. Check Ollama is running: `ollama serve`
4. Verify network: `curl http://127.0.0.1:8000/health`

---

**Now you have Claude Code running locally for free, with any model you want!**

Built with ❤️ using Ollama + MCP + Python
