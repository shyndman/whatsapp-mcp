## ADDED Requirements

### Requirement: Cursor-based paging
The system SHALL accept optional `cursor` and `snapshot_at` parameters on `list_messages`. When `cursor` is provided, the system SHALL return messages ordered by `timestamp` descending then `id` descending, strictly older than the cursor, and constrained to `timestamp <= snapshot_at` when `snapshot_at` is supplied. When `cursor` is provided, `page` SHALL be ignored.

#### Scenario: Cursor paging with snapshot
- **GIVEN** a `cursor` and `snapshot_at` from `partition_messages`
- **WHEN** `list_messages` is called with those values and `limit=1000`
- **THEN** the response contains at most 1000 messages older than the cursor and no messages newer than `snapshot_at`.

#### Scenario: Cursor overrides page
- **GIVEN** `list_messages` is called with both `cursor` and `page`
- **WHEN** the request is processed
- **THEN** the results are based on `cursor` and `page` is ignored.

#### Scenario: Cursor omitted
- **GIVEN** `list_messages` is called without a `cursor`
- **WHEN** the request is processed
- **THEN** the results start from the newest message that matches the filters.

### Requirement: Cursor token decoding
The system SHALL treat `cursor` as a base64-url encoded JSON object with keys `ts` (ISO-8601 timestamp) and `id` (message id), and SHALL reject invalid cursors with a validation error.

#### Scenario: Invalid cursor
- **GIVEN** `list_messages` is called with a malformed `cursor`
- **WHEN** the cursor is decoded
- **THEN** the request returns a validation error describing the invalid cursor.

### Requirement: Snapshot applies to context
When `snapshot_at` is provided, all messages returned by `list_messages` (including context messages) SHALL have `timestamp <= snapshot_at`.

#### Scenario: Snapshot bounds context
- **GIVEN** `list_messages` is called with `snapshot_at` and `include_context=true`
- **WHEN** the response is generated
- **THEN** no returned message has a timestamp after `snapshot_at`.
