## ADDED Requirements

### Requirement: Partition planning tool
The system SHALL provide a `partition_messages` tool that accepts `after`, `before`, `sender_phone_number`, `chat_jid`, `query`, `include_context`, and `partition_size`, and returns `total_count`, `snapshot_at`, and an ordered list of partitions. Each partition SHALL include the original filters plus `limit`, `cursor`, and `snapshot_at` values that can be passed directly to `list_messages`.

#### Scenario: Partition sizing by count
- **GIVEN** 2,500 messages match the provided filters
- **WHEN** `partition_messages` is called with `partition_size` set to 1000
- **THEN** the response includes `total_count` 2500 and three partitions with limits 1000, 1000, and 500.

#### Scenario: Filter propagation
- **GIVEN** `partition_messages` is called with `chat_jid` and `after`
- **WHEN** partitions are returned
- **THEN** each partition includes the same `chat_jid` and `after` values.

#### Scenario: Initial cursor
- **GIVEN** `partition_messages` returns partitions
- **WHEN** inspecting the first partition
- **THEN** the partition cursor is `null` to indicate paging from the newest message.

### Requirement: Stable snapshot planning
The system SHALL compute `snapshot_at` as the latest message timestamp that matches the provided filters and ensure all partitions are scoped to messages with `timestamp <= snapshot_at`.

#### Scenario: Snapshot stability
- **GIVEN** new messages arrive after `partition_messages` returns
- **WHEN** `list_messages` is called using the returned `snapshot_at`
- **THEN** only messages at or before `snapshot_at` are returned.

#### Scenario: Empty result snapshot
- **GIVEN** no messages match the provided filters
- **WHEN** `partition_messages` is called
- **THEN** the response includes `total_count` 0, `snapshot_at` set to `null`, and an empty partitions list.

### Requirement: Default partition size
The system SHALL default `partition_size` to 1000 when it is omitted.

#### Scenario: Default partition sizing
- **GIVEN** `partition_messages` is called without `partition_size`
- **WHEN** partitions are generated
- **THEN** each partition uses a limit of 1000, except the final partition.

### Requirement: Include-context propagation
The system SHALL pass the `include_context` input through to every partition without altering the base count or cursor generation.

#### Scenario: Include-context passthrough
- **GIVEN** `partition_messages` is called with `include_context` set to true
- **WHEN** partitions are returned
- **THEN** each partition includes `include_context` set to true.

### Requirement: Input validation
The system SHALL reject `partition_size` values less than 1 with a validation error message indicating that the value must be positive.

#### Scenario: Invalid partition size
- **GIVEN** `partition_messages` is called with `partition_size` set to 0
- **WHEN** the request is validated
- **THEN** the tool returns a validation error indicating `partition_size` must be positive.
