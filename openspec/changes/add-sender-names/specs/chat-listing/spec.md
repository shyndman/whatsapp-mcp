## ADDED Requirements
### Requirement: Chat listings include last sender names
The system SHALL return `list_chats` results as chat objects containing `jid`, `name`, `last_message_time`, `last_message`, `last_sender`, `last_sender_name`, and `last_is_from_me`.

#### Scenario: Last sender name resolved
- **WHEN** `list_chats` returns a chat with a last sender that has a known contact name
- **THEN** the result includes `last_sender_name` set to that contact name

#### Scenario: Last sender name fallback
- **WHEN** `list_chats` returns a chat with a last sender that has no known contact name
- **THEN** the result includes `last_sender_name` set to `last_sender`

#### Scenario: No last sender
- **WHEN** `list_chats` returns a chat with no last sender
- **THEN** the result includes `last_sender_name` set to `null`
