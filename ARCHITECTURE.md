# Ollama MCP Hub - Architecture & Design

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│                    Ollama Local Models                           │
│        (qwen, llama2, mistral, neural-chat, etc.)                │
│                                                                   │
│    All models access same tools, memory, and context             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP JSON-RPC
                         │
        ┌────────────────┴────────────────┐
        │                                  │
┌───────▼────────┐              ┌────────▼────────┐
│  olcp Bridge   │              │  Web UI (future)│
│  (stdio/HTTP)  │              │  Monitor memory │
│  Model handler │              │  Check tools    │
└───────┬────────┘              └─────────────────┘
        │
        │ MCP Protocol
        │
┌───────▼─────────────────────────────────────────────────┐
│                                                           │
│         Ollama MCP Hub (mcp_server.py)                   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Tool Executor (ollama_mcp_hub.py)              │   │
│  │  • read_file, write_file, list_directory        │   │
│  │  • bash_execute (with timeout)                  │   │
│  │  • search_files (glob/grep)                     │   │
│  │  • git_status, git_commit                       │   │
│  │  • memory_save, memory_search                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Memory Store (SQLite)                          │   │
│  │  • Persistent across sessions                   │   │
│  │  • Full-text search (FTS5)                      │   │
│  │  • Tool execution logging                       │   │
│  │  • Context injection                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  System Prompt Manager                          │   │
│  │  • Base prompt with tool descriptions           │   │
│  │  • Memory context injection                     │   │
│  │  • Task-aware guidance                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
        │
        └──→ ./data/ollama_memory.db (SQLite)
```

## Key Design Principles

### 1. Model Independence
**Problem:** Each model needs to be configured separately for tools.

**Solution:** All tools live in the Hub (MCP server), not in the model. The model just makes tool calls via MCP protocol.

**Benefit:** Switch models anytime - they all access the same tools.

### 2. Persistent Memory
**Problem:** Model context is lost on restart. Good insights are forgotten.

**Solution:** Memory stored in SQLite database, searchable by content.

**Benefit:** Even after switching models or restarting, agent remembers everything.

### 3. System Prompt Injection
**Problem:** Model doesn't know what memory is relevant to current task.

**Solution:** System prompt includes memory search results based on current context.

**Benefit:** Agent provides better answers using its learned knowledge.

### 4. Tool Safety
**Problem:** Unbounded tool execution can break things.

**Solution:**
- Timeouts on all commands (prevent hangs)
- Path validation (prevent traversal)
- Confirmation for dangerous ops (coming)
- Execution logging (audit trail)

**Benefit:** Safe to run unsupervised.

---

## Components

### OllamaMCPHub (orchestrator)
```python
class OllamaMCPHub:
    def __init__(self, port: int = 8000):
        self.memory = MemoryStore()          # Persistent storage
        self.executor = ToolExecutor()       # Tool handler
        self.prompt_manager = SystemPromptManager()  # Prompt builder
    
    async def handle_tool_call(tool_name, args):
        result = await self.executor.execute(tool_name, args)
        self.memory.log_tool_execution(...)  # Log for audit trail
        return result
```

**Responsibilities:**
- Coordinate tool execution
- Manage memory
- Build prompts with context
- Log all operations

### MemoryStore (persistence)
```python
class MemoryStore:
    def save(category, content, tags) -> memory_id
    def search(query, category=None, top_k=5) -> List[Memory]
    def get_context(task) -> str  # For prompt injection
    def log_tool_execution(tool, args, result, success)
```

**Features:**
- SQLite backend with FTS5 (full-text search)
- Categories: project, feedback, code_pattern, fact, tool_execution
- Tags for filtering
- Access count to prioritize relevant memories
- Tool execution audit log

**Database Schema:**
```sql
memories (id, category, content, tags, created_at, updated_at, access_count)
tool_executions (id, tool_name, arguments, result, success, timestamp)
memories_fts (virtual table for full-text search)
```

### ToolExecutor (action handler)
```python
class ToolExecutor:
    async def execute(tool_name: str, args: Dict) -> Dict
    
    # Each tool:
    def _tool_name(self, **kwargs) -> Dict
        # Returns: {"success": bool, "stdout": str, "stderr": str, ...}
```

**Tools Implemented:**
- `read_file` - Read with line range support
- `write_file` - Create/overwrite with parent dir creation
- `list_directory` - With recursive option
- `bash_execute` - With timeout and capture
- `search_files` - Glob or grep patterns
- `git_status` - Repository status
- `git_commit` - Create commits
- `memory_save` - Store to memory
- `memory_search` - Query memory

**Tool Return Format:**
```python
{
    "success": bool,
    "stdout": str,      # For commands
    "stderr": str,      # For errors
    "return_code": int, # For processes
    "error": str,       # If failed
}
```

### SystemPromptManager (prompt engineering)
```python
class SystemPromptManager:
    BASE_PROMPT = """You are a local AI agent...
    Available tools: [list]
    Usage: <tool_use>{"name": "...", "input": {...}}</tool_use>
    """
    
    @staticmethod
    def build(memory_context: str = "") -> str:
        return BASE_PROMPT + memory_context
