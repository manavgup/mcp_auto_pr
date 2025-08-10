#!/bin/bash

# MCP Bridge Setup Script
# Creates HTTP/SSE bridges for stdio MCP servers using mcpgateway.translate

set -e

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🌉 Setting up MCP bridges for stdio servers..."

# Configuration
ANALYZER_PORT=9001
RECOMMENDER_PORT=9002
GATEWAY_URL="http://localhost:4444"
JWT_SECRET="my-secret-key"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Configuration:${NC}"
echo "  Analyzer Bridge Port: $ANALYZER_PORT"
echo "  Recommender Bridge Port: $RECOMMENDER_PORT"
echo "  Gateway URL: $GATEWAY_URL"
echo "  Workspace: $WORKSPACE_ROOT"
echo ""

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        echo "Please stop the service using port $port or choose a different port"
        return 1
    fi
    echo -e "${GREEN}✅ Port $port is available${NC}"
    return 0
}

# Check ports
echo -e "${YELLOW}🔍 Checking port availability...${NC}"
check_port $ANALYZER_PORT
check_port $RECOMMENDER_PORT

# Function to start bridge for analyzer
start_analyzer_bridge() {
    echo -e "${BLUE}🚀 Starting analyzer bridge on port $ANALYZER_PORT...${NC}"

    cd "$WORKSPACE_ROOT/mcp_local_repo_analyzer"

    # Start the bridge in background
    python3 -m mcpgateway.translate \
        --stdio "poetry run local-git-analyzer" \
        --port $ANALYZER_PORT \
        --cors "http://localhost:4444" "http://localhost:3000" "http://127.0.0.1:4444" \
        --logLevel info > analyzer_bridge.log 2>&1 &

    ANALYZER_PID=$!
    echo $ANALYZER_PID > analyzer_bridge.pid
    echo -e "${GREEN}✅ Analyzer bridge started (PID: $ANALYZER_PID)${NC}"
    echo "   Log: $WORKSPACE_ROOT/mcp_local_repo_analyzer/analyzer_bridge.log"
    echo "   SSE endpoint: http://localhost:$ANALYZER_PORT/sse"
    echo "   Message endpoint: http://localhost:$ANALYZER_PORT/message"
    echo "   Health check: http://localhost:$ANALYZER_PORT/healthz"
}

# Function to start bridge for recommender
start_recommender_bridge() {
    echo -e "${BLUE}🚀 Starting recommender bridge on port $RECOMMENDER_PORT...${NC}"

    cd "$WORKSPACE_ROOT/mcp_pr_recommender"

    # Check if .env file exists and has OPENAI_API_KEY
    if [ ! -f ".env" ] || ! grep -q "OPENAI_API_KEY" .env; then
        echo -e "${YELLOW}⚠️  No OPENAI_API_KEY found in .env file${NC}"
        if [ -n "$OPENAI_API_KEY" ]; then
            echo "Using OPENAI_API_KEY from environment"
        else
            echo -e "${RED}❌ OPENAI_API_KEY is required for PR recommender${NC}"
            echo "Please set it in environment or .env file"
            return 1
        fi
    fi

    # Start the bridge in background
    python3 -m mcpgateway.translate \
        --stdio "poetry run pr-recommender" \
        --port $RECOMMENDER_PORT \
        --cors "http://localhost:4444" "http://localhost:3000" "http://127.0.0.1:4444" \
        --logLevel info > recommender_bridge.log 2>&1 &

    RECOMMENDER_PID=$!
    echo $RECOMMENDER_PID > recommender_bridge.pid
    echo -e "${GREEN}✅ Recommender bridge started (PID: $RECOMMENDER_PID)${NC}"
    echo "   Log: $WORKSPACE_ROOT/mcp_pr_recommender/recommender_bridge.log"
    echo "   SSE endpoint: http://localhost:$RECOMMENDER_PORT/sse"
    echo "   Message endpoint: http://localhost:$RECOMMENDER_PORT/message"
    echo "   Health check: http://localhost:$RECOMMENDER_PORT/healthz"
}

