# 🚀 MCP Auto PR Monorepo - Development Guide

This is the consolidated monorepo for the MCP Auto PR project. All components have been unified into a single repository for easier development and maintenance.

## 🏗️ Project Structure

```
mcp_auto_pr/                    # Monorepo root
├── src/                        # Source code
│   ├── shared/                 # Shared utilities and models
│   ├── mcp_local_repo_analyzer/  # Git analysis engine
│   └── mcp_pr_recommender/     # AI-powered PR recommendations
├── tests/                      # Test suite
│   └── unit/                   # Unit tests
├── .vscode/                    # VSCode configuration
├── Makefile                    # Development commands
├── pyproject.toml              # Python dependencies
└── mcp_auto_pr.code-workspace  # VSCode workspace file
```

## 🛠️ Quick Start

### 1. Open the Project

**Option A: VSCode/Cursor Workspace (Recommended)**
```bash
# Open the workspace file
code mcp_auto_pr.code-workspace
# or
cursor mcp_auto_pr.code-workspace
```

**Option B: Direct Directory**
```bash
# Open the directory directly
code .
# or
cursor .
```

### 2. Set Up Environment

```bash
# Install dependencies
make install

# Activate virtual environment (if not auto-activated)
source .venv/bin/activate
```

### 3. Verify Setup

```bash
# Run linting
make lint

# Run formatting
make format

# Run tests
make test-unit

# Run all quality checks
make quality-check
```

## 🧪 Testing

### Available Test Commands

```bash
make test-unit          # Run unit tests only
make test-integration   # Run integration tests
make test-all          # Run all tests
make test-fast         # Run fast tests only
make test-coverage     # Run tests with coverage
```

### Test Structure

- `tests/unit/` - Unit tests for individual components
- Tests use pytest with markers (`@pytest.mark.unit`)
- Import tests relatively: `from .utils.factories import ...`

## 🔍 Code Quality

### Available Quality Commands

```bash
make lint              # Run ruff linting
make format           # Format code with black
make type-check       # Run mypy type checking
make quality-check    # Run all quality checks
```

### Linting Configuration

- **Ruff**: Fast Python linter (configured in `pyproject.toml`)
- **Black**: Code formatter (88 character line length)
- **MyPy**: Type checker (configured in `mypy.ini`)

## 📁 VSCode/Cursor Configuration

The monorepo includes optimized IDE configuration:

### Automatic Features
- ✅ **Python Path**: `./src` automatically added
- ✅ **Virtual Environment**: Auto-activated
- ✅ **Format on Save**: Black formatting
- ✅ **Import Organization**: Automatic import sorting
- ✅ **Test Discovery**: Pytest integration
- ✅ **Linting**: Real-time ruff and mypy feedback

### Available Tasks (Ctrl/Cmd+Shift+P → "Tasks: Run Task")
- Run Unit Tests
- Run All Tests
- Lint Code
- Format Code
- Quality Check
- Install Dependencies

### Debug Configurations (F5)
- Python: Current File
- Run Unit Tests
- Local Repo Analyzer Server
- PR Recommender Server

## 🏃‍♂️ Common Workflows

### Development Workflow
```bash
# 1. Make changes
# 2. Format and lint
make format
make lint

# 3. Run tests
make test-unit

# 4. Full quality check before commit
make quality-check
```

### Adding New Tests
```bash
# Create test file in tests/unit/
# Use relative imports: from .utils.factories import ...
# Mark with @pytest.mark.unit
# Run specific test:
poetry run pytest tests/unit/test_your_file.py -v
```

### Running Servers
```bash
# Local Repo Analyzer
python src/mcp_local_repo_analyzer/main.py

# PR Recommender (requires OPENAI_API_KEY)
export OPENAI_API_KEY=your_key_here
python src/mcp_pr_recommender/main.py
```

## 🔧 Troubleshooting

### Import Issues
- Ensure you're in the `mcp_auto_pr/` directory
- Check that `PYTHONPATH=src` is set
- Use relative imports in tests: `from .utils.factories import ...`

### Test Issues
- Run from monorepo root: `cd mcp_auto_pr && make test-unit`
- Check virtual environment is activated
- Verify pytest markers are registered in `pytest.ini`

### Linting Issues
- Format first: `make format`
- Then lint: `make lint`
- Check MyPy separately: `make type-check`

## 📋 Available Make Targets

```bash
make help              # Show all available targets
make install           # Install dependencies
make test-all          # Run all tests
make test-unit         # Run unit tests
make test-integration  # Run integration tests
make test-fast         # Run fast tests
make test-coverage     # Run with coverage
make lint              # Run linting
make format            # Format code
make type-check        # Type checking
make quality-check     # All quality checks
make clean             # Clean build artifacts
```

## 🎯 Next Steps

This monorepo is ready for development! The test infrastructure, linting, and IDE integration are all configured and working. You can now focus on:

1. **Development**: Write code with full IDE support
2. **Testing**: Comprehensive test suite with easy execution
3. **Quality**: Automated formatting and linting
4. **Debugging**: Full debug configuration for all components

Happy coding! 🚀
