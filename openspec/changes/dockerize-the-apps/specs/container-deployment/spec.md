## ADDED Requirements
### Requirement: Docker Build Assets
The system SHALL include a repo-root `Dockerfile`, entrypoint script, and `.dockerignore` required to build and run the stack in a single container.

#### Scenario: Docker artifacts exist
- **WHEN** the repository is checked out
- **THEN** a `Dockerfile`, entrypoint script, and `.dockerignore` are present at the documented paths

### Requirement: Single-Container Runtime
The system SHALL provide a Docker image that runs both the Go WhatsApp bridge and the Python MCP server in one container.

#### Scenario: Container start
- **WHEN** the Docker container starts
- **THEN** the Go bridge process is running and the MCP server is running in the foreground

### Requirement: Streamable HTTP MCP Transport
The system SHALL expose the MCP server via Streamable HTTP at `/mcp/` on port `8000`.

#### Scenario: MCP HTTP connection
- **WHEN** an MCP client connects to `http://<host>:8000/mcp/`
- **THEN** the MCP server responds using Streamable HTTP

### Requirement: MCP HTTP Bind Address
The system SHALL bind the MCP server to `0.0.0.0:8000` so it is reachable via Docker port mappings.

#### Scenario: Host access
- **WHEN** Docker maps host port `8000` to container port `8000`
- **THEN** the MCP endpoint is reachable from the host network

### Requirement: Bridge REST API Internal Access
The system SHALL make the Go bridge REST API available on port `8080` inside the container for the MCP server to use (host port exposure is not required).

#### Scenario: Internal bridge access
- **WHEN** the MCP server sends HTTP requests to `http://localhost:8080/api` inside the container
- **THEN** the bridge REST API accepts requests

### Requirement: Persistent WhatsApp Store Path
The system SHALL store WhatsApp auth/session data and message history under `/app/whatsapp-bridge/store` and treat the directory as a Docker volume mount target.

#### Scenario: Volume persistence
- **WHEN** a Docker volume is mounted at `/app/whatsapp-bridge/store`
- **THEN** WhatsApp auth and message data persist across container restarts

### Requirement: FFmpeg Availability
The Docker image SHALL include `ffmpeg` for audio conversion.

#### Scenario: Audio conversion
- **WHEN** an audio file requires conversion for `send_audio_message`
- **THEN** `ffmpeg` is available in the container runtime

### Requirement: Debian-Based Runtime Image
The runtime image SHALL be Debian-based to support CGO, SQLite, and FFmpeg dependencies.

#### Scenario: Base image choice
- **WHEN** the Docker image is built
- **THEN** the runtime stage uses a Debian-based Python image
