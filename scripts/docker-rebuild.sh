#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Building Docker image..."
docker build -t whatsapp-mcp .

echo "Stopping and removing existing container (if any)..."
docker rm -f whatsapp-mcp 2>/dev/null || true

echo "Starting new container..."
docker run -d \
  --name whatsapp-mcp \
  -p 8000:8000 \
  -v "$PROJECT_ROOT/tmp/store:/app/whatsapp-bridge/store" \
  whatsapp-mcp

echo "Done! Container 'whatsapp-mcp' is running."
echo "Port 8000 exposed, store mounted at tmp/store"
