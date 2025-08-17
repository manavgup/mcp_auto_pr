FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy package files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY README.md ./

# Configure Poetry: don't create virtual env, install production deps only
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi --no-root

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 9070

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:9070/health || exit 1

# Start the MCP server in HTTP mode
CMD ["poetry", "run", "python", "-m", "mcp_local_repo_analyzer.main", \
     "--transport", "streamable-http", "--port", "9070", "--host", "0.0.0.0"]
