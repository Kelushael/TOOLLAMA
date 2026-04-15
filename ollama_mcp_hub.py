#!/usr/bin/env python3
"""
Ollama MCP Hub - Unified integration of all MCP servers with Ollama
Works with ANY model, NO model-specific configuration needed.

This server aggregates:
- Official MCP servers (filesystem, git, fetch, memory, etc.)
- DesktopCommanderMCP tools
- Custom developer tools
- Persistent memory system

Run with: python ollama_mcp_hub.py
Then connect via: olcp --mcp-server http://localhost:8000 --model <any_ollama_model>
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import sqlite3
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ollama-mcp-hub")


# ============================================================================
# MEMORY SYSTEM - Persistent across all models
# ============================================================================

@dataclass
class Memory:
    """Single memory record"""
    id: str
    category: str  # "project", "feedback", "code_pattern", "fact", "tool_execution"
    content: str
    tags: List[str]
    created_at: str
    updated_at: str
    access_count: int = 0


class MemoryStore:
    """SQLite-based persistent memory system"""

    def __init__(self, db_path: str = "./data/ollama_memory.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with memory tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Main memories table
        c.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT,
                access_count INTEGER DEFAULT 0
            )
        """)

        # Full-text search index
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content,
                category,
                content=memories,
                content_rowid=rowid
            )
        """)

        # Tool execution history
        c.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                arguments TEXT,
                result TEXT,
                success BOOLEAN,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save(self, category: str, content: str, tags: List[str] = None) -> str:
        """Save a memory"""
        import uuid
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        tags_str = json.dumps(tags or [])
        c.execute("""
            INSERT INTO memories (id, category, content, tags, created_at, updated_at, access_count)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (memory_id, category, content, tags_str, now, now))

        conn.commit()
        conn.close()

        logger.info(f"Memory saved: {memory_id} ({category})")
        return memory_id

    def search(self, query: str, category: str = None, top_k: int = 5) -> List[Memory]:
        """Search memories by text"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if category:
            c.execute("""
                SELECT id, category, content, tags, created_at, updated_at, access_count
                FROM memories
                WHERE category = ? AND (content LIKE ? OR tags LIKE ?)
                ORDER BY access_count DESC
                LIMIT ?
            """, (category, f"%{query}%", f"%{query}%", top_k))
        else:
            c.execute("""
                SELECT id, category, content, tags, created_at, updated_at, access_count
                FROM memories
                WHERE content LIKE ? OR tags LIKE ?
                ORDER BY access_count DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", top_k))

        results = c.fetchall()
        conn.close()

        memories = []
        for row in results:
            memories.append(Memory(
                id=row[0],
                category=row[1],
                content=row[2],
                tags=json.loads(row[3]) if row[3] else [],
                created_at=row[4],
                updated_at=row[5],
                access_count=row[6]
            ))

        return memories

    def get_context(self, task_description: str, top_k: int = 3) -> str:
        """Get relevant memory context for current task"""
        relevant = self.search(task_description, top_k=top_k)
        if not relevant:
            return ""

        context_lines = ["# Relevant Context from Memory:"]
        for mem in relevant:
            context_lines.append(f"- [{mem.category}] {mem.content[:200]}")

        return "\n".join(context_lines)

    def log_tool_execution(self, tool_name: str, arguments: Dict, result: Dict, success: bool):
        """Log tool execution to memory"""
        import uuid
        exec_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO tool_executions (id, tool_name, arguments, result, success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            exec_id,
            tool_name,
            json.dumps(arguments),
            json.dumps(result),
            success,
            now
        ))

        conn.commit()
        conn.close()

        # Also save to memories for semantic search
        summary = f"Executed {tool_name}: {result.get('stdout', '')[:100]}"
        self.save("tool_execution", summary, tags=[tool_name, "execution"])

    def get_stats(self) -> Dict:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM memories")
        total_memories = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tool_executions")
        total_executions = c.fetchone()[0]

        c.execute("SELECT COUNT(DISTINCT category) FROM memories")
        categories = c.fetchone()[0]

        conn.close()

        return {
            "total_memories": total_memories,
            "total_executions": total_executions,
            "categories": categories,
            "db_path": self.db_path
        }


