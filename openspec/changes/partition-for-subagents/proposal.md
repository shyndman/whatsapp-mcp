# Change: Partition message listings for subagents

## Why
Agents need deterministic, count-based partitions of `list_messages` results so they can run subagents in parallel without overlapping or probing. Offset paging forces discovery queries and can drift as new messages arrive.

## What Changes
- Add a `partition_messages` tool that returns stable, cursor-based partitions for any `list_messages` filter set.
  - Inputs: `after`, `before`, `sender_phone_number`, `chat_jid`, `query`, `include_context`, and `partition_size` (default 1000).
  - Output: `total_count`, `snapshot_at` (nullable), and an ordered list of partitions. Each partition includes the original filters, `limit`, `cursor` (null for the first partition), and `snapshot_at`.
- Extend `list_messages` with optional `cursor` and `snapshot_at` inputs for deterministic paging.
  - When `cursor` is provided, order by `timestamp DESC, id DESC` and ignore `page`.
  - Treat the cursor as an exclusive bound (`timestamp`/`id` strictly older than the cursor).
  - When `snapshot_at` is provided, all returned messages (including context) are limited to `timestamp <= snapshot_at`.
- Add a SQLite index on `(chat_jid, timestamp, id)` to keep cursor paging fast for chat-scoped partitions.

## Scope / Compatibility
- Backward compatible: existing `list_messages` calls without `cursor` behave exactly as today.
- `partition_messages` is additive; no existing tools are removed.
- `message_id` handling remains unchanged and is not supported by `partition_messages`.

## Impact
- Affected specs: `message-listing`, new `message-partitioning`.
- Affected code: `whatsapp-mcp-server/main.py`, `whatsapp-mcp-server/whatsapp.py`, `whatsapp-bridge/main.go`, `README.md`.
