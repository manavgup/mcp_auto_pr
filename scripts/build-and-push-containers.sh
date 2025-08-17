#!/bin/bash

# Build and Push MCP Containers to GHCR
# This script helps manually build and push containers to GitHub Container Registry

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
ANALYZER_REPO="manavgup/mcp_local_repo_analyzer"
RECOMMENDER_REPO="manavgup/mcp_pr_recommender"
VERSION=${1:-"latest"}

echo -e "${BLUE}🚀 Building and Pushing MCP Containers to GHCR${NC}"
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if logged into GHCR
if ! docker info | grep -q "ghcr.io"; then
    echo -e "${YELLOW}⚠️  Not logged into GHCR. Please run:${NC}"
    echo -e "${YELLOW}   echo \$GITHUB_TOKEN | docker login ghcr.io -u \$GITHUB_USERNAME --password-stdin${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to build and push a container
build_and_push() {
    local repo=$1
    local context=$2
    local dockerfile=$3
    local port=$4

    echo -e "${BLUE}🔨 Building ${repo}...${NC}"

    # Build the image
    docker build \
        --platform linux/amd64,linux/arm64 \
        -f "${dockerfile}" \
        -t "${REGISTRY}/${repo}:${VERSION}" \
        -t "${REGISTRY}/${repo}:latest" \
        "${context}"

    echo -e "${GREEN}✅ Built ${repo} successfully${NC}"

    # Push the image
    echo -e "${BLUE}📤 Pushing ${repo} to GHCR...${NC}"
    docker push "${REGISTRY}/${repo}:${VERSION}"
    docker push "${REGISTRY}/${repo}:latest"

    echo -e "${GREEN}✅ Pushed ${repo} successfully${NC}"
    echo ""
}

# Build and push Local Repository Analyzer
echo -e "${YELLOW}📦 Local Repository Analyzer${NC}"
build_and_push \
    "${ANALYZER_REPO}" \
    "../mcp_local_repo_analyzer" \
    "docker/analyzer/Dockerfile" \
    "9070"

# Build and push PR Recommender
echo -e "${YELLOW}📦 PR Recommender${NC}"
build_and_push \
    "${RECOMMENDER_REPO}" \
    "../mcp_pr_recommender" \
    "docker/recommender/Dockerfile" \
    "9071"

echo -e "${GREEN}🎉 All containers built and pushed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Container URLs:${NC}"
echo -e "  ${ANALYZER_REPO}: ${REGISTRY}/${ANALYZER_REPO}:${VERSION}"
echo -e "  ${RECOMMENDER_REPO}: ${REGISTRY}/${RECOMMENDER_REPO}:${VERSION}"
echo ""
echo -e "${BLUE}🔍 View containers at:${NC}"
echo -e "  https://github.com/manavgup/mcp_local_repo_analyzer/packages"
echo -e "  https://github.com/manavgup/mcp_pr_recommender/packages"