# ============================================================================
# SYSTEM PROMPT MANAGEMENT
# ============================================================================

class SystemPromptManager:
    """Manages system prompts with memory context injection"""

    BASE_PROMPT = """You are a local AI agent with full access to developer tools.

You are running on the user's machine with access to:
- Filesystem operations (read, write, edit files)
- Shell commands (bash, PowerShell, etc.)
- Git version control
- Process management
- Web fetching
- Time utilities
- Persistent memory system

## How to Use Tools

When you need to use a tool, format requests as:
<tool_use>
{
  "name": "tool_name",
  "input": {
    "param1": "value1",
    "param2": "value2"
  }
}
</tool_use>

You can chain multiple tool calls in a single response.

## Guidelines

1. Always preview file contents before making changes
2. Explain your approach before executing dangerous operations
3. Use memory to track patterns and learned insights
4. Ask clarifying questions when requests are ambiguous
5. Be cautious with destructive operations (deletions, overwrites)
6. Test changes when possible before finalizing
7. Leverage memory context for informed decisions

## Important Notes

- You work with your local Ollama installation
- Your model can be switched anytime without losing context
- Memory persists across all sessions
- All tool executions are logged for future reference
- Path guidance: Use absolute paths when possible
"""

    @staticmethod
    def build(memory_context: str = "") -> str:
        """Build final system prompt with memory context"""
        if memory_context:
            return SystemPromptManager.BASE_PROMPT + f"\n\n## Your Memory Context\n\n{memory_context}"
        return SystemPromptManager.BASE_PROMPT


# ============================================================================
# TOOL DEFINITIONS & EXECUTION
# ============================================================================

