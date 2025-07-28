# MCP Auto PR System

**Intelligent PR boundary detection and recommendation system powered by Model Context Protocol (MCP)**

Automatically analyzes outstanding code changes and generates atomic, logically-grouped pull request recommendations optimized for code review efficiency and deployment safety.

## 🏗️ Repository Architecture

| Repository | Purpose | Status |
|------------|---------|--------|
| [mcp_shared_lib](https://github.com/manavgup/mcp_shared_lib) | Shared models, tools, utilities | ✅ Active |
| [mcp_local_repo_analyzer](https://github.com/manavgup/mcp_local_repo_analyzer) | Analyzes repository changes | ✅ Active |
| [mcp_pr_recommender](https://github.com/manavgup/mcp_pr_recommender) | Generates PR recommendations | ✅ Active |
| [mcp_auto_pr](https://github.com/manavgup/mcp_auto_pr) | Project coordination & Docker orchestration | ✅ Active |
| [mcp-gateway-demo](https://github.com/manavgup/mcp-gateway-demo) | Demo scenarios and examples | 🚀 New |

---

## 🚀 Quick Start

### Option 1: Docker Setup (Recommended)

```bash
# Clone and setup
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr
./setup.sh  # Sets up workspace with all repositories

# Start with Docker
chmod +x scripts/*.sh
./scripts/docker-setup.sh
```

### Option 2: Traditional Setup

```bash
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr
./setup.sh
```

---

## 🐳 Docker Deployment

### Quick Start
```bash
# One-command setup
./scripts/docker-setup.sh

# Test the deployment
./scripts/test-servers.sh
```

### Services
- **Local Repo Analyzer**: `http://localhost:9070`
- **PR Recommender**: `http://localhost:9071`
- **Health Checks**: `/health` endpoint on each service

### Docker Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose build && docker-compose up -d
```

---

## 🛠️ Workspace Management

### Makefile Commands
```bash
make setup-auto        # Auto-clone all repos and setup
make test-setup         # Test if workspace is properly setup
make setup-workspace    # Setup dependencies for existing repos
make install-all        # Install all dependencies
make test-all          # Run all tests
make format-all        # Format all code
make serve-analyzer    # Start analyzer service
make serve-recommender # Start recommender service
```

### VSCode Integration
```bash
code ../mcp_workspace.code-workspace
```

---

## 📁 Workspace Structure

```
mcp_workspace/
├── mcp_auto_pr/                    # Main coordination repo
│   ├── docker-compose.yml         # Docker orchestration
│   ├── scripts/                   # Setup and utility scripts
│   │   ├── docker-setup.sh       # Docker deployment script
│   │   ├── test-servers.sh       # Server testing script
│   │   └── health-check.sh       # Health monitoring
│   ├── docker/                   # Docker configurations
│   │   ├── analyzer/Dockerfile   # Repo analyzer container
│   │   ├── recommender/Dockerfile # PR recommender container
│   │   └── docs/                 # Integration guides
│   ├── docs/                     # Documentation
│   └── Makefile                  # Build commands
├── mcp_shared_lib/               # Shared utilities and models
├── mcp_local_repo_analyzer/      # Repository change analysis
├── mcp_pr_recommender/           # PR recommendation engine
└── mcp_workspace.code-workspace  # VSCode workspace file
```

---

## 🔌 Integration Options

### MCP Gateway Integration
```bash
# Register with MCP Gateway
curl -X POST http://localhost:8000/gateways \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-JWT-TOKEN" \
  -d '{"name":"repo-analyzer","url":"http://localhost:9070/mcp"}'

curl -X POST http://localhost:8000/gateways \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-JWT-TOKEN" \
  -d '{"name":"pr-recommender","url":"http://localhost:9071/mcp"}'
```

### Claude Desktop Integration
Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "mcp-gateway": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-gateway", "mcp-client"],
      "env": {
        "MCP_GATEWAY_URL": "http://localhost:8000"
      }
    }
  }
}
```

---

## 🎯 Available Tools

### Local Repository Analyzer
- `analyze_working_directory` - Analyze uncommitted changes
- `analyze_staged_changes` - Analyze staged changes
- `get_outstanding_summary` - Comprehensive change summary
- `compare_with_remote` - Compare with remote branch

### PR Recommender
- `generate_pr_recommendations` - Generate smart PR groupings
- `analyze_pr_feasibility` - Analyze PR feasibility and risks
- `get_strategy_options` - Available grouping strategies
- `validate_pr_recommendations` - Validate recommendations

---

## 🧪 Demo Scenarios

Check out the [MCP Gateway Demo](https://github.com/manavgup/mcp-gateway-demo) repository for:

1. **Messy Repo Rescue** - Transform chaotic changes into clean PRs
2. **Smart Memory Assistant** - Learn from development patterns
3. **GitHub Automation Hub** - Automate workflow orchestration
4. **Team Coordination Engine** - Multi-developer coordination

---

## 📚 Documentation

- [Docker Integration Guide](docker/docs/claude-integration.md)
- [VSCode Setup](docker/docs/vscode-integration.md)
- [MCP Gateway Integration](docker/docs/gateway-integration.md)
- [Setup Guide](docs/setup-guide.md)
- [Architecture Overview](docs/architecture.md)
- [API Integration](docs/api-integration.md)

---

## 🐞 Troubleshooting

### Docker Issues
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs mcp-repo-analyzer
docker-compose logs mcp-pr-recommender

# Restart services
docker-compose restart
```

### Common Issues
- **Permission denied:**
  ```bash
  chmod +x setup.sh scripts/*.sh
  ```
- **Port conflicts:** Stop conflicting services with `pm2 delete all`
- **Missing dependencies:** Run `./setup.sh` to reinstall
- **Docker not found:** Install Docker Desktop
- **Test your setup:**
  ```bash
  ./scripts/test-servers.sh
  ```

---

## 🌟 Key Features

- **🚀 One-Command Deployment** - Docker-first architecture
- **🧠 Intelligent Analysis** - AI-powered change detection
- **📦 Atomic PRs** - Logical, reviewable groupings
- **🔄 Multiple Transport** - stdio, HTTP, streamable-http
- **🎯 Gateway Ready** - Seamless MCP Gateway integration
- **📊 Health Monitoring** - Built-in health checks
- **🔧 Developer Friendly** - Easy local development

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test with Docker: `./scripts/test-servers.sh`
4. Submit a pull request

---

## 📄 License

[MIT License](LICENSE)