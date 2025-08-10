# 🚀 Docker Images Implementation Plan

## 1. Executive Summary

This document outlines the implementation plan to achieve a 30-second setup for the MCP Auto PR project by using pre-built Docker images.

- **Current State**: Local Docker builds take 2-3 minutes, defeating the quick setup goal.
- **Target State**: Pre-built images from GitHub Container Registry enable 15-30 second setup.
- **Timeline**: Estimated 6-7 hours to complete all phases.

## 2. Prerequisites & Assumptions

- **GitHub Repositories**: `mcp_local_repo_analyzer` and `mcp_pr_recommender` are separate GitHub repositories.
- **Permissions**: GitHub Actions require package write permissions to push to the container registry.
- **Environment**: Development and deployment environments support Docker and Docker Compose.

## 3. Detailed Implementation Phases

### Phase 1: GitHub Actions Setup (2-3 hours)

- [ ] Create `.github/workflows/docker-build.yml` in `mcp_local_repo_analyzer`
- [ ] Create `.github/workflows/docker-build.yml` in `mcp_pr_recommender`
- [ ] Configure GitHub Container Registry permissions
- [ ] Test workflow with a release tag

### Phase 2: Install Script Enhancement (2 hours)

- [ ] Add command line argument parsing for `stable`, `bleeding-edge`, and `version` modes.
- [ ] Implement logic to use pre-built images by default (`stable` mode).
- [ ] Add fallback to local build for `bleeding-edge` mode.
- [ ] Set `MCP_VERSION` environment variable based on selected mode.

### Phase 3: Docker Compose Updates (1 hour)

- [ ] Update `docker-compose.yml` to use versioned images from `ghcr.io`.
- [ ] Maintain `build` context for local development fallback.
- [ ] Test image pulling and local build fallback.

### Phase 4: Dockerfile Optimization (1 hour)

- [ ] Create optimized, standalone Dockerfiles in each repository.
- [ ] Add `.dockerignore` files to reduce build context.
- [ ] Implement multi-stage builds to minimize final image size.

### Phase 5: Testing & Validation (1 hour)

- [ ] Test `stable` mode setup time (target: 15-30 seconds).
- [ ] Test `bleeding-edge` mode to ensure local builds work correctly.
- [ ] Test `version` mode with a specific tagged release.
- [ ] Validate that all service health endpoints are operational.
- [ ] Document final performance metrics.

## 4. Release Process

- **Tagging Strategy**: Releases will be triggered by pushing `v*` tags (e.g., `v1.0.0`).
- **Automation**: GitHub Actions will automatically build and push images for each release.
- **Verification**: Post-build, automated tests will verify image integrity.

## 5. Troubleshooting

- **Build Failures**: Check GitHub Actions logs for build errors.
- **Pull Errors**: Ensure `ghcr.io` is accessible and image tags are correct.
- **Performance Issues**: Analyze Docker build logs for caching and optimization opportunities.

## 6. Success Metrics

- **Setup Time**: First-time setup for stable releases should be under 30 seconds.
- **Image Size**: Final images should be optimized for size.
- **User Experience**: Clear and reliable installation process for both stable and development modes.
