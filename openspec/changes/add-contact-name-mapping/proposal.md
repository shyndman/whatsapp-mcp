# Change: Map contact names in MCP responses

## Why
Contact names are stored in the WhatsApp contacts database, but MCP responses only surface what is already present in `messages.db`. This results in missing `sender_name` and `chat.name` values when chat rows lack names.

## What Changes
- Load WhatsApp contacts from `whatsapp.db` in the same `whatsapp-bridge/store` directory as `messages.db` (mirroring the existing `MESSAGES_DB_PATH` resolution), after authentication on first request.
- Use the cache to fill missing `sender_name` and `chat.name` values for one-on-one chats (sender IDs are full JIDs).
- Resolve display names from `whatsmeow_contacts` fields `their_jid`, `full_name`, `business_name`, `first_name`, `push_name` with priority `full_name`, `business_name`, `first_name`, `push_name`.

## Impact
- Affected specs: `contact-name-resolution` (new).
- Affected code: `whatsapp-mcp-server/whatsapp.py`.
