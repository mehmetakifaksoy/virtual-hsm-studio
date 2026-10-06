# Changelog

## 0.5.0-alpha.2 - 2026-10-07

- Positioned as a Vendor-agnostic HSM, PKCS#11 and Key Sovereignty Platform.
- Added real local AES-256-GCM, fresh DEKs and authenticated versioned envelope packages.
- Added explicitly virtual, process-memory KEK wrapping and capability checks.
- Added vendor-neutral Cloud KMS Integration with offline External BYOK contracts and mock adapter.
- Added Key Sovereignty, Cloud KMS Integration, Keys and Audit/Diagnostics console pages.
- Added closed-schema protection/BYOK audit with no secret payloads.
- Preserved provider, slot/token, session, object, key management and signing workflows.
- Added negative crypto, no-secret-log, GUI and packaged executable validation.
- Published three Windows installers, portable ZIPs and SHA-256 checksums.
- Native wrapping, durable KEK recovery, live cloud connections and uploads remain unimplemented.

## 0.4.0-beta.2

- Separate Windows HSM Studio, Key Manager and Sign & Verify applications, installers and portable packages.
- Simplified light console with dark navigation; clear demo/external-provider distinction and collapsed advanced controls.
- Removed key generation from the slot-management screen.
- AES/RSA generation and metadata listing in Key Manager.
- Detached RSA PKCS#1 v1.5/SHA-256 signing, PEM public-key export and independent verification.
- Fixed signing dialog QDialog.finished signal collision that left key loading at Working.
- Corrected Key Manager heading contrast and legacy launcher routing.
- Documented installation without Python, source setup with short virtual-environment paths and shared token configuration.
- Added regression and SoftHSM2 integration coverage for signing, tampering and wrong keys.

## 0.4.0-beta.1

- Guided Virtual HSM onboarding, modular console pages and initial Windows installer.
- Isolated native workers and sanitized build PATH to prevent foreign ICU DLL collection.

## 0.2.0 - 2026-09-23

- Rebuilt project around domain/application/infrastructure/presentation boundaries.
- Added isolated one-shot PKCS#11 worker protocol.
- Added background GUI worker threads for provider load and refresh.
- Added persistent virtual slots/tokens with atomic state writes.
- Added versioned PBKDF2-SHA256 PIN hashing.
- Added drag-and-drop PKCS#11 module loading.
- Added unit tests and stricter public DTO separation from private auth metadata.
