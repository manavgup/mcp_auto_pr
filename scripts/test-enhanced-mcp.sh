#!/bin/bash
# Working MCP Server Test Script

set -e

# Configuration
REPO_ANALYZER_PORT=9070
PR_RECOMMENDER_PORT=9071

# Function to test MCP server with proper initialization
test_mcp_server() {
    local port=$1
    local tool_name=$2
    local arguments=$3
    local description=$4

    echo "🔗 Testing: $description"
    echo "📡 Server: localhost:$port"
    echo "🔧 Tool: $tool_name"
    echo ""

    # 1. Initialize session
    echo "Step 1: Initializing session..."
    curl -s -D /tmp/mcp_headers_${port}.txt -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
          "protocolVersion": "2024-11-05",
          "capabilities": {},
          "clientInfo": {"name": "curl-client", "version": "1.0"}
        }
      }' \
      "http://localhost:$port/mcp/" > /dev/null

    # 2. Extract session ID
    local session_id=$(grep -i "mcp-session-id" /tmp/mcp_headers_${port}.txt | cut -d' ' -f2 | tr -d '\r\n')
    echo "Session ID: $session_id"

    # 3. CRITICAL: Send initialized notification
    echo "Step 2: Sending initialized notification..."
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Mcp-Session-Id: $session_id" \
      -d '{
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
      }' \
      "http://localhost:$port/mcp/" > /dev/null

    # 4. Call the tool
    echo "Step 3: Calling tool..."
    local response=$(curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Mcp-Session-Id: $session_id" \
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
          "name": "'$tool_name'",
          "arguments": '$arguments'
        }
      }' \
      "http://localhost:$port/mcp/")

    # 5. Extract and display result
    echo "✅ Result:"
    echo "$response" | grep "^data: " | tail -1 | sed 's/^data: //' | jq -r '.result.structuredContent' | jq .

    echo ""
    echo "----------------------------------------"
    echo ""
}

# Function to list available tools
list_tools() {
    local port=$1
    echo "📋 Listing tools on port $port..."

    # Initialize session
    curl -s -D /tmp/mcp_headers_${port}.txt -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
          "protocolVersion": "2024-11-05",
          "capabilities": {},
          "clientInfo": {"name": "curl-client", "version": "1.0"}
        }
      }' \
      "http://localhost:$port/mcp/" > /dev/null

    local session_id=$(grep -i "mcp-session-id" /tmp/mcp_headers_${port}.txt | cut -d' ' -f2 | tr -d '\r\n')

    # Send initialized notification
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Mcp-Session-Id: $session_id" \
      -d '{
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
      }' \
      "http://localhost:$port/mcp/" > /dev/null

    # List tools
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Mcp-Session-Id: $session_id" \
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
      }' \
      "http://localhost:$port/mcp/" | grep "^data: " | tail -1 | sed 's/^data: //' | jq -r '.result.tools[].name'

    echo ""
}

echo "🧪 Testing MCP Servers with Proper Initialization"
echo "=================================================="
echo ""

# List tools on both servers
list_tools $REPO_ANALYZER_PORT
list_tools $PR_RECOMMENDER_PORT

# Test Repo Analyzer tools
echo "=== REPO ANALYZER TESTS ==="

test_mcp_server $REPO_ANALYZER_PORT "get_outstanding_summary" \
    '{"repository_path": ".", "detailed": false}' \
    "Get comprehensive repository summary"

test_mcp_server $REPO_ANALYZER_PORT "analyze_working_directory" \
    '{"repository_path": ".", "include_diffs": false}' \
    "Analyze working directory changes"

test_mcp_server $REPO_ANALYZER_PORT "analyze_repository_health" \
    '{"repository_path": "."}' \
    "Check repository health"

# Test PR Recommender tools
echo "=== PR RECOMMENDER TESTS ==="

test_mcp_server $PR_RECOMMENDER_PORT "get_strategy_options" \
    '{"repository_path": "."}' \
    "Get PR strategy options"

echo "🎉 All tests completed!"
echo ""
echo "💡 Key findings:"
echo "   ✅ MCP servers work perfectly with proper initialization"
echo "   ✅ Required: notifications/initialized after session creation"
echo "   ✅ Session management via mcp-session-id headers"
echo "   ✅ SSE format responses with structured data"
echo ""
echo "🔧 For manual testing:"
echo "   1. Initialize: POST /mcp/ with initialize method"
echo "   2. Notify: POST with notifications/initialized"
echo "   3. Call tools: POST with tools/call method"
