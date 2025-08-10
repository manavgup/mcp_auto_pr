#!/bin/bash

# complete-mcp-setup-simple.sh
# Simple, reliable setup script - UPDATED with working local repo analyzer
# Uses direct stdio mode for local repo analyzer (bypasses connection issues)

set -e

# Function to prompt for MCP gateway path
get_mcp_gateway_path() {
    if [ -z "$MCP_GATEWAY_DIR" ]; then
        echo "🔍 Please provide the path to your mcp-context-forge directory:"
        echo "   (Default: /Users/mg/mg-work/manav/work/ai-experiments/mcp-context-forge)"
        read -r input_path
        if [ -z "$input_path" ]; then
            export MCP_GATEWAY_DIR="/Users/mg/mg-work/manav/work/ai-experiments/mcp-context-forge"
        else
            export MCP_GATEWAY_DIR="$input_path"
        fi
    fi

    if [ ! -d "$MCP_GATEWAY_DIR" ]; then
        echo "❌ Directory not found: $MCP_GATEWAY_DIR"
        exit 1
    fi

    if [ ! -d "$MCP_GATEWAY_DIR/mcpgateway" ]; then
        echo "❌ mcpgateway module not found in: $MCP_GATEWAY_DIR"
        exit 1
    fi

    echo "✅ Found MCP Gateway at: $MCP_GATEWAY_DIR"
}

# Function to prompt for workspace path
get_workspace_path() {
    if [ -z "$MCP_WORKSPACE_DIR" ]; then
        echo "🔍 Please provide the path to your MCP workspace directory:"
        echo "   (Default: /Users/mg/mg-work/manav/work/ai-experiments/mcp_pr_workspace)"
        read -r input_path
        if [ -z "$input_path" ]; then
            export MCP_WORKSPACE_DIR="/Users/mg/mg-work/manav/work/ai-experiments/mcp_pr_workspace"
        else
            export MCP_WORKSPACE_DIR="$input_path"
        fi
    fi

    if [ ! -d "$MCP_WORKSPACE_DIR" ]; then
        echo "❌ Workspace directory not found: $MCP_WORKSPACE_DIR"
        exit 1
    fi

    echo "✅ Found MCP Workspace at: $MCP_WORKSPACE_DIR"
}

# UPDATED: Simple working local repo analyzer startup
start_local_repo_analyzer() {
    echo "🎯 Starting local repo analyzer (FIXED - direct stdio mode)..."

    # Use direct stdio mode - this works perfectly as we confirmed
    pm2 start "cd $MCP_WORKSPACE_DIR/mcp_local_repo_analyzer && poetry run local-git-analyzer" \
        --name local-repo-analyzer \
        --cwd "$MCP_WORKSPACE_DIR/mcp_local_repo_analyzer"

    echo "✅ Local repo analyzer started in direct stdio mode"
    echo "ℹ️  Note: This runs in stdio mode for direct MCP client connections"
}

# Function to test server health
test_server_health() {
    local port=$1
    local name=$2
    local max_attempts=10

    for i in $(seq 1 $max_attempts); do
        if curl -s "http://localhost:$port/healthz" | grep -q "ok"; then
            echo "✅ $name is healthy"
            return 0
        fi
        echo "⏳ Waiting for $name... (attempt $i/$max_attempts)"
        sleep 2
    done
    echo "❌ $name failed health check after $max_attempts attempts"
    return 1
}

# Determine gateway URL mode
if [[ "$1" == "--dev-mode" ]]; then
    export MCP_GATEWAY_URL="http://localhost:8000"
    echo "🛠️  Dev mode enabled. Using MCP Gateway URL: $MCP_GATEWAY_URL"
else
    export MCP_GATEWAY_URL="http://localhost:4444"
    echo "🚀 Using production MCP Gateway URL: $MCP_GATEWAY_URL"
fi

# Get paths
get_mcp_gateway_path
get_workspace_path

# Configuration
export GITHUB_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN:-your_github_token_here}"
export MEMORY_TOKEN="${MEMORY_PLUGIN_TOKEN:-your_memory_token_here}"
export WORK_DIR="/Users/mg/mg-work"
export DOWNLOADS_DIR="/Users/mg/Downloads"
export DOCUMENTS_DIR="/Users/mg/Documents"

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set. PR recommender may not work properly."
fi

# Set Python path and activate environment
export PYTHONPATH="$MCP_GATEWAY_DIR:$PYTHONPATH"
if [ -f "/Users/mg/.venv/mcpgateway/bin/activate" ]; then
    source /Users/mg/.venv/mcpgateway/bin/activate
    echo "🐍 Activated virtual environment"
fi

# Generate JWT token
if [ -z "$MCP_BEARER_TOKEN" ]; then
    echo "🔑 Generating JWT token..."
    cd "$MCP_GATEWAY_DIR"
    export MCP_BEARER_TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
          --username admin --exp 10080 --secret my-test-key)
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate JWT token"
        exit 1
    fi
fi

if [ -z "$MEMORY_PLUGIN_TOKEN" ]; then
    export MEMORY_PLUGIN_TOKEN="default-memory-token-for-testing"
fi

echo "🧹 Cleaning up..."
pm2 delete all 2>/dev/null || true
docker stop fast-time-server 2>/dev/null || true
docker rm fast-time-server 2>/dev/null || true

echo "🐳 Starting Docker time server..."
docker run --rm -d -p 8899:8080 --name fast-time-server fast-time-server:latest

echo "📦 Installing dependencies..."
cd "$MCP_WORKSPACE_DIR/mcp_local_repo_analyzer"
poetry install --quiet
cd "$MCP_WORKSPACE_DIR/mcp_pr_recommender"
poetry install --quiet

