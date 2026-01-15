## 1. Implementation
- [x] 1.1 Add a WhatsApp contacts DB path constant and auth-gated cache loader in `whatsapp-mcp-server/whatsapp.py`.
- [x] 1.2 Build an in-memory contact map keyed by full JID with the defined name priority.
- [x] 1.3 Apply cache-based name resolution for `sender_name` and `chat.name` across MCP response paths.

## 2. Validation
- [x] 2.1 Run the MCP server and call `list_messages`/`list_chats` to confirm contact names are returned.
