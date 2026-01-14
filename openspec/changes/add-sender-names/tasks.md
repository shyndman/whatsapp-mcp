## 1. Implementation
- [ ] 1.1 Add sender-name resolution helper and extend message/chat models with `sender_name` and `last_sender_name`.
- [ ] 1.2 Update `list_messages` to return structured message objects including `sender_name`.
- [ ] 1.3 Update chat listing helpers (`list_chats`, `get_chat`, `get_contact_chats`, `get_direct_chat_by_contact`) to include `last_sender_name`.
- [ ] 1.4 Update MCP tool docs/types in `whatsapp-mcp-server/main.py` to describe new fields.
- [ ] 1.5 Validate via manual calls to `list_messages` and `list_chats`.
