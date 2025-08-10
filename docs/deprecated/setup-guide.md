# MCP Auto PR Setup Guide

This guide explains how to set up and manage the MCP Auto PR workspace, which automatically clones and configures all required repositories.

---

## Prerequisites

- **Git** (https://git-scm.com/)
- **Python 3.11+**
- **Poetry** (recommended):
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```
- **VSCode** (recommended)

---

## 🚀 Automatic Setup (Recommended)

1. **Clone the main repository:**
   ```bash
   git clone https://github.com/manavgup/mcp_auto_pr.git
   cd mcp_auto_pr
   ```
2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   - This will:
     - Clone all required repositories
     - Set up Python environments
     - Install dependencies
     - Generate a VSCode workspace file
3. **Open the workspace in VSCode:**
   ```bash
   code ../mcp_workspace.code-workspace
   ```

---

## 🛠️ Makefile Commands

- `make setup-auto` — Auto-clone all repos and setup
- `make test-setup` — Test if workspace is properly setup
- `make setup-workspace` — Setup dependencies for existing repos
- `make install-all` — Install all dependencies
- `make test-all` — Run all tests
- `make format-all` — Format all code
- `make serve-analyzer` — Start analyzer service
- `make serve-recommender` — Start recommender service

---

## 🧩 Scripts Overview

- `setup.sh` — Top-level entry point for workspace setup
- `scripts/setup-workspace.sh` — Main script for cloning, updating, and configuring all repos
- `scripts/config.sh` — Central configuration for repo URLs, branches, and workspace settings
- `scripts/test-setup.sh` — Test script to verify workspace health
- `scripts/post-clone.sh` — Alternative post-clone setup script

---

## 📁 Workspace Structure

```
mcp_workspace/
├── mcp_auto_pr/           # Main coordination repo
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

## 🧑‍💻 Advanced Configuration

- **Add/Remove repositories:** Edit `scripts/config.sh` and update the `REPOS` array.
- **Change default branches:** Edit `DEFAULT_BRANCHES` in `scripts/config.sh`.
- **Customize workspace file:** Edit the workspace generation logic in `scripts/setup-workspace.sh`.

---

## 🤝 Contributing

See [Contributing Guidelines](../CONTRIBUTING.md)

---

## 📄 License

[Link to License]