# Function to test bridges
test_bridges() {
    echo -e "${YELLOW}🧪 Testing bridge endpoints...${NC}"

    sleep 3  # Give bridges time to start

    # Test analyzer bridge
    echo "Testing analyzer bridge health..."
    if curl -s -f "http://localhost:$ANALYZER_PORT/healthz" > /dev/null; then
        echo -e "${GREEN}✅ Analyzer bridge is healthy${NC}"
    else
        echo -e "${RED}❌ Analyzer bridge health check failed${NC}"
    fi

    # Test recommender bridge
    echo "Testing recommender bridge health..."
    if curl -s -f "http://localhost:$RECOMMENDER_PORT/healthz" > /dev/null; then
        echo -e "${GREEN}✅ Recommender bridge is healthy${NC}"
    else
        echo -e "${RED}❌ Recommender bridge health check failed${NC}"
    fi
}

# Function to register with gateway
register_with_gateway() {
    echo -e "${YELLOW}🔗 Registering bridges with MCP Gateway...${NC}"

    # Generate JWT token
    # Try docker exec first, fall back to docker run
    JWT_TOKEN=$(docker exec mcpgateway python3 -m mcpgateway.utils.create_jwt_token \
      --username admin \
      --exp 10080 \
      --secret ${JWT_SECRET} 2>/dev/null || \
      docker run --rm ghcr.io/ibm/mcp-context-forge:latest \
      python3 -m mcpgateway.utils.create_jwt_token -u admin --secret ${JWT_SECRET})

    if [ -z "$JWT_TOKEN" ]; then
        echo -e "${RED}❌ Failed to generate JWT token${NC}"
        echo "Make sure MCP Gateway is running: docker ps | grep mcpgateway"
        return 1
    fi

    export MCPGATEWAY_BEARER_TOKEN="$JWT_TOKEN"
    echo -e "${GREEN}✅ JWT token generated${NC}"

    # Register individual tools from analyzer
    echo "Registering analyzer tools..."

    # Analyze working directory tool
    curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "analyze_working_directory",
        "url": "http://localhost:'$ANALYZER_PORT'/message",
        "description": "Analyze uncommitted changes in working directory of a repository",
        "input_schema": {
          "type": "object",
          "properties": {
            "repo_path": {
              "type": "string",
              "description": "Path to the repository to analyze (required)"
            }
          },
          "required": ["repo_path"]
        },
        "metadata": {
          "source": "local_repo_analyzer",
          "bridge_port": '$ANALYZER_PORT',
          "sse_endpoint": "http://localhost:'$ANALYZER_PORT'/sse",
          "method": "analyze_working_directory"
        }
      }' \
      "${GATEWAY_URL}/tools" && echo -e "${GREEN}✅ Working directory analyzer registered${NC}" || echo -e "${RED}❌ Working directory analyzer registration failed${NC}"

    # Analyze staged changes tool
    curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "analyze_staged_changes",
        "url": "http://localhost:'$ANALYZER_PORT'/message",
        "description": "Analyze staged changes ready for commit",
        "input_schema": {
          "type": "object",
          "properties": {
            "repo_path": {
              "type": "string",
              "description": "Path to the repository to analyze (required)"
            }
          },
          "required": ["repo_path"]
        },
        "metadata": {
          "source": "local_repo_analyzer",
          "bridge_port": '$ANALYZER_PORT',
          "method": "analyze_staged_changes"
        }
      }' \
      "${GATEWAY_URL}/tools" && echo -e "${GREEN}✅ Staged changes analyzer registered${NC}" || echo -e "${RED}❌ Staged changes analyzer registration failed${NC}"

    # Analyze unpushed commits tool
    curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "analyze_unpushed_commits",
        "url": "http://localhost:'$ANALYZER_PORT'/message",
        "description": "Analyze commits that exist locally but have not been pushed to remote",
        "input_schema": {
          "type": "object",
          "properties": {
            "repo_path": {
              "type": "string",
              "description": "Path to the repository to analyze (required)"
            }
          },
          "required": ["repo_path"]
        },
        "metadata": {
          "source": "local_repo_analyzer",
          "bridge_port": '$ANALYZER_PORT',
          "method": "analyze_unpushed_commits"
        }
      }' \
      "${GATEWAY_URL}/tools" && echo -e "${GREEN}✅ Unpushed commits analyzer registered${NC}" || echo -e "${RED}❌ Unpushed commits analyzer registration failed${NC}"

    # Get outstanding summary tool
    curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "get_outstanding_summary",
        "url": "http://localhost:'$ANALYZER_PORT'/message",
        "description": "Get comprehensive summary of all outstanding changes (working dir, staged, unpushed)",
        "input_schema": {
          "type": "object",
          "properties": {
            "repo_path": {
              "type": "string",
              "description": "Path to the repository to analyze (required)"
            }
          },
          "required": ["repo_path"]
        },
        "metadata": {
          "source": "local_repo_analyzer",
          "bridge_port": '$ANALYZER_PORT',
          "method": "get_outstanding_summary"
        }
      }' \
      "${GATEWAY_URL}/tools" && echo -e "${GREEN}✅ Outstanding summary analyzer registered${NC}" || echo -e "${RED}❌ Outstanding summary analyzer registration failed${NC}"

    # Register PR recommendation tools
    echo "Registering PR recommender tools..."

    curl -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "generate_pr_recommendations",
        "url": "http://localhost:'$RECOMMENDER_PORT'/message",
        "description": "Generate PR recommendations from git analysis data",
        "input_schema": {
          "type": "object",
          "properties": {
            "analysis_data": {
              "type": "object",
              "description": "Git analysis data from repository analyzer"
            },
            "strategy": {
              "type": "string",
              "enum": ["semantic", "atomic", "feature-based", "risk-based"],
              "description": "Grouping strategy for PR recommendations",
              "default": "semantic"
            },
            "max_files_per_pr": {
              "type": "integer",
              "description": "Maximum files per PR recommendation",
              "default": 8,
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": ["analysis_data"]
        },
        "metadata": {
          "source": "pr_recommender",
          "bridge_port": '$RECOMMENDER_PORT',
          "method": "generate_pr_recommendations"
        }
      }' \
      "${GATEWAY_URL}/tools" && echo -e "${GREEN}✅ PR recommendations tool registered${NC}" || echo -e "${RED}❌ PR recommendations tool registration failed${NC}"

    echo ""
    echo -e "${GREEN}🔐 Your JWT token:${NC} $JWT_TOKEN"

    # Show usage examples
    echo ""
    echo -e "${BLUE}📖 Usage Examples:${NC}"
    echo "─────────────────────────────────────────"
    echo "# Get outstanding changes summary:"
    echo "curl -X POST -H \"Authorization: Bearer \$MCPGATEWAY_BEARER_TOKEN\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"get_outstanding_summary\",\"params\":{\"repo_path\":\"/path/to/your/repo\"}}' \\"
    echo "  ${GATEWAY_URL}/rpc"
    echo ""
    echo "# Analyze working directory only:"
    echo "curl -X POST -H \"Authorization: Bearer \$MCPGATEWAY_BEARER_TOKEN\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"analyze_working_directory\",\"params\":{\"repo_path\":\"/path/to/your/repo\"}}' \\"
    echo "  ${GATEWAY_URL}/rpc"
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}📊 Bridge Status:${NC}"
    echo "─────────────────────────────────────────"

    # Check analyzer bridge
    if [ -f "$WORKSPACE_ROOT/mcp_local_repo_analyzer/analyzer_bridge.pid" ]; then
        ANALYZER_PID=$(cat "$WORKSPACE_ROOT/mcp_local_repo_analyzer/analyzer_bridge.pid")
        if kill -0 $ANALYZER_PID 2>/dev/null; then
            echo -e "${GREEN}✅ Analyzer Bridge:${NC} Running (PID: $ANALYZER_PID, Port: $ANALYZER_PORT)"
        else
            echo -e "${RED}❌ Analyzer Bridge:${NC} Not running"
        fi
    else
        echo -e "${RED}❌ Analyzer Bridge:${NC} Not started"
    fi

    # Check recommender bridge
    if [ -f "$WORKSPACE_ROOT/mcp_pr_recommender/recommender_bridge.pid" ]; then
        RECOMMENDER_PID=$(cat "$WORKSPACE_ROOT/mcp_pr_recommender/recommender_bridge.pid")
        if kill -0 $RECOMMENDER_PID 2>/dev/null; then
            echo -e "${GREEN}✅ Recommender Bridge:${NC} Running (PID: $RECOMMENDER_PID, Port: $RECOMMENDER_PORT)"
        else
            echo -e "${RED}❌ Recommender Bridge:${NC} Not running"
        fi
    else
        echo -e "${RED}❌ Recommender Bridge:${NC} Not started"
    fi

    echo ""
    echo -e "${BLUE}🌐 Available Endpoints:${NC}"
    echo "  Analyzer SSE:     http://localhost:$ANALYZER_PORT/sse"
    echo "  Analyzer Health:  http://localhost:$ANALYZER_PORT/healthz"
    echo "  Recommender SSE:  http://localhost:$RECOMMENDER_PORT/sse"
    echo "  Recommender Health: http://localhost:$RECOMMENDER_PORT/healthz"
    echo "  Gateway Admin:    http://localhost:4444/admin"
    echo "  Gateway API:      http://localhost:4444/docs"
}

