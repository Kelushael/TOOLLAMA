# Contributing to Ollama MCP Hub

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/ollama-mcp-hub.git
cd ollama-mcp-hub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Testing

Run the test suite:

```bash
# Unit tests
python3 tests/test_tool_executor.py

# End-to-end tests
python3 tests/e2e_test.py

# Live integration tests
bash tests/live_test.sh
```

All tests must pass before submitting a PR.

## Making Changes

1. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test them:
   ```bash
   # Run tests frequently during development
   python3 tests/test_tool_executor.py
   ```

3. **Add tests** for new functionality

4. **Update documentation** if needed:
   - README.md for user-facing changes
   - ARCHITECTURE.md for structural changes
   - Code comments for complex logic

5. **Commit with clear messages**:
   ```bash
   git commit -m "Add: Brief description of your change"
   ```

## Code Style

- Use Python 3.8+ syntax
- Follow PEP 8 conventions
- Add docstrings to functions
- Keep functions focused and testable

## Types of Contributions

### New Tools
To add a new tool to the system:

1. Add a method in `ToolExecutor._load_tools()` with the tool schema
2. Implement the tool method (e.g., `_my_tool()`)
3. Add tests to `tests/test_tool_executor.py`
4. Update documentation

### Bug Fixes
1. Include a test that reproduces the bug
2. Fix the code
3. Verify the test passes

### Documentation
- README improvements
- Clarifications in existing docs
- New examples or tutorials

## Reporting Issues

Use GitHub Issues with:
- Clear title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version, Ollama version)

## Questions?

Open a discussion or issue. We're here to help!
