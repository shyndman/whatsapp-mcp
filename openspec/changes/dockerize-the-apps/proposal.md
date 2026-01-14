# Change: Dockerize WhatsApp MCP stack

## Current State
1. The Go WhatsApp bridge is started manually (for example, `go run main.go`) and runs as a standalone process under `whatsapp-bridge/`.
2. The Python MCP server is started separately (for example, `uv run main.py`) and currently uses STDIO transport for MCP connections.
3. The Python MCP server assumes the Go bridge REST API is reachable at `http://localhost:8080/api` and reads SQLite data directly from `whatsapp-bridge/store/messages.db`.
4. Auth/session data is stored under `whatsapp-bridge/store/whatsapp.db`, and media downloads are stored under `whatsapp-bridge/store/<chat>/`.
5. Users must install and manage Go, Python, uv, and FFmpeg locally, and must coordinate two processes manually.

## Why
1. A single-container deployment reduces setup complexity and eliminates the need for local Go/Python/uv installations.
2. Streamable HTTP MCP allows the MCP server to be reachable over the network instead of STDIO-only local process spawning.
3. Persisting the WhatsApp auth/session state inside a Docker volume ensures auth continuity across container restarts.
4. A containerized runtime is easier to deploy in cloud or remote environments while keeping all data local to a mounted volume.

## What Changes
1. Add a repo-root Docker build that produces one image containing both services.
   1.1. The Docker build uses a multi-stage build: a Go builder stage and a Python runtime stage.
   1.2. The runtime stage is Debian-based to keep CGO, SQLite, and FFmpeg support straightforward.
2. Add an entrypoint script that runs the Go bridge in the background and the MCP server in the foreground.
   2.1. The Go bridge runs with working directory `whatsapp-bridge/` so `store/` is resolved correctly.
   2.2. The MCP server runs with working directory `whatsapp-mcp-server/` using `uv run`.
3. Switch the MCP server transport to Streamable HTTP and bind it to `0.0.0.0:8000`.
   3.1. The MCP endpoint is reachable at `/mcp/`.
4. Expose the MCP HTTP server on port `8000` (the Go bridge REST API stays internal to the container and is not published by default).
5. Declare `/app/whatsapp-bridge/store` as the persistence path for a Docker volume.
6. Include `ffmpeg` in the image so `send_audio_message` conversions work without host dependencies.
7. Add a `.dockerignore` to keep local `.venv` and build artifacts out of image builds.
8. Update `README.md` with Docker build/run steps and the MCP client configuration for HTTP transport.

## Impact
1. Affected specs: `container-deployment`.
2. Affected code and assets:
   2.1. `whatsapp-bridge/` (runtime path expectations and Go binary packaging).
   2.2. `whatsapp-mcp-server/` (MCP transport change and runtime entrypoint).
   2.3. Repo-root Docker files (`Dockerfile`, entrypoint, `.dockerignore`).
   2.4. `README.md` (new Docker usage instructions).
3. User-facing changes:
   3.1. MCP clients must connect to `http://<host>:8000/mcp/` instead of STDIO.
   3.2. The Go bridge REST API remains internal to the container (no host port mapping by default).
4. Operational changes:
   4.1. Docker is the only required dependency for running the stack.
   4.2. All WhatsApp data persists in a Docker volume mounted to `/app/whatsapp-bridge/store`.

## Success Criteria
1. `docker build` completes without errors and produces a runnable image.
2. `docker run` starts the Go bridge, prints a QR code on first run, and starts the MCP server on port `8000`.
3. `curl -I http://localhost:8000/mcp/` returns an HTTP response from the MCP server.
4. Stopping and restarting the container with the same volume preserves `whatsapp-bridge/store/whatsapp.db` and `messages.db`.
