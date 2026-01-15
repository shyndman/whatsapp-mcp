## ADDED Requirements
### Requirement: Media filenames are hash-based
The system SHALL store media filenames derived from `file_enc_sha256` (lowercase hex) with a media-type extension.

#### Scenario: Image filename uses hash
- **WHEN** an image message is stored
- **THEN** the filename is `<file_enc_sha256-hex>.jpg` and is stable across downloads

#### Scenario: Video filename uses hash
- **WHEN** a video message is stored
- **THEN** the filename is `<file_enc_sha256-hex>.mp4`

#### Scenario: Audio filename uses hash
- **WHEN** an audio message is stored
- **THEN** the filename is `<file_enc_sha256-hex>.ogg`

#### Scenario: Document filename preserves extension
- **WHEN** a document message is stored with an original filename extension
- **THEN** the filename is `<file_enc_sha256-hex>.<original_extension>`

#### Scenario: Document filename fallback extension
- **WHEN** a document message is stored without an original extension
- **THEN** the filename is `<file_enc_sha256-hex>.bin`

### Requirement: Missing hash is computed at download time
If `file_enc_sha256` is missing, the system SHALL compute it from the decrypted media bytes during download and persist it for future requests.

#### Scenario: Hash computed on download
- **WHEN** a media download is requested for a message with `file_enc_sha256` missing
- **THEN** the system computes SHA-256 from the decrypted media bytes, stores it in `messages.file_enc_sha256`, and names the downloaded file using the computed hash