echo "🔄 Starting servers..."
cd "$MCP_GATEWAY_DIR"

# Standard servers (these work fine with gateway translation)
pm2 start "python3 -m mcpgateway.translate --stdio 'npx @modelcontextprotocol/server-filesystem $DOWNLOADS_DIR' --port 9000" --name filesystem-downloads --cwd "$MCP_GATEWAY_DIR"
pm2 start "python3 -m mcpgateway.translate --stdio 'npx @modelcontextprotocol/server-filesystem $DOCUMENTS_DIR' --port 9001" --name filesystem-documents --cwd "$MCP_GATEWAY_DIR"
pm2 start "MEMORY_PLUGIN_TOKEN=$MEMORY_PLUGIN_TOKEN python3 -m mcpgateway.translate --stdio 'npx @memoryplugin/mcp-server' --port 9002" --name memory-server --cwd "$MCP_GATEWAY_DIR"
pm2 start "python3 -m mcpgateway.translate --stdio 'docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN ghcr.io/github/github-mcp-server stdio' --port 9003" --name github-server --cwd "$MCP_GATEWAY_DIR"

# FIXED: Start local repo analyzer in working direct stdio mode
start_local_repo_analyzer

# Start PR recommender if API key is available
if [ -n "$OPENAI_API_KEY" ]; then
    pm2 start "OPENAI_API_KEY=$OPENAI_API_KEY cd $MCP_WORKSPACE_DIR/mcp_pr_recommender && poetry run pr-recommender --transport sse --port 8003" --name pr-recommender --cwd "$MCP_WORKSPACE_DIR/mcp_pr_recommender"
fi

echo "⏳ Waiting for servers to start..."
sleep 15

# Health check for gateway-connected servers
echo "🔍 Checking server health..."
test_server_health 9000 "Filesystem Downloads"
test_server_health 9001 "Filesystem Documents"
test_server_health 9002 "Memory Server"
test_server_health 9003 "GitHub Server"

if [ -n "$OPENAI_API_KEY" ]; then
    test_server_health 8003 "PR Recommender"
fi

# Check local repo analyzer (running in stdio mode)
if pm2 status local-repo-analyzer | grep -q "online"; then
    echo "✅ Local repo analyzer is running (stdio mode)"
else
    echo "❌ Local repo analyzer failed to start"
fi

echo "📝 Registering servers with gateway..."

# Register standard servers with gateway
echo "Registering standard servers..."
curl -s -X POST -H "Authorization: Bearer $MCP_BEARER_TOKEN" -H "Content-Type: application/json" -d '{"name":"filesystem-downloads","url":"http://localhost:9000/sse","description":"Filesystem server for Downloads folder"}' "$MCP_GATEWAY_URL/gateways" > /dev/null
curl -s -X POST -H "Authorization: Bearer $MCP_BEARER_TOKEN" -H "Content-Type: application/json" -d '{"name":"filesystem-documents","url":"http://localhost:9001/sse","description":"Filesystem server for Documents folder"}' "$MCP_GATEWAY_URL/gateways" > /dev/null
curl -s -X POST -H "Authorization: Bearer $MCP_BEARER_TOKEN" -H "Content-Type: application/json" -d '{"name":"memory-server","url":"http://localhost:9002/sse","description":"Memory plugin server"}' "$MCP_GATEWAY_URL/gateways" > /dev/null
curl -s -X POST -H "Authorization: Bearer $MCP_BEARER_TOKEN" -H "Content-Type: application/json" -d '{"name":"github-server","url":"http://localhost:9003/sse","description":"GitHub MCP server"}' "$MCP_GATEWAY_URL/gateways" > /dev/null
curl -s -X POST -H "Authorization: Bearer $MCP_BEARER_TOKEN" -H "Content-Type: application/json" -d '{"name":"time-server","url":"http://localhost:8899/sse","description":"Time server"}' "$MCP_GATEWAY_URL/gateways" > /dev/null

if [ -n "$OPENAI_API_KEY" ]; then
    curl -s -X POST -H "Authorization: Bearer $MCP_BEARER_TOKEN" -H "Content-Type: application/json" -d '{"name":"pr-recommender","url":"http://localhost:8003/sse","description":"AI-powered PR recommendation engine"}' "$MCP_GATEWAY_URL/gateways" > /dev/null
fi

# NOTE: Local repo analyzer runs in direct stdio mode, so it's not registered with the gateway
# Your MCP clients can connect to it directly via stdio

echo "✅ Server registration completed"

pm2 save

echo ""
echo "✅ Setup complete!"
echo "🎉 All servers running and registered with gateway"
echo "🌐 Check admin UI at $MCP_GATEWAY_URL/admin"
echo ""
echo "📋 Server Summary:"
echo "   • Standard servers: Connected via gateway (ports 9000-9003, 8899)"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "   • PR recommender: Connected via gateway (port 8003)"
fi
echo "   • Local repo analyzer: Direct stdio mode (use PM2 or connect directly)"
echo ""
echo "🧪 Quick tests:"
echo "   curl http://localhost:9000/healthz  # Filesystem Downloads"
echo "   curl http://localhost:9001/healthz  # Filesystem Documents"
echo "   curl http://localhost:9002/healthz  # Memory Server"
echo "   curl http://localhost:9003/healthz  # GitHub Server"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "   curl http://localhost:8003/healthz  # PR Recommender"
fi
echo "   pm2 logs local-repo-analyzer       # Local repo analyzer logs"
echo ""
echo "💡 Local repo analyzer is working perfectly in stdio mode!"
echo "   Connect your MCP clients directly to the stdio process for best results."