```

**Template:** Includes tool descriptions and usage format
**Injection:** Adds relevant memories from context

### OllamaMCPServer (MCP protocol)
```python
class OllamaMCPServer:
    def __init__(self, hub: OllamaMCPHub):
        self.server = Server("ollama-mcp-hub")
        self._setup_handlers()
    
    @self.server.list_tools()
    async def list_tools() -> List[Tool]
    
    @self.server.call_tool()
    async def call_tool(name: str, args: Dict) -> List[TextContent]
    
    async def run(host, port)
```

**Implements MCP Protocol:**
- `tools/list` - List all tools
- `tools/call` - Execute a tool
- HTTP JSON-RPC interface for olcp

---

## Data Flow

### User Request
```
User Input
    ↓
olcp receives input
    ↓
sends to MCP server (HTTP JSON-RPC)
    ↓
OllamaMCPServer.call_tool("tool_name", args)
    ↓
OllamaMCPHub.handle_tool_call(...)
    ↓
ToolExecutor.execute(...)
    ↓
Specific tool (_read_file, _bash_execute, etc.)
    ↓
Result + logging to MemoryStore
    ↓
Return to olcp
    ↓
Display to user
```

### Model Context Building
```
User message received
    ↓
OllamaMCPHub.get_system_prompt(user_message)
    ↓
MemoryStore.get_context(user_message)
    ↓
Search memory for relevant facts/patterns
    ↓
SystemPromptManager.build(memory_context)
    ↓
System Prompt = Base + Memory Context
    ↓
Send to model with conversation history
    ↓
Model generates response (with tool calls)
```

---

## Extension Points

### Adding New Tools

1. Add to `ToolExecutor._load_tools()`:
```python
"my_tool": {
    "description": "...",
    "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

2. Implement handler:
```python
async def _my_tool(self, arg1: str, arg2: int) -> Dict:
    try:
        # Implementation
        return {"success": True, "result": "..."}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

3. Add case in `execute()`:
```python
elif tool_name == "my_tool":
    return await self._my_tool(**arguments)
```

### Integrating Official MCP Servers

Eventually, can run as sub-servers:
```python
class OllamaMCPHub:
    def __init__(self):
        self.tool_executor = ToolExecutor()  # Our tools
        self.filesystem_server = FilesystemMCPServer()  # Official
        self.git_server = GitMCPServer()  # Official
        
    def get_tools(self):
        return (
            self.tool_executor.get_tools() +
            self.filesystem_server.get_tools() +
            self.git_server.get_tools()
        )
```

### Memory Enhancements

- Semantic search (using embeddings)
- Memory summarization (when DB grows)
- Category-based organization
- Time-based queries ("what happened last week")

### Safety Features (Coming)

```python
class SafetyManager:
    DANGEROUS_COMMANDS = [...patterns...]
    
    async def validate_tool_call(tool_name, args):
        if tool_name == "bash_execute":
            if any(cmd in args['command'] for cmd in DANGEROUS_COMMANDS):
                require_confirmation()
        
        if tool_name in ["write_file", "git_commit"]:
            require_confirmation()
```

---

## Configuration

Via `.env`:
```
MEMORY_DB_PATH=./data/ollama_memory.db
BASH_TIMEOUT_SECONDS=30
ALLOW_BASH_EXECUTE=true
ALLOW_FILE_WRITE=true
LOG_LEVEL=INFO
```

---

## Deployment Strategies

### Local Only
```bash
python mcp_server.py      # One machine
olcp --mcp-server ...     # Same machine
```

### Remote Server
```bash
# Server machine
python mcp_server.py --host 0.0.0.0 --port 8000

# Client machine
olcp --mcp-server http://server-ip:8000 --model qwen:7b
```

### Multiple Agents
```bash
# One hub, multiple clients
python mcp_server.py --port 8000
# Client 1
olcp --mcp-server http://localhost:8000 --model qwen:7b
# Client 2
olcp --mcp-server http://localhost:8000 --model llama2:13b
# Both share same memory!
```

---

## Performance Characteristics

### Memory Usage
- Base: ~100MB (Python + MCP SDK)
- Per memory record: ~1KB (average)
- Database: Grows with usage, pruning available

### Response Time
- Simple file ops: ~100ms
- Bash execution: 50ms - 30s (command dependent)
- Memory search: ~50ms
- MCP overhead: ~10ms

### Scalability
- Up to ~100k memories before noticeable slowdown
- SQLite can handle concurrent clients
- No hard limits on tool executions

---

## Security Model

### What's Protected
- ✅ Memory database is local SQLite (not shared)
- ✅ No external API calls (no phone home)
- ✅ All operations logged for audit
- ✅ Path validation prevents directory traversal

### What's Not Protected (by design)
- ⚠️ No tool call rate limiting (yet)
- ⚠️ No command blacklist (yet)
- ⚠️ No sandboxing for bash (by design - full local access)
- ⚠️ No authentication (assumes trusted local use)

---

## Future Improvements

### Phase 2
- [ ] Integrate official MCP servers (filesystem, git, fetch)
- [ ] Web UI for memory browser
- [ ] Process management tools
- [ ] Environment variable tools

### Phase 3
- [ ] Semantic search over memory (embeddings)
- [ ] Memory summarization & archiving
- [ ] Tool confirmation system
- [ ] Rate limiting & safety policies

### Phase 4
- [ ] Multi-user support with authentication
- [ ] Distributed memory (Redis)
- [ ] Plugin system for custom tools
- [ ] LLM-powered memory deduplication

---

**This architecture enables ANY local model to have full developer capabilities with persistent learning.**
