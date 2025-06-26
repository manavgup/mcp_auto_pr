# MCP Auto PR System

Automatically creates pull requests based on outstanding code changes across repositories.

## Repository Architecture

| Repository | Purpose | Status |
|------------|---------|--------|
| [mcp_shared_lib](https://github.com/manavgup/mcp_shared_lib) | Shared models, tools, utilities | ✅ Active |
| [mcp_local_repo_analyzer](https://github.com/manavgup/mcp_local_repo_analyzer) | Analyzes repository changes | 🏗️ In Progress |
| [mcp_pr_recommender](https://github.com/manavgup/mcp_pr_recommender) | Generates PR recommendations | 🏗️ In Progress |
| [mcp_auto_pr](https://github.com/manavgup/mcp_auto_pr) | Project coordination & docs | 📋 Planning |

---

## 🚀 Quick Start

### 1. Clone and Setup the Workspace

```bash
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr
./setup.sh
```

- This will **automatically clone all required repositories** into the parent directory, set up Python environments, install dependencies, and generate a VSCode workspace file.

### 2. Open in VSCode

```bash
code ../mcp_workspace.code-workspace
```

---

## 🛠️ Workspace Management

You can also use the Makefile for common tasks:

```bash
make setup-auto      # Auto-clone all repos and setup
make test-setup      # Test if workspace is properly setup
make setup-workspace # Setup dependencies for existing repos
make install-all     # Install all dependencies
make test-all        # Run all tests
make format-all      # Format all code
make serve-analyzer  # Start analyzer service
make serve-recommender # Start recommender service
```

---

## 📁 Workspace Structure

```
mcp_workspace/
├── mcp_auto_pr/           # Main coordination repo (this one)
│   ├── scripts/           # Setup and utility scripts
│   ├── docs/              # Documentation
│   ├── workspace/         # VSCode workspace templates
│   └── Makefile           # Build and management commands
├── mcp_shared_lib/        # Shared utilities and models
├── mcp_local_repo_analyzer/ # Repository change analysis
├── mcp_pr_recommender/    # PR recommendation engine
└── mcp_workspace.code-workspace  # VSCode workspace file
```

---

## 📚 Documentation

- [Setup Guide](docs/setup-guide.md) — **Detailed setup, troubleshooting, and advanced configuration**
- [Architecture Overview](docs/architecture.md)
- [API Integration](docs/api-integration.md)
- [Project Planning](planning/)

---

## 🧩 Scripts Overview

- `setup.sh` — Top-level entry point for workspace setup (run this after cloning)
- `scripts/setup-workspace.sh` — Main script for cloning, updating, and configuring all repos
- `scripts/config.sh` — Central configuration for repo URLs, branches, and workspace settings
- `scripts/test-setup.sh` — Test script to verify workspace health
- `scripts/post-clone.sh` — Alternative post-clone setup script

---

## 🐞 Troubleshooting

- **Permission denied:**
  ```bash
  chmod +x setup.sh scripts/*.sh
  ```
- **Git not found:** Install from https://git-scm.com/
- **Poetry not found:**
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```
- **Repo already exists:** The setup script will pull latest changes automatically.
- **Workspace file missing:** Run `./setup.sh` or `make setup-auto` again.
- **Test your setup:**
  ```bash
  make test-setup
  ```

---

## 🤝 Contributing

See [Contributing Guidelines](CONTRIBUTING.md)

---

## 📄 License

[Link to License]

