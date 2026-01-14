# Project Context

## Purpose
Provide an MCP server that lets LLMs read/search/send WhatsApp messages and media via a local WhatsApp Web bridge, with data stored in SQLite.

## Tech Stack
- Go (Go 1.24.1) bridge using `whatsmeow` and `go-sqlite3`
- Python 3.11 MCP server using `mcp`, `httpx`, `requests`
- SQLite for local message/media storage

## Project Conventions

### Code Style
Not documented in the repository.

### Architecture Patterns
- Two-component architecture: Go WhatsApp bridge + Python MCP server
- Bridge exposes REST endpoints; Python server calls them and reads SQLite directly

### Testing Strategy
Not documented in the repository.

### Git Workflow
Not documented in the repository.

## Domain Context
Personal WhatsApp account access via WhatsApp Web multi-device API, exposing controlled LLM tooling for messaging and media access.

## Important Constraints
- Requires Go and Python (project uses Python 3.11)
- FFmpeg required for voice message conversion
- Windows builds require CGO enabled for `go-sqlite3`

## External Dependencies
- WhatsApp Web API via `whatsmeow`
- MCP integration (Claude Desktop/Cursor)
- SQLite
- FFmpeg (audio conversion)
