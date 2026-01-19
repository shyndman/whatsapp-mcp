# WhatsApp MCP

> This fork aims to make the MCP server generally more usable by trimming tool surface
> (and context usage) while also enabling parallel sub-agent workflows (see
> `partition_messages` and `list_messages`).

> ⚠️☠️🚨 **Security note**: This MCP ingests messages from untrusted sources — other
> people. If connected to an agent with outbound capabilities (web requests, email, other
> messaging tools, this MCP's `send_message`), a malicious message could potentially
> instruct the agent to exfiltrate conversation contents. Consider running read-only
> and/or isolating this MCP from agents with sensitive tool access.

WhatsApp MCP is a two-process stack that exposes a Model Context Protocol (MCP) server for WhatsApp operations. It bundles:

- `whatsapp-bridge/`: Go-based WhatsApp bridge exposing a REST API on `http://localhost:8080/api`.
- `whatsapp-mcp-server/`: Python MCP server exposing Streamable HTTP on `http://localhost:8000/mcp/`.

The Docker image runs both services in one container and persists WhatsApp data under `/app/whatsapp-bridge/store`.

## Requirements

Local development:

- Go 1.24.1+
- Python 3.11+
- `uv` (recommended) for Python dependencies

Container runtime:

- Docker 24+
- Docker Compose v2 (for the compose example below)

## Local development

Run the bridge:

```bash
cd whatsapp-bridge
go run main.go
```

Run the MCP server (in another shell):

```bash
cd whatsapp-mcp-server
uv run main.py
```

The MCP server connects to the bridge at `http://localhost:8080/api`.

## Docker

Build the image:

```bash
docker build -t whatsapp-mcp:local .
```

Run the container (exposes MCP on port 8000):

```bash
docker run --rm -p 8000:8000 \
  -v "$(pwd)/data/store:/app/whatsapp-bridge/store" \
  whatsapp-mcp:local
```

The bind mount persists WhatsApp session data and message databases between runs.

## Docker Compose (bind mount for SQLite data)

```yaml
services:
  whatsapp-mcp:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data/store:/app/whatsapp-bridge/store
```

This bind mount stores the SQLite files (`whatsapp-bridge/store/messages.db`, `whatsapp-bridge/store/whatsapp.db`) on the host at `./data/store`.

## MCP tools

The MCP server exposes the following tools (defined in `whatsapp-mcp-server/main.py`).

### `search_contacts`

Searches contacts by name or phone number.

Parameters:

- `query` (string): Search term.

Returns:

- List of contact objects (dicts) from the bridge.

### `list_messages`

Lists messages with filtering and optional context.

Parameters:

- `message_id` (string, optional): Fetch a specific message with context; other filters ignored.
- `after` / `before` (ISO-8601 string, optional): Time bounds.
- `sender_phone_number` (string, optional): Filter by sender.
- `chat_jid` (string, optional): Filter by chat.
- `query` (string, optional): Full-text search.
- `cursor` (string, optional): Paging cursor (base64-url).
- `snapshot_at` (string, optional): Bound results to a snapshot.
- `limit` (int, optional, default 20): Page size.
- `page` (int, optional, default 0): Page number (ignored if cursor is set).
- `include_context` (bool, optional, default true): Include surrounding messages.
- `context_before` / `context_after` (int, optional, default 1): Context window.

Returns:

- List of messages with fields: `id`, `chat_jid`, `chat_name`, `sender`, `sender_name`, `content`, `timestamp`, `is_from_me`, `media_type`.

### `partition_messages`

Plans deterministic partitions for large message listings, so callers can set up parallel sub-agent calls.

Parameters:

- `after` / `before` (ISO-8601 string, optional): Time bounds.
- `sender_phone_number` (string, optional): Filter by sender.
- `chat_jid` (string, optional): Filter by chat.
- `query` (string, optional): Full-text search.
- `include_context` (bool, optional, default true): Include surrounding messages.
- `partition_size` (int, optional, default 1000): Base message count per partition.

Returns:

- Dict with `total_count`, `snapshot_at`, and `partitions` entries.

### `list_chats`

Lists chats with filters and sorting.

Parameters:

- `query` (string, optional): Name or JID search.
- `limit` (int, optional, default 20): Page size.
- `page` (int, optional, default 0): Page number.
- `include_last_message` (bool, optional, default true): Include last message.
- `sort_by` (string, optional, default `last_active`): `last_active` or `name`.
- `contact_jid` (string, optional): Filter by contact JID.

Returns:

- List of chat objects with fields: `jid`, `name`, `last_message_time`, `last_message`, `last_sender`, `last_sender_name`, `last_is_from_me`.

### `get_chat`

Fetches chat metadata by JID or sender phone number.

Parameters:

- `chat_jid` (string, optional): Chat JID.
- `sender_phone_number` (string, optional): Phone number for direct chat lookup.
- `include_last_message` (bool, optional, default true): Include last message.

Returns:

- A chat object (same shape as `list_chats`) or `null` if none found.

### `send`

Sends a text message or media file.

> ⚠️ **Send tool gating**: The `send` tool is only exposed when `WHATSAPP_ALLOW_SEND=true` is set in the MCP server environment.

Parameters:

- `recipient` (string): Phone number (country code, no `+`) or group JID (`123@g.us`).
- `message` (string, optional): Message text.
- `media_path` (string, optional): Absolute path to media file.

Returns:

- Dict with `success` (bool) and `message` (status string).

### `download_media`

Downloads media from a message.

Parameters:

- `message_id` (string): Message ID.
- `chat_jid` (string): Chat JID.

Returns:

- Dict with `success` (bool), `message` (status string), and `file_path` when successful.
