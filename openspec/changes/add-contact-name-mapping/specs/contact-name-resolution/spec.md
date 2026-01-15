## ADDED Requirements

### Requirement: Load contact cache after authentication
The MCP server SHALL load contact data from `whatsmeow_contacts` (`their_jid`, `full_name`, `business_name`, `first_name`, `push_name`) into an in-memory map the first time a request is handled after the device is authenticated.

#### Scenario: Authenticated cache load
- **GIVEN** a row exists in `whatsmeow_device`
- **WHEN** the MCP server handles a request and the contact cache is uninitialized
- **THEN** the server loads all contacts into memory.

### Requirement: Contact name selection
The MCP server SHALL choose a display name from each contact using the priority order: `full_name`, `business_name`, `first_name`, then `push_name`, ignoring empty values.

#### Scenario: Name priority
- **GIVEN** a contact with multiple non-empty name fields
- **WHEN** the contact is loaded into the cache
- **THEN** the highest-priority non-empty field is used as the display name.

### Requirement: Cache keying by full JID
The MCP server SHALL index each contact by `their_jid` to support lookups by full JID.

#### Scenario: Lookup by full JID
- **GIVEN** a contact stored as `their_jid`
- **WHEN** a lookup uses the full JID value
- **THEN** the cached display name is returned.

### Requirement: Apply contact names to MCP responses
The MCP server SHALL populate missing `sender_name` and `chat.name` values for non-group chats using the contact cache without overriding existing non-empty values.

#### Scenario: Fill missing sender name
- **GIVEN** a message where `sender_name` is empty and the sender JID is not a group (`@g.us`)
- **WHEN** the response is built
- **THEN** the response includes the cached contact name.

#### Scenario: Fill missing chat name
- **GIVEN** a one-on-one chat where `chat.name` is empty
- **WHEN** the chat response is built
- **THEN** the response includes the cached contact name.

#### Scenario: Preserve existing chat name
- **GIVEN** a chat where `chat.name` is already populated
- **WHEN** the chat response is built
- **THEN** the existing name is returned unchanged.
