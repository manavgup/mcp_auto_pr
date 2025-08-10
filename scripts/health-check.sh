#!/bin/bash

services=("mcp-repo-analyzer:9070" "mcp-pr-recommender:9071")
max_wait=60
wait_time=0

echo "🔍 Checking MCP server health..."

for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"

    echo "Checking $name on port $port..."

    while [ $wait_time -lt $max_wait ]; do
        if curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
            echo "✅ $name is healthy"
            break
        fi

        sleep 3
        wait_time=$((wait_time + 3))

        if [ $wait_time -ge $max_wait ]; then
            echo "❌ $name failed to become healthy within ${max_wait}s"
            echo "💡 Try: docker-compose logs $name"
            exit 1
        fi
    done
done

echo "🎉 All MCP servers are healthy!"
