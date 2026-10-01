# Changelog

## 0.2.0 - 2026-09-23

- Rebuilt project around domain/application/infrastructure/presentation boundaries.
- Added isolated one-shot PKCS#11 worker protocol.
- Added background GUI worker threads for provider load and refresh.
- Added persistent virtual slots/tokens with atomic state writes.
- Added versioned PBKDF2-SHA256 PIN hashing.
- Added drag-and-drop PKCS#11 module loading.
- Added unit tests and stricter public DTO separation from private auth metadata.
