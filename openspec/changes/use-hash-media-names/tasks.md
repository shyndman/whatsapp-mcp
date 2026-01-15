## 1. Implementation
- [ ] 1.1 Add helpers to hex-encode `file_enc_sha256` and build filenames by media type
- [ ] 1.2 Update media ingest to store hash-based filenames (image/video/audio/document)
- [ ] 1.3 Preserve document extensions when present; otherwise store `.bin`
- [ ] 1.4 If `file_enc_sha256` is missing during download, compute SHA-256 from the decrypted media bytes, persist it in `messages.file_enc_sha256`, and rebuild the filename
- [ ] 1.5 Ensure download path uses the updated filename and does not overwrite other media
- [ ] 1.6 Manual validation: send two images within the same second, download both, and verify two distinct filenames on disk and in `messages.filename`
