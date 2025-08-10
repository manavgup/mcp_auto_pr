# Phase 2: CI/CD Setup (Days 3-4)

## Objectives
- Create unified CI/CD pipeline
- Set up automated testing
- Configure Docker image building
- Implement security scanning

## Day 3: GitHub Actions Setup

### Main CI Pipeline (.github/workflows/ci.yml)
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

env:
  PYTHON_VERSION: '3.11'
  POETRY_VERSION: '1.7.1'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}
      - run: poetry install --with dev
      - run: poetry run ruff check src/ tests/
      - run: poetry run mypy src/
      - run: poetry run black --check src/ tests/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: snok/install-poetry@v1
      - run: poetry install --with test
      - run: poetry run pytest tests/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
      - uses: github/super-linter@v5
        env:
          DEFAULT_BRANCH: main
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Docker Build Pipeline (.github/workflows/docker.yml)
```yaml
name: Docker Build & Push

on:
  push:
    tags:
      - 'v*'
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [analyzer, recommender]
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - uses: docker/setup-buildx-action@v3
      
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/mcp-${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/${{ matrix.service }}/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Day 4: Release Automation

### Release Workflow (.github/workflows/release.yml)
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  publish-pypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: snok/install-poetry@v1
      
      - name: Build packages
        run: |
          poetry build
          
      - name: Publish to PyPI
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: |
          poetry publish
```

### Pre-commit CI (.github/workflows/pre-commit.yml)
```yaml
name: Pre-commit

on:
  pull_request:
  push:
    branches: [main]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: pre-commit/action@v3.0.0
```

## Docker Configuration

### Analyzer Dockerfile (docker/analyzer/Dockerfile)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY src/mcp_shared_lib /app/src/mcp_shared_lib
COPY src/mcp_local_repo_analyzer /app/src/mcp_local_repo_analyzer
COPY pyproject.toml poetry.lock /app/

# Install Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Run as non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

EXPOSE 9070

ENTRYPOINT ["python", "-m", "mcp_local_repo_analyzer.main"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "9070"]
```

### Docker Compose (docker-compose.yml)
```yaml
version: '3.8'

services:
  analyzer:
    build:
      context: .
      dockerfile: docker/analyzer/Dockerfile
    image: ghcr.io/manavgup/mcp-local-repo-analyzer:latest
    ports:
      - "9070:9070"
    volumes:
      - ./repos:/repos:ro
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9070/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  recommender:
    build:
      context: .
      dockerfile: docker/recommender/Dockerfile
    image: ghcr.io/manavgup/mcp-pr-recommender:latest
    ports:
      - "9071:9071"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9071/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - analyzer
```

## Security Configuration

### Dependabot (.github/dependabot.yml)
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    
  - package-ecosystem: "docker"
    directory: "/docker/analyzer"
    schedule:
      interval: "weekly"
      
  - package-ecosystem: "docker"
    directory: "/docker/recommender"
    schedule:
      interval: "weekly"
      
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Security Policy (SECURITY.md)
```markdown
# Security Policy

## Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability
Please report vulnerabilities to manavg@gmail.com
```

## Checklist

### GitHub Actions
- [ ] Created main CI pipeline
- [ ] Set up Docker build workflow
- [ ] Configured release automation
- [ ] Added pre-commit CI
- [ ] Set up security scanning

### Docker
- [ ] Created Dockerfiles for each service
- [ ] Configured docker-compose.yml
- [ ] Added health checks
- [ ] Implemented multi-platform builds
- [ ] Set up Docker image caching

### Security
- [ ] Configured Dependabot
- [ ] Added security scanning
- [ ] Created security policy
- [ ] Set up secret scanning
- [ ] Configured CODEOWNERS

### Monitoring
- [ ] Added code coverage reporting
- [ ] Set up test result reporting
- [ ] Configured build status badges
- [ ] Added performance benchmarks

## Verification

### Test CI Pipeline
```bash
# Run locally with act
act -j lint
act -j test
act -j security
```

### Test Docker Builds
```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# Check health
docker-compose ps
curl http://localhost:9070/health
curl http://localhost:9071/health
```

## Next Steps
- Proceed to [Phase 3: Test Implementation](./07-phase3-testing.md)
- Monitor first CI runs
- Address any failing checks