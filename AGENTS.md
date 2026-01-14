# WhatsApp MCP Agent Notes

These notes describe how to build, run, and style code in this repo. They are
written for coding agents working on the WhatsApp MCP server and bridge.

## Repo Layout

- `whatsapp-bridge/`: Go WhatsApp bridge (REST API + WhatsApp client).
- `whatsapp-mcp-server/`: Python MCP server exposed to Claude/Cursor.
- `openspec/`: Spec-driven change proposals and capability specs.
- `.opencode/`: Opencode CLI integration (no build scripts here).

## Commands (Build/Run/Test/Lint)

### Go (whatsapp-bridge)

- Run the bridge (per README):
  - `cd whatsapp-bridge`
  - `go run main.go`
- Build a binary locally:
  - `cd whatsapp-bridge`
  - `go build ./...`
- Tests:
  - No Go test files found in this repo, so there is no single-test command yet.
  - If tests are added later, use Go’s standard pattern: `go test ./...`.
- Lint:
  - No Go lint tooling configured in this repo.

### Python (whatsapp-mcp-server)

- Run the MCP server (per README):
  - `cd whatsapp-mcp-server`
  - `uv run main.py`
- Alternative direct run if `uv` isn’t used locally:
  - `cd whatsapp-mcp-server`
  - `python main.py`
- Tests:
  - No Python test directory or runner configuration found.
  - There is no single-test command available yet.
- Lint:
  - No formatter or linter config (ruff/black/flake8) found.

### OpenSpec

- OpenSpec CLI is used for spec changes (see `openspec/AGENTS.md`).
- Only use it when the request matches the spec-driven workflow triggers.

### Cursor/Copilot Rules

- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files
  were found in this repository.

## Code Style Guidelines

### Shared Principles

- Prefer simple, direct implementations; avoid unnecessary abstractions.
- Keep functions focused; break up large functions when possible.
- Use explicit error handling and return meaningful errors or messages.
- Use constants for repeated literal values (paths, URLs, default limits).
- Avoid placeholder logic unless explicitly requested.

### Python (whatsapp-mcp-server)

- **Imports**: standard library first, then third-party, then local modules.
- **Typing**: use `typing` annotations (`Optional`, `List`, `Dict`, `Tuple`).
- **Naming**:
  - `snake_case` for functions and variables.
  - `PascalCase` for classes and dataclasses.
  - `SCREAMING_SNAKE_CASE` for module-level constants.
- **Formatting**:
  - 4-space indentation; no tabs.
  - Keep docstrings on public tool functions and data helpers.
- **Error handling**:
  - Use `try/except` around database and network operations.
  - Return structured error messages for tool responses.
  - Prefer `ValueError` for validation errors and `RuntimeError` for runtime issues.
- **Data modeling**:
  - Use `@dataclass` for structured records passed around internally.
  - Return JSON-serializable structures to MCP tools (dicts/lists/strings).

### Go (whatsapp-bridge)

- **Formatting**: follow `gofmt` output (tabs for indentation).
- **Imports**:
  - Standard library first, blank line, then third-party packages.
  - Use blank imports only when required (e.g., sqlite3 driver).
- **Naming**:
  - `PascalCase` for exported types and functions.
  - `camelCase` for locals and unexported helpers.
- **Errors**:
  - Wrap errors with context using `fmt.Errorf`.
  - Log failures where execution continues; return errors when callers need to act.
- **HTTP handlers**:
  - Validate request bodies early and return clear HTTP status codes.
  - Use JSON response structs for API responses.

## Runtime Notes

- Go module targets `go 1.24.1` (`whatsapp-bridge/go.mod`).
- Python requires `>=3.11` (`whatsapp-mcp-server/pyproject.toml`).
- WhatsApp API bridge listens on `http://localhost:8080/api`.
- Local SQLite databases live under `whatsapp-bridge/store/`.

## Key Paths

- `whatsapp-bridge/store/messages.db`: Message history store.
- `whatsapp-bridge/store/whatsapp.db`: WhatsApp session data.
- `whatsapp-bridge/store/<chat>/`: Media downloads per chat.

## Safety and Operational Tips

- The bridge holds personal WhatsApp data locally; avoid logging secrets.
- Message history sync can be large; avoid expensive operations in tight loops.
- Media downloads write files under `whatsapp-bridge/store/<chat>/`.

## When Editing

- Prefer small, incremental edits over large rewrites.
- Keep Go and Python responsibilities separate (bridge vs MCP server).
- If you add new tooling, update this file with the new commands.

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->
