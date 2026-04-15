#!/usr/bin/env python3
"""
MCP Protocol Server for Ollama Integration
Implements the Model Context Protocol to work with olcp bridge.

Usage:
    python mcp_server.py

Then in another terminal:
    olcp --mcp-server http://localhost:8000 --model qwen:7b
"""

import json
import logging
import asyncio
from typing import Any, Dict
from datetime import datetime
import sys
from pathlib import Path

from ollama_mcp_hub import (
    OllamaMCPHub,
    MemoryStore,
    SystemPromptManager
)

# Add MCP SDK (will need to install)
try:
    from mcp.server import Server
    from mcp.types import (
        Tool,
        TextContent,
        ToolResult,
        CallToolRequest,
    )
except ImportError:
    print("ERROR: MCP SDK not installed. Install with: pip install mcp")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")


class OllamaMCPServer:
    """MCP Protocol Server for Ollama"""

    def __init__(self, hub: OllamaMCPHub):
        self.hub = hub
        self.server = Server("ollama-mcp-hub")
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            tools = []
            for tool_def in self.hub.get_tools():
                tools.append(Tool(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    inputSchema=tool_def["inputSchema"]
                ))
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent | ToolResult]:
            """Execute a tool"""
            logger.info(f"Tool call: {name} with args: {arguments}")

            result = await self.hub.handle_tool_call(name, arguments)

            # Format result for MCP
            content = json.dumps(result, indent=2)

            if result.get("success"):
                return [TextContent(type="text", text=content)]
            else:
                return [ToolResult(
                    type="text",
                    text=content,
                    isError=True
                )]

    async def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server"""
        logger.info(f"Starting MCP server on {host}:{port}")

        # The server.run() method handles the protocol
        async with self.server:
            logger.info("MCP server ready")
            logger.info(f"Connect with: olcp --mcp-server http://{host}:{port} --model <model_name>")

            # Keep server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")


# ============================================================================
# HTTP/STDIO Bridge for olcp compatibility
# ============================================================================

async def run_stdio_server():
    """Run MCP server over stdio (standard way for local tools)"""
    hub = OllamaMCPHub()
    mcp_server = OllamaMCPServer(hub)

    # Setup handlers
    mcp_server._setup_handlers()

    logger.info("Ollama MCP Hub - Stdio mode")
    logger.info(f"Tools available: {len(hub.get_tools())}")

    # Run server (stdio mode is default)
    async with mcp_server.server:
        logger.info("Server ready on stdio")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass


async def run_http_server():
    """Run MCP server with HTTP transport"""
    import aiohttp
    from aiohttp import web

    hub = OllamaMCPHub()
    mcp_server = OllamaMCPServer(hub)

    async def handle_rpc(request):
        """Handle JSON-RPC requests"""
        try:
            data = await request.json()

            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")

            logger.info(f"RPC: {method}")

            # Handle different RPC methods
            if method == "tools/list":
                result = [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "inputSchema": t["inputSchema"]
                    }
                    for t in hub.get_tools()
                ]
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await hub.handle_tool_call(tool_name, arguments)
            elif method == "system/prompt":
                task_context = params.get("context", "")
                result = {"prompt": hub.get_system_prompt(task_context)}
            elif method == "memory/search":
                query = params.get("query", "")
                memories = hub.memory.search(query, top_k=5)
                result = {"memories": [m.__dict__ for m in memories]}
            else:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                })

            return web.json_response({
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            })

        except Exception as e:
            logger.error(f"RPC error: {e}", exc_info=True)
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": request_id
            }, status=500)

    # Create HTTP app
    app = web.Application()
    app.router.post("/rpc", handle_rpc)
    app.router.get("/health", lambda r: web.json_response({"status": "ok"}))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8000)
    await site.start()

    logger.info("="*60)
    logger.info("OLLAMA MCP HUB - HTTP Server")
    logger.info("="*60)
    logger.info(f"✓ Server running on http://127.0.0.1:8000")
    logger.info(f"✓ Tools available: {len(hub.get_tools())}")
    logger.info(f"✓ Memory persisted to: {hub.memory.db_path}")
    logger.info("="*60)
    logger.info("\nUsage:")
    logger.info("  olcp --mcp-server http://127.0.0.1:8000 --model <any_ollama_model>")
    logger.info("\nThen in olcp:")
    logger.info("  /model llama2        - Switch models (keeps context!)")
    logger.info("  /memory              - View memory stats")
    logger.info("\n" + "="*60 + "\n")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await runner.cleanup()


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # Use stdio mode (MCP default)
        await run_stdio_server()
    else:
        # Use HTTP mode (for olcp compatibility)
        await run_http_server()


if __name__ == "__main__":
    asyncio.run(main())
