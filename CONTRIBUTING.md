# Contributing to MCP Auto PR

Thank you for your interest in contributing to MCP Auto PR! This guide outlines the development workflow and standards for this project.

## Development Environment Setup

### Prerequisites
- Python 3.10 or higher
- Poetry for dependency management
- Git for version control
- Docker and Docker Compose (for containerized deployment)
- Make (for workspace orchestration)

### Initial Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/manavgup/mcp_auto_pr.git
   cd mcp_auto_pr
   ```

2. **Set up the entire workspace:**
   ```bash
   make setup-workspace
   ```

3. **Install all dependencies:**
   ```bash
   make install-all
   ```

4. **Verify installation:**
   ```bash
   make test-all
   ```

## Code Standards

### Code Style
This project follows the same standards as other MCP repositories:

- **Black**: Code formatting with 88-character line length
- **Ruff**: Fast Python linter for code quality
- **mypy**: Static type checking
- **pre-commit**: Automated checks before commits

### Running Code Quality Checks
```bash
# Run quality checks across all repositories
make lint-all
make format-all

# Individual repository checks
cd ../mcp_shared_lib && poetry run pre-commit run --all-files
```

### Documentation Standards
- All scripts must include header comments explaining purpose
- Docker configurations must be documented
- Makefile targets must include help text
- Update README.md for significant changes

## Project Structure

### MCP Auto PR Architecture
This repository provides orchestration and deployment for the MCP ecosystem:

- **Docker Services**: Containerized deployment of analyzer and recommender
- **Scripts**: Setup automation, health checks, integration testing
- **Documentation**: Architecture guides, setup instructions, API integration
- **Workspace**: Multi-root workspace coordination and build system

### Key Components
- **docker-compose.yml**: Production deployment configuration
- **docker-compose.dev.yml**: Development deployment configuration
- **scripts/**: Automation scripts for setup and maintenance
- **docs/**: Architecture documentation and guides
- **Makefile**: Workspace-level orchestration commands

## Development Workflow

### Branch Strategy
1. Create feature branches from `main`: `git checkout -b feature/your-feature-name`
2. Test changes across all repositories
3. Push branch and create pull request
4. Address review feedback
5. Merge after approval

### Commit Message Format
```
type(scope): short description

Longer description if needed explaining the changes
and their rationale.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `ci`: CI/CD pipeline changes
- `docker`: Docker configuration changes

### Pull Request Process
1. **Before creating PR:**
   - Test workspace-level commands work correctly
   - Verify Docker services start and communicate properly
   - Run cross-repository tests
   - Update documentation if needed

2. **PR Requirements:**
   - Clear title and description
   - Link to related issues
   - Include testing instructions for entire workspace
   - Verify Docker deployment works

3. **Review Process:**
   - Address all reviewer feedback
   - Ensure all repository CI checks pass
   - Test Docker deployment in clean environment
   - Await approval before merging

## Workspace Management

### Available Make Commands
```bash
# Workspace setup and management
make setup-auto         # Auto-clone all repos and setup
make setup-workspace    # Initialize entire workspace
make install-all        # Install all repo dependencies
make update-all         # Update all repo dependencies

# Cross-repo testing and quality
make test-all          # Run tests across all repos
make lint-all          # Run linting across all repos
make format-all        # Format code across all repos

# Service management
make serve-analyzer    # Start analyzer service (port 8001)
make serve-recommender # Start recommender service (port 8002)
make serve-all         # Start all MCP servers
make check-servers     # Check server entry points
make stop-servers      # Stop all MCP servers
```

### Docker Deployment
```bash
# Production deployment
docker-compose up -d

# Development deployment
docker-compose -f docker-compose.dev.yml up -d

# Health checks
curl http://localhost:9070/health  # Analyzer service
curl http://localhost:9071/health  # Recommender service

# View logs
docker-compose logs -f mcp-repo-analyzer
docker-compose logs -f mcp-pr-recommender
```

### Multi-Repository Coordination
- **Dependency Updates**: Coordinate version updates across repos
- **Breaking Changes**: Test impact across all services
- **Release Management**: Coordinate releases and tagging
- **CI/CD Pipeline**: Ensure consistent pipeline configurations

## Testing Requirements

### Test Types
- **Integration Tests**: Cross-service communication tests
- **Docker Tests**: Container deployment and health checks
- **Workspace Tests**: Multi-repository operation validation
- **End-to-End Tests**: Complete workflow testing

### Running Tests
```bash
# Test entire workspace
make test-all

# Test specific aspects
make test-integration
make test-docker
make test-workspace
```

### Test Coverage
- Maintain coverage across all repositories
- Test Docker service interactions
- Validate workspace orchestration commands
- Test failure scenarios and recovery

## Project-Specific Guidelines

### Docker Best Practices
- **Multi-stage builds**: Optimize image sizes
- **Health checks**: Include comprehensive health endpoints
- **Environment variables**: Externalize all configuration
- **Volume management**: Persist important data
- **Network configuration**: Secure service communication

### Script Guidelines
- **Error handling**: All scripts must handle failures gracefully
- **Logging**: Include informative progress messages
- **Idempotency**: Scripts should be safe to run multiple times
- **Documentation**: Include usage examples and help text

### Documentation Standards
- **Architecture docs**: Keep architectural decisions documented
- **Setup guides**: Maintain comprehensive setup instructions
- **API documentation**: Document service interactions
- **Troubleshooting**: Include common issues and solutions

## Issue Reporting

### Bug Reports
When reporting bugs, please include:
- Operating system and Docker version
- Complete error messages and logs
- Docker service states and health checks
- Steps to reproduce across workspace
- Expected vs. actual behavior

### Feature Requests
For new features, please provide:
- Clear use case and motivation
- Impact assessment across all repositories
- Docker/deployment considerations
- Backward compatibility analysis

## Getting Help

- **Documentation**: Check the extensive docs/ directory
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for architecture questions
- **Code Review**: Ask for guidance on multi-repo coordination

## Recognition

Contributors are recognized in:
- Git commit history
- Release notes for significant contributions
- Contributors section in README.md
- Architecture decision records

Thank you for contributing to MCP Auto PR!
