# Change: Use hash-based media filenames

## Why
Timestamp-based media filenames collide when multiple media messages arrive in the same second, causing downloads to overwrite previous files.

## What Changes
- Generate media filenames from `file_enc_sha256` (lowercase hex) plus the media-type extension.
- If `file_enc_sha256` is missing, compute SHA-256 from the decrypted media bytes at download time and store it back into the message record for future downloads.
- For document media, preserve the original extension when present; otherwise use `.bin`.
- Remove timestamp-based media filenames during ingest.

## Impact
- Affected specs: `media-storage`
- Affected code: `whatsapp-bridge/main.go` (media ingest and filename generation)
