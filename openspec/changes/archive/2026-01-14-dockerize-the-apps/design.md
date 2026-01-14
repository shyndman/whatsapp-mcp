## Context
The project currently runs two local processes: a Go WhatsApp bridge and a Python MCP server. The bridge exposes a REST API on port `8080` and stores all WhatsApp session and message data under `whatsapp-bridge/store/`. The Python MCP server reads the SQLite database directly and uses the bridge REST API for send/download operations. This change packages both services into a single Docker image, switches MCP to Streamable HTTP, and persists WhatsApp data via a Docker volume mounted at the existing path.

## Current Architecture
1. **Go bridge runtime**
   1.1. Runs from `whatsapp-bridge/` and stores data in `whatsapp-bridge/store/` relative to its working directory.
   1.2. Stores session/auth data in `whatsapp-bridge/store/whatsapp.db`.
   1.3. Stores message history in `whatsapp-bridge/store/messages.db`.
   1.4. Writes downloaded media under `whatsapp-bridge/store/<chat>/`.
2. **Python MCP server runtime**
   2.1. Runs from `whatsapp-mcp-server/` using `uv run main.py`.
   2.2. Reads SQLite data from `../whatsapp-bridge/store/messages.db` (relative to `whatsapp-mcp-server/`).
   2.3. Sends HTTP requests to `http://localhost:8080/api` for message sending and media download.
   2.4. Uses STDIO transport for MCP connections.
3. **Local process management**
   3.1. Operators run and monitor two processes manually.
   3.2. No container packaging exists today.

## Proposed Architecture
1. **Single Docker image**
   1.1. Build a single image that includes the Go bridge binary and the Python MCP server runtime.
   1.2. Maintain the existing directory layout inside the image:
       1.2.1. `/app/whatsapp-bridge` for the Go bridge.
       1.2.2. `/app/whatsapp-mcp-server` for the MCP server.
2. **Streamable HTTP MCP**
   2.1. Update the MCP server to run `mcp.run(transport="http", host="0.0.0.0", port=8000)`.
   2.2. Keep the default MCP endpoint path `/mcp/`.
3. **Persistent data**
   3.1. Keep the storage path as `/app/whatsapp-bridge/store`.
   3.2. Declare the path as a Docker volume target so auth and history persist across restarts.
4. **Ports and networking**
   4.1. Expose port `8000` for Streamable HTTP MCP.
   4.2. Keep the bridge REST API internal on port `8080` (no host port publishing by default).
5. **Runtime dependencies**
   5.1. Include `ffmpeg` in the runtime image for audio conversion.
   5.2. Use a Debian-based runtime to keep CGO + SQLite + FFmpeg installation straightforward.

## Docker Build Plan
1. **Go builder stage**
   1.1. Base image: `golang:1.24.x` (Debian-based) to match the repo’s Go version.
   1.2. Install CGO prerequisites if they are not present in the base image:
       1.2.1. `gcc` and `libsqlite3-dev` for `go-sqlite3` builds.
   1.3. Set `WORKDIR /src/whatsapp-bridge`.
   1.4. Copy `whatsapp-bridge/go.mod` and `whatsapp-bridge/go.sum`, then run `go mod download`.
   1.5. Copy the rest of `whatsapp-bridge/` and build the binary:
       1.5.1. `CGO_ENABLED=1`.
       1.5.2. `go build -o /out/whatsapp-bridge`.
2. **Python runtime stage**
   2.1. Base image: `python:3.11-slim` (Debian-based).
   2.2. Install runtime packages: `ffmpeg`, `ca-certificates`, and any OS packages required for SSL.
   2.3. Copy the `uv` binary from `ghcr.io/astral-sh/uv:<pinned-version>` to `/bin/uv` and `/bin/uvx`.
   2.4. Set `WORKDIR /app` and copy the repository contents into `/app`.
   2.5. Install Python dependencies from `whatsapp-mcp-server/pyproject.toml` and `whatsapp-mcp-server/uv.lock`:
       2.5.1. Set `UV_NO_DEV=1` to avoid dev dependencies.
       2.5.2. Run `uv sync --locked` inside `/app/whatsapp-mcp-server`.
   2.6. Copy the Go bridge binary from the builder stage to `/app/whatsapp-bridge/whatsapp-bridge` (or `/app/bin/whatsapp-bridge`).
   2.7. Add an entrypoint script and mark it executable.
   2.8. Declare `VOLUME /app/whatsapp-bridge/store` and `EXPOSE 8000`.

## Runtime Process Model
1. **Entrypoint responsibilities**
   1.1. Ensure `/app/whatsapp-bridge/store` exists (create it if missing).
   1.2. Start the Go bridge from `/app/whatsapp-bridge` so `store/` resolves correctly.
   1.3. Start the MCP server from `/app/whatsapp-mcp-server` using `uv run main.py`.
   1.4. Keep the MCP server as the foreground process so container lifecycle follows MCP lifecycle.
2. **Signal behavior**
   2.1. The MCP process receives `SIGTERM`/`SIGINT` as the foreground process.
   2.2. When the container stops, Docker terminates both processes; no in-container supervisor is required for this scope.

## Data Flow in the Container
1. MCP tools call the Python server at `http://<host>:8000/mcp/`.
2. The Python server reads message history from `/app/whatsapp-bridge/store/messages.db`.
3. The Python server forwards send/download operations to `http://localhost:8080/api` (Go bridge).
4. The Go bridge uses `whatsapp-bridge/store/whatsapp.db` for auth and updates `messages.db`.

## Operational Notes
1. **Port usage**
   1.1. Host port `8000` maps to container port `8000` for MCP.
   1.2. The bridge REST API stays internal on port `8080`; do not publish it to the host unless debugging.
2. **Volume usage**
   2.1. Operators should mount a Docker volume at `/app/whatsapp-bridge/store` to persist auth.
   2.2. The volume contains both `whatsapp.db` and `messages.db` plus media files.
3. **Security**
   3.1. The MCP endpoint has no built-in auth; deployment must restrict access at the network layer.

## Rollout / Migration
1. Build the Docker image from the repo root.
2. Run the container with port mapping for `8000` only and a named volume mounted at `/app/whatsapp-bridge/store`.
3. Update MCP client configuration to point to `http://<host>:8000/mcp/`.

## Risks / Trade-offs
1. A single container ties the Go and Python lifecycles; updates to either require rebuilding the image.
2. Without an internal supervisor, a Go crash does not automatically restart the process until the container restarts.

## Open Questions
1. None.
