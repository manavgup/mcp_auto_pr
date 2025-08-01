#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP Auto PR - One-Command Install
#   Get up and running in 30 seconds!
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}${BOLD}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🚀 MCP Auto PR - 30 Second Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Timer functions
start_timer() {
    START_TIME=$(date +%s)
}

show_timer() {
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    echo -e "${GREEN}⏱️  Setup completed in ${ELAPSED} seconds!${NC}"
}

# Environment detection
detect_environment() {
    print_status "Detecting environment..."
    
    # Check for Docker
    if command -v docker &> /dev/null && docker info >/dev/null 2>&1; then
        INSTALL_METHOD="docker"
        print_success "Docker detected - using containerized setup"
    elif command -v poetry &> /dev/null; then
        INSTALL_METHOD="poetry"
        print_success "Poetry detected - using local setup"
    else
        print_warning "Neither Docker nor Poetry found"
        print_status "Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        INSTALL_METHOD="poetry"
    fi
    
    # Check for required tools
    if ! command -v git &> /dev/null; then
        print_error "Git is required but not installed"
        exit 1
    fi
    
    # Auto-detect API key
    if [ -n "$OPENAI_API_KEY" ]; then
        print_success "OpenAI API key detected"
        HAS_API_KEY=true
    else
        print_warning "OPENAI_API_KEY not set - PR recommender will be limited"
        HAS_API_KEY=false
    fi
}

# Quick Docker setup
setup_docker() {
    print_status "Setting up with Docker (fastest method)..."
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cp .env.example .env
        if [ "$HAS_API_KEY" = true ]; then
            sed -i.bak "s/your_openai_api_key_here/$OPENAI_API_KEY/" .env
        fi
    fi
    
    # Use pre-built images if available, otherwise build
    print_status "Starting MCP services..."
    if docker-compose pull --quiet 2>/dev/null; then
        print_success "Using pre-built images"
        docker-compose up -d --quiet-pull
    else
        print_status "Building images (this may take a moment)..."
        docker-compose up -d --build
    fi
    
    # Quick health check
    print_status "Checking service health..."
    sleep 5
    ./scripts/health-check.sh
}

# Quick Poetry setup
setup_poetry() {
    print_status "Setting up with Poetry..."
    
    # Run workspace setup
    ./setup.sh
    
    # Quick health check for local services
    print_status "Services ready for local development"
}

# Generate connection configs
generate_configs() {
    print_status "Generating connection configurations..."
    
    # Create configs directory
    mkdir -p configs
    
    # VS Code/Cursor MCP config
    cat > configs/mcp-settings.json << EOF
{
  "mcpServers": {
    "repo-analyzer": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-repo-analyzer", "python", "-m", "mcp_local_repo_analyzer.main"],
      "transport": "stdio"
    },
    "pr-recommender": {
      "command": "docker", 
      "args": ["exec", "-i", "mcp-pr-recommender", "python", "-m", "mcp_pr_recommender.main"],
      "transport": "stdio"
    }
  }
}
EOF

    # Cline integration config
    cat > configs/cline-mcp-settings.json << EOF
{
  "mcpServers": {
    "repo-analyzer": {
      "timeout": 120,
      "type": "stdio",
      "command": "poetry",
      "args": ["run", "python", "-m", "mcp_local_repo_analyzer.main"],
      "cwd": "./mcp_local_repo_analyzer"
    },
    "pr-recommender": {
      "timeout": 120,
      "type": "stdio", 
      "command": "poetry",
      "args": ["run", "python", "-m", "mcp_pr_recommender.main"],
      "cwd": "./mcp_pr_recommender",
      "env": {
        "OPENAI_API_KEY": "\${OPENAI_API_KEY}"
      }
    }
  }
}
EOF

    print_success "Configuration files created in configs/"
}

# Show next steps
show_next_steps() {
    echo ""
    echo -e "${GREEN}${BOLD}🎉 MCP Auto PR is ready!${NC}"
    echo ""
    
    if [ "$INSTALL_METHOD" = "docker" ]; then
        echo -e "${BLUE}📊 Services running:${NC}"
        echo "   • Local Repo Analyzer: http://localhost:9070"
        echo "   • PR Recommender: http://localhost:9071"
        echo ""
        echo -e "${BLUE}🔧 Quick test:${NC}"
        echo "   curl http://localhost:9070/health"
        echo "   curl http://localhost:9071/health"
        echo ""
    fi
    
    echo -e "${BLUE}🔌 IDE Integration:${NC}"
    echo "   • VS Code/Cursor: Copy configs/mcp-settings.json to your MCP settings"
    echo "   • Cline: Copy configs/cline-mcp-settings.json to your Cline settings"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "   • Architecture: docs/architecture.md"
    echo "   • Setup Guide: docs/setup-guide.md"
    echo "   • API Integration: docs/api-integration.md"
    echo ""
    echo -e "${BLUE}🛠️  Management:${NC}"
    if [ "$INSTALL_METHOD" = "docker" ]; then
        echo "   • Stop services: docker-compose down"
        echo "   • View logs: docker-compose logs -f"
        echo "   • Restart: docker-compose restart"
    else
        echo "   • Run tests: make test-all"
        echo "   • Start services: make serve-all"
        echo "   • View help: make help"
    fi
    echo ""
    echo -e "${YELLOW}💡 Pro tip:${NC} Set OPENAI_API_KEY environment variable for full PR recommendation features"
}

# Main execution
main() {
    print_header
    start_timer
    
    # Environment detection
    detect_environment
    
    # Run appropriate setup
    case $INSTALL_METHOD in
        docker)
            setup_docker
            ;;
        poetry)
            setup_poetry
            ;;
        *)
            print_error "Unknown installation method: $INSTALL_METHOD"
            exit 1
            ;;
    esac
    
    # Generate configs
    generate_configs
    
    # Show results
    show_timer
    show_next_steps
}

# Handle script arguments
case "${1:-}" in
    --docker)
        INSTALL_METHOD="docker"
        ;;
    --poetry)
        INSTALL_METHOD="poetry"
        ;;
    --help|-h)
        echo "MCP Auto PR - One-Command Install"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --docker    Force Docker installation"
        echo "  --poetry    Force Poetry installation"
        echo "  --help      Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  OPENAI_API_KEY    OpenAI API key for PR recommendations"
        echo ""
        exit 0
        ;;
esac

# Run main function
main "$@"
