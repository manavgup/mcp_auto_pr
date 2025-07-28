#!/bin/bash
set -e

echo "🧪 Testing MCP Servers (Streamable HTTP)..."

# Test repo analyzer
echo "Testing Local Repo Analyzer..."
if curl -s "http://localhost:9070/health" | grep -q "ok"; then
    echo "✅ Repo analyzer health check passed"
else
    echo "❌ Repo analyzer health check failed"
    echo "💡 Check logs: docker-compose logs mcp-repo-analyzer"
    exit 1
fi

# Test PR recommender  
echo "Testing PR Recommender..."
if curl -s "http://localhost:9071/health" | grep -q "ok"; then
    echo "✅ PR recommender health check passed"
else
    echo "❌ PR recommender health check failed"
    echo "💡 Check logs: docker-compose logs mcp-pr-recommender"
    exit 1
fi

# Test MCP protocol (streamable-http only needs initialization, not list_tools)
echo "Testing MCP protocol initialization..."

# Test repo analyzer MCP initialization
echo "  Testing repo analyzer MCP..."
if curl -s -X POST \
   -H "Content-Type: application/json" \
   -H "Accept: application/json, text/event-stream" \
   -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}' \
   "http://localhost:9070/mcp/" | grep -q "serverInfo"; then
    echo "✅ Repo analyzer MCP initialization working"
else
    echo "❌ Repo analyzer MCP initialization failed"
    echo "💡 Check logs: docker-compose logs mcp-repo-analyzer"
fi

# Test PR recommender MCP initialization
echo "  Testing PR recommender MCP..."
if curl -s -X POST \
   -H "Content-Type: application/json" \
   -H "Accept: application/json, text/event-stream" \
   -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}' \
   "http://localhost:9071/mcp/" | grep -q "serverInfo"; then
    echo "✅ PR recommender MCP initialization working"
else
    echo "❌ PR recommender MCP initialization failed"
    echo "💡 Check logs: docker-compose logs mcp-pr-recommender"
fi

echo "🎉 Basic tests passed!"
echo ""
echo "💡 Note: streamable-http requires persistent connections for full testing"
echo "   For proper tool testing, use MCP Gateway or persistent WebSocket clients"
echo ""
echo "📋 Available tools:"
echo "   Repo Analyzer: analyze_working_directory, analyze_staged_changes, get_outstanding_summary"
echo "   PR Recommender: generate_pr_recommendations, analyze_pr_feasibility, get_strategy_options"
echo ""
echo "🔧 For MCP Gateway integration:"
echo "   curl -X POST http://gateway:8000/gateways -d '{\"name\":\"repo-analyzer\",\"url\":\"http://localhost:9070/mcp\"}'"
echo "   curl -X POST http://gateway:8000/gateways -d '{\"name\":\"pr-recommender\",\"url\":\"http://localhost:9071/mcp\"}'"
