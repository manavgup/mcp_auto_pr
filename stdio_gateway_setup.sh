#!/bin/bash

# MCP Gateway Registration for stdio-based MCP Servers

set -e

# Configuration
GATEWAY_URL="http://localhost:4444"
JWT_SECRET="my-secret-key"

echo "🚀 Setting up MCP Gateway integration for stdio servers..."

# Generate JWT token
echo "🔑 Generating authentication token..."
JWT_TOKEN=$(docker exec mcpgateway python3 -m mcpgateway.utils.create_jwt_token \
  --username admin \
  --exp 10080 \
  --secret ${JWT_SECRET})

if [ -z "$JWT_TOKEN" ]; then
    echo "❌ Failed to generate JWT token"
    exit 1
fi

export MCPGATEWAY_BEARER_TOKEN="$JWT_TOKEN"
echo "✅ JWT token generated: ${JWT_TOKEN:0:20}..."

# Health check gateway
echo "🏥 Checking gateway health..."
if curl -s -f -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
   "${GATEWAY_URL}/health" > /dev/null; then
    echo "✅ Gateway is healthy"
else
    echo "❌ Gateway health check failed"
    exit 1
fi

# For stdio servers, we need to register them as "virtual servers" 
# that the gateway can manage through the wrapper

echo "📊 Registering Local Repository Analyzer as virtual server..."
curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "local_repo_analyzer",
    "description": "Local Git repository analysis and change detection",
    "command": "poetry",
    "args": ["run", "local-git-analyzer"],
    "cwd": "/workspace/mcp_local_repo_analyzer",
    "env": {
      "PYTHONPATH": "src",
      "LOG_LEVEL": "INFO"
    },
    "transport": "stdio",
    "metadata": {
      "version": "0.1.0",
      "capabilities": ["analyze_repository", "detect_changes", "git_analysis"],
      "category": "development"
    }
  }' \
  "${GATEWAY_URL}/servers" && echo "✅ Analyzer registered" || echo "⚠️ Analyzer registration failed"

echo "🎯 Registering PR Recommender as virtual server..."
curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pr_recommender", 
    "description": "Pull request recommendation and strategy engine",
    "command": "poetry",
    "args": ["run", "pr-recommender"],
    "cwd": "/workspace/mcp_pr_recommender",
    "env": {
      "PYTHONPATH": "src",
      "LOG_LEVEL": "INFO",
      "OPENAI_API_KEY": "'${OPENAI_API_KEY}'"
    },
    "transport": "stdio",
    "metadata": {
      "version": "0.1.0", 
      "capabilities": ["recommend_pr_strategy", "analyze_changes", "group_commits"],
      "category": "development"
    }
  }' \
  "${GATEWAY_URL}/servers" && echo "✅ Recommender registered" || echo "⚠️ Recommender registration failed"

# List registered servers
echo ""
echo "📋 Listing registered servers..."
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  "${GATEWAY_URL}/servers" | jq '.[].name' 2>/dev/null || \
  curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "${GATEWAY_URL}/servers"

echo ""
echo "✅ Gateway setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Check servers: curl -H 'Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN' ${GATEWAY_URL}/servers"
echo "  2. Access Admin UI: ${GATEWAY_URL}/admin (admin/changeme)"
echo "  3. View API docs: ${GATEWAY_URL}/docs"
echo ""
echo "🔐 Your JWT token: $JWT_TOKEN"
echo ""
echo "🧪 Test server communication through gateway:"
echo "curl -X POST -H 'Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}' \\"
echo "  ${GATEWAY_URL}/rpc"
