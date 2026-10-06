# Changelog

## Unreleased — Key Sovereignty POC (2026-10-06)

- Repositioned as Vendor-agnostic HSM, PKCS#11 and Key Sovereignty Platform.
- Preserved local HSM console changes and reconciled origin/main on the feature branch.
- Added reference-only KEK/DEK/envelope models and capability-based local AES-256-GCM.
- Added explicit ephemeral virtual wrapping and authenticated ciphertext-only packages.
- Added vendor-neutral External BYOK contracts and offline Huawei adapter validation.
- Added Key Sovereignty, Cloud Integration, Keys and Audit/Diagnostics; restored Object Explorer.
- Added closed-schema protection/BYOK audit, negative crypto, no-secret-log and GUI tests.
- Retained standalone Key Manager and Sign & Verify; native modules require explicit selection.
- No native wrapping, upload, credentials, main merge, new tag or release. Existing installers predate this POC.

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
