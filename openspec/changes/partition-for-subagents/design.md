## Context
- Agents need to split `list_messages` results ahead of time for parallel subagents.
- `list_messages` currently uses offset paging and does not expose totals or stable snapshots.

## Goals / Non-Goals
- Goals:
  - Provide a planning tool that returns deterministic partitions for any `list_messages` filter set.
  - Support stable snapshot paging via cursor tokens and a snapshot timestamp.
  - Keep changes minimal and backward compatible for existing `list_messages` usage.
- Non-Goals:
  - Introduce full-text indexing or rework the storage schema.
  - Replace the existing `page`/`limit` API for `list_messages`.
  - Add orchestration logic for running subagents.

## Tool Contracts
### `partition_messages`
Inputs:
- `after`/`before`: ISO-8601 timestamps (optional).
- `sender_phone_number`, `chat_jid`, `query`: same semantics as `list_messages`.
- `include_context`: optional; when true, partitions may overlap due to context expansion.
- `partition_size`: positive integer; default 1000.

Output:
- `total_count`: number of base messages that match the filters (context is not included in counts).
- `snapshot_at`: ISO-8601 timestamp of the newest matching message or `null` when no messages match.
- `partitions`: ordered newest-to-oldest. Each partition includes the input filters, `limit`, `cursor` (null for the first partition), and `snapshot_at`.

### `list_messages` (cursor paging)
- New optional inputs: `cursor` and `snapshot_at`.
- When `cursor` is provided, order by `timestamp DESC, id DESC` and ignore `page`.
- Cursor is an exclusive bound: return messages older than the cursor.
- When `snapshot_at` is provided, all returned messages (including context) must have `timestamp <= snapshot_at`.

## Cursor Token
- Format: base64-url encoded JSON with keys `ts` (ISO-8601 timestamp string) and `id` (message id string).
- `cursor` omitted or `null` means start from the newest message.
- Invalid or undecodable cursors raise `ValueError` with a clear message.

## SQL Query Strategy
### Base filters (shared)
- `after`: `messages.timestamp > ?`
- `before`: `messages.timestamp < ?`
- `sender_phone_number`: `messages.sender = ?`
- `chat_jid`: `messages.chat_jid = ?`
- `query`: `LOWER(messages.content) LIKE LOWER(?)`

### Snapshot calculation
1. Compute `snapshot_at` with `SELECT MAX(messages.timestamp)` using the same filters.
2. If `snapshot_at` is `NULL`, return `total_count=0` and `partitions=[]`.
3. Otherwise, add `messages.timestamp <= snapshot_at` to every count and partition query.

### Cursor paging clause
- Add an exclusive bound for descending order:
  - `(messages.timestamp < :cursor_ts) OR (messages.timestamp = :cursor_ts AND messages.id < :cursor_id)`

### Partition generation
1. Count the base matches with `SELECT COUNT(1)` (same filters + `timestamp <= snapshot_at`).
2. For each partition, run the base query with `ORDER BY timestamp DESC, id DESC` and `LIMIT partition_size`.
3. Set the partition cursor to the last row returned.
4. Repeat until fewer than `partition_size` rows are returned.

## Include Context Behavior
- `include_context` is configurable and passed through by the planner.
- Partition counts and cursor generation are based on base messages only.
- If `include_context=true`, returned messages can overlap across partitions by design.

## Indexing
- Add `CREATE INDEX IF NOT EXISTS messages_chat_time_id ON messages(chat_jid, timestamp, id)`.
- This index accelerates chat-scoped partitions and cursor paging.

## Risks / Trade-offs
- Planning requires a `COUNT(*)` plus cursor walks, which may be heavy for very large history syncs.
- The `(chat_jid, timestamp, id)` index speeds chat-scoped pagination but provides limited benefit for query-only or sender-only filters.
- LIKE-based `query` filters remain unindexed; large text searches may be slow without FTS.

## Migration Plan
- Add index creation in bridge startup so existing databases backfill automatically.
- Keep `page`/`limit` behavior untouched when `cursor` is not provided.

## Open Questions
- Should we add a global `(timestamp, id)` index if non-chat queries become a bottleneck?
