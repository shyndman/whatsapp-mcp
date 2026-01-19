## 1. Implementation
- [x] 1.1 Add `CREATE INDEX IF NOT EXISTS messages_chat_time_id ON messages(chat_jid, timestamp, id)` in `whatsapp-bridge/main.go` during store initialization.
- [x] 1.2 Add cursor encode/decode helpers in `whatsapp-mcp-server/whatsapp.py` (base64-url JSON with `ts` and `id`) and centralized error messages for invalid cursors.
- [x] 1.3 Extend `list_messages` in `whatsapp-mcp-server/whatsapp.py` to accept `cursor` and `snapshot_at`, ignore `page` when `cursor` is provided, and apply the cursor + snapshot filters to the SQL query.
- [x] 1.4 Ensure `list_messages` applies `snapshot_at` filtering to context messages when `include_context=true`.
- [x] 1.5 Update the MCP tool wrapper in `whatsapp-mcp-server/main.py` to surface the new `cursor` and `snapshot_at` parameters with docstrings and logging fields.
- [x] 1.6 Implement `partition_messages` in `whatsapp-mcp-server/whatsapp.py`: validate `partition_size`, compute `snapshot_at`, handle empty results, count matches, and generate ordered partitions with `cursor` and `snapshot_at`.
- [x] 1.7 Add the MCP tool wrapper for `partition_messages` in `whatsapp-mcp-server/main.py` with full parameter documentation.
- [x] 1.8 Update `README.md` tool documentation to include `partition_messages` and the new `list_messages` parameters.
- [ ] 1.9 Manual validation: run `partition_messages` with `partition_size=2`, confirm `list_messages` returns non-overlapping results for `include_context=false`, confirm `snapshot_at` is `null` when no matches, and confirm invalid cursor inputs raise a validation error.
