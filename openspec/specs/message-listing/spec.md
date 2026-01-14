# message-listing Specification

## Purpose
TBD - created by archiving change add-sender-names. Update Purpose after archive.
## Requirements
### Requirement: Message listings include sender names
The system SHALL return `list_messages` results as message objects containing `id`, `chat_jid`, `chat_name`, `sender`, `sender_name`, `content`, `timestamp`, `is_from_me`, and `media_type`.

#### Scenario: Sender name resolved
- **WHEN** `list_messages` is called for a message whose sender has a known contact name
- **THEN** the result includes `sender_name` set to that contact name and `sender` set to the sender identifier

#### Scenario: Sender name fallback
- **WHEN** `list_messages` is called for a message whose sender has no known contact name
- **THEN** the result includes `sender_name` set to the sender identifier

