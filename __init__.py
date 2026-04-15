"""
Ollama MCP Hub - Universal Developer Agent for Local Models

This package integrates the Model Context Protocol (MCP) with Ollama,
enabling any local model to act as a full-featured code assistant.

Quick start:
    python mcp_server.py
    # In another terminal:
    olcp --mcp-server http://127.0.0.1:8000 --model qwen:7b
"""

from .ollama_mcp_hub import (
    OllamaMCPHub,
    MemoryStore,
    Memory,
    SystemPromptManager,
    ToolExecutor,
)

__version__ = "0.1.0"
__all__ = [
    "OllamaMCPHub",
    "MemoryStore",
    "Memory",
    "SystemPromptManager",
    "ToolExecutor",
]
