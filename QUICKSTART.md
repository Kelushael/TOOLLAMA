# Quick Start - 5 Minutes to Your Local AI Agent

## Prerequisites
- Ollama installed ([ollama.com](https://ollama.com))
- Python 3.11+
- ~5 minutes

## Step 1: Start Ollama
```bash
ollama serve
```
Keep this running in a terminal.

## Step 2: Pull a Model
In another terminal:
```bash
ollama pull qwen:7b
```

(Other models: `llama2`, `mistral`, `neural-chat`, `dolphin-mixtral`)

## Step 3: Setup the Hub
```bash
cd ollama-mcp-hub

# Run setup script
bash setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Start MCP Server
```bash
source venv/bin/activate  # if not already activated
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
```

## Step 5: Start Agent (New Terminal)
```bash
# Install olcp if needed (one-time)
pip install ollama-mcp-client

# Start the agent
olcp --mcp-server http://127.0.0.1:8000 --model qwen:7b
```

## Step 6: Use It!

```
> Create a Python script that calculates factorial numbers

[Agent creates the file with code]

> Run it

[Agent executes it and shows output]

> Add a function to print the first 10 factorials

[Agent modifies the file]

> Run it again

[Agent runs the updated script]
```

## Key Commands in Agent

```
/model llama2           # Switch models (keeps all context!)
/memory                 # Show what you've learned
/search previous work   # Find things you did before
/exit                   # Quit
```

## That's It!

You now have a local Claude Code-like agent that:
✅ Works with ANY Ollama model (swap anytime)
✅ Remembers everything across sessions
✅ Runs entirely on your machine
✅ Completely free and private

## Next Steps

- Try more complex tasks
- Read `README.md` for advanced features
- Check `ollama_mcp_hub.py` to see how tools work
- Add your own tools!

## Troubleshooting

**"Connection refused"**
- Make sure `python mcp_server.py` is running
- Check port 8000 is free: `lsof -i :8000`

**Model not found**
- `ollama pull qwen:7b` to download it

**Memory not working**
- Check `./data/` directory exists
- Run `chmod 755 data/`

---

**Enjoy your local AI agent!** 🚀
