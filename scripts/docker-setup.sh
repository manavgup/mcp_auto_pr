#!/bin/bash
set -e

echo "🐳 Setting up MCP Servers with Docker (Poetry-First)..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if we're in the right directory and workspace exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the mcp_auto_pr directory"
    exit 1
fi

# Check if the server directories exist
if [ ! -d "../mcp_local_repo_analyzer" ]; then
    echo "❌ mcp_local_repo_analyzer directory not found at ../mcp_local_repo_analyzer"
    echo "💡 Make sure you've run the main setup.sh to clone all repositories"
    exit 1
fi

if [ ! -d "../mcp_pr_recommender" ]; then
    echo "❌ mcp_pr_recommender directory not found at ../mcp_pr_recommender"
    echo "💡 Make sure you've run the main setup.sh to clone all repositories"
    exit 1
fi

# Verify Poetry files exist
if [ ! -f "../mcp_local_repo_analyzer/pyproject.toml" ]; then
    echo "❌ pyproject.toml not found in mcp_local_repo_analyzer"
    exit 1
fi

if [ ! -f "../mcp_pr_recommender/pyproject.toml" ]; then
    echo "❌ pyproject.toml not found in mcp_pr_recommender"
    exit 1
fi

# Generate .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual API keys and paths"
    echo "   - Set OPENAI_API_KEY for PR recommender"
    echo "   - Set WORKSPACE_DIR to your code workspace path"
fi

# Build the Docker images (this will use Poetry)
echo "🏗️  Building MCP server images with Poetry..."
echo "   📊 Building repo analyzer..."
docker-compose build mcp-repo-analyzer

echo "   🎯 Building PR recommender..."
docker-compose build mcp-pr-recommender

# Start the services
echo "🚀 Starting MCP servers..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
./scripts/health-check.sh

echo "✅ MCP Servers are ready!"
echo ""
echo "📊 Local Repo Analyzer: http://localhost:9070"
echo "🎯 PR Recommender: http://localhost:9071"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your API keys: nano .env"
echo "   2. Restart if needed: docker-compose restart"
echo "   3. Test the servers: ./scripts/test-servers.sh"
echo "   4. Connect to Claude: see docker/docs/claude-integration.md"
echo "   5. Connect to VSCode: see docker/docs/vscode-integration.md"
echo "   6. Connect to MCP Gateway: see docker/docs/gateway-integration.md"
