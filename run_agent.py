#!/usr/bin/env python3
"""
SIMPLIFIED: Ollama Agent with Tools - One Command to Rule Them All

Usage:
    python3 run_agent.py qwen:7b
    python3 run_agent.py llama2
    python3 run_agent.py mistral:7b

Works with ANY Ollama model. Just run!
"""

import asyncio
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Setup paths
DB_PATH = Path("./data/ollama_memory.db")
DB_PATH.parent.mkdir(exist_ok=True)

# Import from hub
from ollama_mcp_hub import OllamaMCPHub, MemoryStore, SystemPromptManager


class OllamaAgent:
    """Direct Ollama integration - no bridges, no complexity"""

    def __init__(self, model: str):
        self.model = model
        self.hub = OllamaMCPHub()
        self.memory = self.hub.memory
        self.executor = self.hub.executor
        self.conversation = []

        print(f"\n{'='*70}")
        print(f"OLLAMA LOCAL AGENT - {model.upper()}")
        print(f"{'='*70}")
        print(f"✓ Model: {model}")
        print(f"✓ Memory: {self.memory.db_path}")
        print(f"✓ Tools: {len(self.executor.get_tools())}")
        print(f"\nType 'help' for commands, 'exit' to quit\n{'='*70}\n")

    def get_system_prompt(self):
        """Get system prompt with memory context"""
        if self.conversation:
            last_message = self.conversation[-1].get("content", "")
            context = self.memory.get_context(last_message[:200])
        else:
            context = ""

        return SystemPromptManager.build(context)

    def call_ollama(self, user_input: str) -> str:
        """Call Ollama with tool support"""
        # Build messages
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        messages.extend(self.conversation)
        messages.append({"role": "user", "content": user_input})

        # Call ollama
        try:
            cmd = ["ollama", "run", self.model]

            # Use stdin to send the conversation
            json_data = json.dumps({"messages": messages, "stream": True})

            # Actually, ollamda run doesn't support JSON input directly
            # So we'll use the REST API instead
            import urllib.request
            import json

            api_url = "http://localhost:11434/api/chat"

            request_data = json.dumps({
                "model": self.model,
                "messages": messages,
                "stream": False
            }).encode('utf-8')

            req = urllib.request.Request(
                api_url,
                data=request_data,
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data.get("message", {}).get("content", "")

        except Exception as e:
            return f"Error calling Ollama: {e}\n\nMake sure Ollama is running: ollama serve"

    def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool"""
        asyncio.run(self.executor.execute(tool_name, args))
        result = asyncio.run(self.executor.execute(tool_name, args))
        return json.dumps(result, indent=2)

    def parse_tool_calls(self, response: str) -> list:
        """Extract tool calls from response"""
        import re
        tool_calls = []
        pattern = r'<tool_use>\s*({.*?})\s*</tool_use>'
        for match in re.finditer(pattern, response, re.DOTALL):
            try:
                tool_call = json.loads(match.group(1))
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                pass
        return tool_calls

    async def process_input(self, user_input: str):
        """Process user input through agent loop"""
        # Save to conversation
        self.conversation.append({"role": "user", "content": user_input})
        self.memory.save("user_input", user_input[:200], tags=["input"])

        # Get response from ollama
        print("🤔 Thinking...")
        response = self.call_ollama(user_input)

        # Check for tool calls
        tool_calls = self.parse_tool_calls(response)

        if tool_calls:
            print(f"\n🔧 Using tools...\n")
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                args = tool_call.get("input", {})

                print(f"  [{tool_name}]")
                result = await self.executor.execute(tool_name, args)

                # Log execution
                self.memory.log_tool_execution(
                    tool_name, args, result, result.get("success", False)
                )

                # Show result
                if result.get("success"):
                    output = result.get("stdout", str(result))[:200]
                    print(f"    ✓ {output}")
                else:
                    print(f"    ✗ {result.get('error', 'Unknown error')}")

        # Add to conversation
        self.conversation.append({"role": "assistant", "content": response})

        # Display response
        print(f"\n{response}\n")

    def handle_command(self, cmd: str):
        """Handle special commands"""
        if cmd == "help":
            print("""
Commands:
  /model <name>    - Switch models (e.g., /model llama2)
  /memory          - Show memory stats
  /search <query>  - Search memories
  /tools           - List available tools
  /exit            - Exit
  /clear           - Clear conversation
""")
        elif cmd.startswith("/model "):
            new_model = cmd[7:].strip()
            self.model = new_model
            print(f"✓ Switched to {new_model} (memory preserved)")
        elif cmd == "/memory":
            stats = self.memory.get_stats()
            print(f"\n📚 Memory Stats:")
            print(f"   Memories: {stats['total_memories']}")
            print(f"   Executions: {stats['total_executions']}")
            print(f"   Categories: {stats['categories']}\n")
        elif cmd.startswith("/search "):
            query = cmd[8:].strip()
            results = self.memory.search(query, top_k=3)
            if results:
                print(f"\n🔍 Found {len(results)} memories:")
                for mem in results:
                    print(f"   - [{mem.category}] {mem.content[:100]}")
                print()
            else:
                print("No memories found.\n")
        elif cmd == "/tools":
            print("\n🔧 Available Tools:")
            for tool in self.executor.get_tools():
                print(f"   - {tool['name']}: {tool['description']}")
            print()
        elif cmd == "/exit":
            return False
        elif cmd == "/clear":
            self.conversation = []
            print("✓ Conversation cleared\n")
        else:
            print("Unknown command. Type 'help' for commands.\n")
        return True

    async def run(self):
        """Main REPL loop"""
        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Process with agent
                await self.process_input(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 run_agent.py <model>")
        print("Example: python3 run_agent.py qwen:7b")
        print("\nAvailable models (run 'ollama pull <model>'):")
        print("  - qwen:7b (recommended)")
        print("  - llama2:7b")
        print("  - mistral:7b")
        print("  - neural-chat:7b")
        sys.exit(1)

    model = sys.argv[1]

    # Check if ollama is running
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags")
    except Exception as e:
        print(f"❌ Ollama is not running!")
        print(f"\nStart Ollama with: ollama serve")
        sys.exit(1)

    agent = OllamaAgent(model)
    await agent.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