# Function to stop bridges
stop_bridges() {
    echo -e "${YELLOW}🛑 Stopping MCP bridges...${NC}"

    # Stop analyzer bridge
    if [ -f "$WORKSPACE_ROOT/mcp_local_repo_analyzer/analyzer_bridge.pid" ]; then
        ANALYZER_PID=$(cat "$WORKSPACE_ROOT/mcp_local_repo_analyzer/analyzer_bridge.pid")
        if kill -0 $ANALYZER_PID 2>/dev/null; then
            kill $ANALYZER_PID
            echo -e "${GREEN}✅ Stopped analyzer bridge${NC}"
        fi
        rm -f "$WORKSPACE_ROOT/mcp_local_repo_analyzer/analyzer_bridge.pid"
    fi

    # Stop recommender bridge
    if [ -f "$WORKSPACE_ROOT/mcp_pr_recommender/recommender_bridge.pid" ]; then
        RECOMMENDER_PID=$(cat "$WORKSPACE_ROOT/mcp_pr_recommender/recommender_bridge.pid")
        if kill -0 $RECOMMENDER_PID 2>/dev/null; then
            kill $RECOMMENDER_PID
            echo -e "${GREEN}✅ Stopped recommender bridge${NC}"
        fi
        rm -f "$WORKSPACE_ROOT/mcp_pr_recommender/recommender_bridge.pid"
    fi
}

# Main script logic
case "${1:-start}" in
    "start")
        echo -e "${BLUE}🚀 Starting MCP bridges...${NC}"
        start_analyzer_bridge
        start_recommender_bridge
        test_bridges
        register_with_gateway
        show_status
        ;;
    "stop")
        stop_bridges
        ;;
    "status")
        show_status
        ;;
    "restart")
        stop_bridges
        sleep 2
        start_analyzer_bridge
        start_recommender_bridge
        test_bridges
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start    - Start bridges and register with gateway"
        echo "  stop     - Stop all bridges"
        echo "  status   - Show bridge status"
        echo "  restart  - Restart all bridges"
        exit 1
        ;;
esac