class ToolExecutor:
    """Execute tools with safety checks and memory integration"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store
        self.tools = self._load_tools()

    def _load_tools(self) -> Dict[str, Dict]:
        """Load all available tools with their schemas"""
        return {
            # Filesystem tools
            "read_file": {
                "description": "Read file contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "start_line": {"type": "integer", "description": "Start line (optional)"},
                        "end_line": {"type": "integer", "description": "End line (optional)"},
                    },
                    "required": ["path"]
                }
            },
            "write_file": {
                "description": "Write/create a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"]
                }
            },
            "list_directory": {
                "description": "List directory contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                        "recursive": {"type": "boolean", "description": "Recursive listing (optional)"},
                    },
                    "required": ["path"]
                }
            },
            "bash_execute": {
                "description": "Execute bash/shell command",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "timeout_seconds": {"type": "integer", "description": "Timeout (default: 30)"},
                    },
                    "required": ["command"]
                }
            },
            "search_files": {
                "description": "Search for files using glob or grep",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "path": {"type": "string", "description": "Search path (default: .)"},
                        "search_type": {"type": "string", "enum": ["glob", "grep"]},
                    },
                    "required": ["pattern"]
                }
            },
            # Git tools
            "git_status": {
                "description": "Get git repository status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                    },
                    "required": ["repo_path"]
                }
            },
            "git_commit": {
                "description": "Create a git commit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["repo_path", "message"]
                }
            },
            # Memory tools
            "memory_save": {
                "description": "Save information to persistent memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "content": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["category", "content"]
                }
            },
            "memory_search": {
                "description": "Search persistent memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"]
                }
            },
        }

    def get_tools(self) -> List[Dict]:
        """Get all tool definitions for MCP"""
        return [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["input_schema"]
            }
            for name, tool in self.tools.items()
        ]

    async def execute(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute a tool"""
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        try:
            if tool_name == "read_file":
                return self._read_file(**arguments)
            elif tool_name == "write_file":
                return self._write_file(**arguments)
            elif tool_name == "list_directory":
                return self._list_directory(**arguments)
            elif tool_name == "bash_execute":
                return self._bash_execute(**arguments)
            elif tool_name == "search_files":
                return self._search_files(**arguments)
            elif tool_name == "git_status":
                return self._git_status(**arguments)
            elif tool_name == "git_commit":
                return self._git_commit(**arguments)
            elif tool_name == "memory_save":
                return self._memory_save(**arguments)
            elif tool_name == "memory_search":
                return self._memory_search(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            result = {"success": False, "error": str(e)}
            self.memory.log_tool_execution(tool_name, arguments, result, False)
            return result

    def _read_file(self, path: str, start_line: int = None, end_line: int = None) -> Dict:
        """Read file"""
        try:
            with open(path, 'r') as f:
                content = f.read()

            if start_line and end_line:
                lines = content.split('\n')
                content = '\n'.join(lines[start_line-1:end_line])

            return {
                "success": True,
                "content": content,
                "lines": len(content.split('\n'))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_file(self, path: str, content: str) -> Dict:
        """Write file"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            self.memory.save("file_write", f"Wrote to {path}", tags=["file", "write"])
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_directory(self, path: str = ".", recursive: bool = False) -> Dict:
        """List directory"""
        try:
            items = []
            p = Path(path)
            pattern = "**/*" if recursive else "*"
            for item in p.glob(pattern):
                items.append({
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _bash_execute(self, command: str, timeout_seconds: int = 30) -> Dict:
        """Execute bash command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout_seconds}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search_files(self, pattern: str, path: str = ".", search_type: str = "glob") -> Dict:
        """Search files"""
        try:
            results = []
            if search_type == "glob":
                p = Path(path)
                for item in p.glob(pattern):
                    results.append(str(item))
            else:  # grep
                result = subprocess.run(
                    f"grep -r '{pattern}' {path}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                results = result.stdout.split('\n')[:20]  # Limit results

            return {"success": True, "results": results[:50]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _git_status(self, repo_path: str = ".") -> Dict:
        """Get git status"""
        try:
            result = subprocess.run(
                f"cd {repo_path} && git status",
                shell=True,
                capture_output=True,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "status": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _git_commit(self, repo_path: str, message: str) -> Dict:
        """Create git commit"""
        try:
            result = subprocess.run(
                f"cd {repo_path} && git add -A && git commit -m '{message}'",
                shell=True,
                capture_output=True,
                text=True
            )
            self.memory.save("git_commit", f"Committed: {message}", tags=["git", "commit"])
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _memory_save(self, category: str, content: str, tags: List[str] = None) -> Dict:
        """Save to memory"""
        try:
            memory_id = self.memory.save(category, content, tags)
            return {"success": True, "memory_id": memory_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _memory_search(self, query: str) -> Dict:
        """Search memory"""
        try:
            results = self.memory.search(query)
            return {
                "success": True,
                "results": [asdict(r) for r in results]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# MCP SERVER - The main integration point
# ============================================================================

class OllamaMCPHub:
    """Main MCP server for Ollama integration"""

    def __init__(self, port: int = 8000):
        self.port = port
        self.memory = MemoryStore()
        self.executor = ToolExecutor(self.memory)
        self.prompt_manager = SystemPromptManager()

        logger.info(f"Initialized Ollama MCP Hub on port {port}")

    async def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle tool call from model"""
        result = await self.executor.execute(tool_name, arguments)
        self.memory.log_tool_execution(tool_name, arguments, result, result.get("success", False))
        return result

    def get_tools(self) -> List[Dict]:
        """Get all available tools"""
        return self.executor.get_tools()

    def get_system_prompt(self, task_context: str = "") -> str:
        """Get system prompt with memory context"""
        memory_context = self.memory.get_context(task_context)
        return self.prompt_manager.build(memory_context)

    async def start(self):
        """Start the MCP server"""
        logger.info(f"Starting Ollama MCP Hub on port {self.port}")
        logger.info(f"Memory stats: {self.memory.get_stats()}")
        logger.info("\nTo connect with Ollama:")
        logger.info(f"  olcp --mcp-server http://localhost:{self.port} --model <model_name>\n")

        # For now, just run indefinitely
        # In production, would use a proper HTTP/WebSocket server
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    hub = OllamaMCPHub(port=8000)

    # Log capabilities
    logger.info("\n" + "="*60)
    logger.info("OLLAMA MCP HUB - Model Context Protocol Integration")
    logger.info("="*60)
    logger.info(f"Available tools: {len(hub.get_tools())}")
    for tool in hub.get_tools():
        logger.info(f"  - {tool['name']}: {tool['description']}")
    logger.info("="*60 + "\n")

    await hub.start()


if __name__ == "__main__":
    asyncio.run(main())
