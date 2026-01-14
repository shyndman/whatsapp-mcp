# Change: Add sender names to list outputs

## Why
The MCP list outputs expose sender identifiers without human-readable names, forcing clients to perform manual contact lookups.

## What Changes
- Add `sender_name` to each `list_messages` result alongside `sender`.
- Add `last_sender_name` to each `list_chats` result alongside `last_sender`.
- Ensure name resolution falls back to the sender identifier when no contact name is available.

## Impact
- Affected specs: `message-listing`, `chat-listing` (new capabilities)
- Affected code: `whatsapp-mcp-server/whatsapp.py`, `whatsapp-mcp-server/main.py`
- Behavior: `list_messages` output becomes structured message objects instead of formatted strings.
