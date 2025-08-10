# Command Reference

## Quick Reference
Common commands for development, testing, and deployment.

## Development Commands

### Setup
```bash
# Initial setup
make install-all
make dev-setup

# Install dependencies
poetry install --with dev,test

# Update dependencies
poetry update
poetry lock --no-update

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Code Quality
```bash
# Format code
make format
poetry run black src/ tests/
poetry run ruff check --fix src/ tests/

# Lint code
make lint
poetry run ruff check src/ tests/
poetry run mypy src/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
pre-commit autoupdate
```

## Testing Commands

### Run Tests
```bash
# All tests
make test-all
poetry run pytest tests/

# Unit tests only
make test-unit
poetry run pytest tests/unit/

# Integration tests
make test-integration
poetry run pytest tests/integration/

# Specific package tests
poetry run pytest tests/unit/test_local_repo_analyzer/
poetry run pytest tests/unit/test_pr_recommender/

# With coverage
poetry run pytest --cov=src --cov-report=term-missing
poetry run pytest --cov=src --cov-report=html
poetry run pytest --cov=src --cov-fail-under=90

# Parallel execution
poetry run pytest -n auto

# Verbose output
poetry run pytest -vv

# Stop on first failure
poetry run pytest -x

# Run specific test
poetry run pytest tests/unit/test_cli.py::test_specific_function
```

### Coverage Reports
```bash
# Generate HTML coverage report
poetry run coverage html
open htmlcov/index.html

# Generate XML for CI
poetry run coverage xml

# Show coverage in terminal
poetry run coverage report

# Generate coverage badge
poetry run coverage-badge -o coverage.svg
```

## Building and Publishing

### Build Packages
```bash
# Build all packages
make build-all

# Build with Poetry
poetry build
poetry build -f wheel
poetry build -f sdist

# Clean build artifacts
rm -rf dist/ build/ *.egg-info
```

### Publishing
```bash
# Configure PyPI credentials
poetry config pypi-token.pypi <token>

# Publish to TestPyPI
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi

# Publish to PyPI
poetry publish

# Dry run (no actual upload)
poetry publish --dry-run
```

## Docker Commands

### Build Images
```bash
# Build all images
make docker-build-all
docker-compose build

# Build specific service
docker-compose build analyzer
docker-compose build recommender

# Build with no cache
docker-compose build --no-cache

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 .
```

### Run Services
```bash
# Start all services
make docker-up
docker-compose up -d

# Start specific service
docker-compose up -d analyzer

# View logs
docker-compose logs -f
docker-compose logs analyzer

# Stop services
docker-compose down
docker-compose down -v  # Remove volumes

# Check status
docker-compose ps
docker-compose exec analyzer sh
```

### Docker Registry
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag images
docker tag mcp-analyzer:latest ghcr.io/manavgup/mcp-analyzer:latest

# Push images
docker push ghcr.io/manavgup/mcp-analyzer:latest
docker push ghcr.io/manavgup/mcp-analyzer:v0.2.0

# Pull images
docker pull ghcr.io/manavgup/mcp-analyzer:latest
```

## Git Commands

### Version Management
```bash
# Create and push tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Delete tag
git tag -d v0.2.0
git push origin --delete v0.2.0

# List tags
git tag -l
git tag -l "v0.2.*"
```

### Branch Management
```bash
# Create feature branch
git checkout -b feature/monorepo-migration

# Push branch
git push -u origin feature/monorepo-migration

# Merge branch
git checkout main
git merge feature/monorepo-migration

# Delete branch
git branch -d feature/monorepo-migration
git push origin --delete feature/monorepo-migration
```

## MCP Server Commands

### Local Repository Analyzer
```bash
# Run in stdio mode (default)
poetry run python -m mcp_local_repo_analyzer.main

# Run with HTTP transport
poetry run python -m mcp_local_repo_analyzer.main \
  --transport http --port 9070

# Run with WebSocket
poetry run python -m mcp_local_repo_analyzer.main \
  --transport websocket --port 9070

# With custom config
poetry run python -m mcp_local_repo_analyzer.main \
  --config config/analyzer.yaml
```

### PR Recommender
```bash
# Set OpenAI API key
export OPENAI_API_KEY=your_key_here

# Run server
poetry run python -m mcp_pr_recommender.main

# With HTTP transport
poetry run python -m mcp_pr_recommender.main \
  --transport http --port 9071

# Debug mode
poetry run python -m mcp_pr_recommender.main \
  --log-level DEBUG
```

## Utility Commands

### Clean Up
```bash
# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove build artifacts
rm -rf dist/ build/ *.egg-info
rm -rf htmlcov/ .coverage coverage.xml

# Remove test artifacts
rm -rf .pytest_cache/ .tox/ .mypy_cache/

# Full clean
make clean-all
```

### Environment Variables
```bash
# Set environment variables
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=9070
export LOG_LEVEL=DEBUG
export OPENAI_API_KEY=sk-...

# Load from .env file
source .env
python -m dotenv run -- python script.py
```

### Debug Commands
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check installed packages
pip list
poetry show

# Check import
python -c "import mcp_local_repo_analyzer; print(mcp_local_repo_analyzer.__file__)"

# Run with debugger
python -m pdb -m mcp_local_repo_analyzer.main

# Profile performance
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats
```

## CI/CD Commands

### GitHub Actions (Local)
```bash
# Install act
brew install act  # macOS
# or download from https://github.com/nektos/act

# Run workflows locally
act -j lint
act -j test
act -j build

# With specific event
act pull_request
act push -b main
```

### Pre-commit
```bash
# Install hooks
pre-commit install
pre-commit install --hook-type commit-msg

# Run manually
pre-commit run --all-files
pre-commit run black --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks (use sparingly)
git commit --no-verify
```

## Makefile Targets

### Common Targets
```bash
make help          # Show available commands
make install       # Install dependencies
make test          # Run all tests
make lint          # Run linting
make format        # Format code
make build         # Build packages
make clean         # Clean artifacts
make docker-up     # Start Docker services
make docker-down   # Stop Docker services
```

### Custom Targets
```bash
make test-coverage      # Run tests with coverage
make test-watch        # Run tests in watch mode
make serve-analyzer    # Start analyzer server
make serve-recommender # Start recommender server
make check-security    # Run security checks
make update-deps       # Update all dependencies
```

## Troubleshooting Commands

### Dependency Issues
```bash
# Clear Poetry cache
poetry cache clear --all pypi

# Reinstall dependencies
poetry install --remove-untracked

# Check for conflicts
poetry check
pip check
```

### Import Issues
```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check module location
python -c "import mcp_shared_lib; print(mcp_shared_lib.__file__)"
```

### Performance
```bash
# Memory profiling
python -m memory_profiler script.py

# Time execution
time python script.py

# Profile with py-spy
py-spy record -o profile.svg -- python script.py
```