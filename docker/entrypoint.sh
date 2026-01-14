#!/bin/sh
set -e

STORE_DIR="/app/whatsapp-bridge/store"
BRIDGE_DIR="/app/whatsapp-bridge"
MCP_DIR="/app/whatsapp-mcp-server"

mkdir -p "$STORE_DIR"

(
	cd "$BRIDGE_DIR"
	./whatsapp-bridge
) &

cd "$MCP_DIR"
exec uv run main.py
