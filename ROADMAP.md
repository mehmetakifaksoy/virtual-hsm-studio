# Virtual HSM Studio Roadmap

Positioning: **Vendor-agnostic HSM, PKCS#11 and Key Sovereignty Platform**.

## Key Sovereignty milestone — unreleased POC

Implemented: local AES-256-GCM, fresh DEKs, authenticated versioned envelopes,
virtual memory KEK wrap/unwrap, Key Sovereignty and Cloud KMS Integration pages,
offline External BYOK contracts and Cloud KMS fake, safe protection/BYOK audit,
negative crypto, no-secret-log and GUI workflow tests.

Before production or durable-data release:

- Native PKCS#11 wrapping with authenticated sessions, mechanism/policy checks and non-extractable KEKs.
- Recoverable key lifecycle, rotation, backup/recovery and explicit retention policy.
- GUI decryption, background/streaming processing and atomic package publication.
- Live Cloud KMS adapter with injected ephemeral authentication and region/API integration tests.
- Ciphertext-only upload port accepting validated envelopes; no plaintext upload API.
- Durable tamper-evident audit and wider HSM lifecycle audit coverage.
- Independent security review, hardware validation and clean-machine packaging tests.

SoftHSMv2 remains an independent compatible/test provider, not the product identity.

## Earlier HSM laboratory milestones

Virtual HSM Studio is an open-source PKCS#11 development,
simulation, and HSM management proof-of-concept.

The roadmap focuses on evolving the project from a virtual slot
simulator into a complete desktop HSM management laboratory.

## v0.2.0 — Foundation

Status: Current

- Clean Architecture
- Virtual HSM provider
- Persistent virtual slots
- Token initialization
- SO PIN and User PIN
- PBKDF2-based PIN storage
- PKCS#11 module loading
- DLL / SO / DYLIB discovery
- PKCS#11 slot enumeration
- Isolated PKCS#11 worker process
- PySide6 desktop GUI
- Unit tests

## v0.3.0 — Sessions & Objects

- PKCS#11 session model
- User login
- Security Officer login
- Session state visualization
- Token object browser
- Private / public / secret object classification
- CKA_LABEL support
- CKA_ID support
- Object attribute viewer
- Mechanism discovery

## v0.4.0 — Key Management

- AES key generation
- RSA key-pair generation
- EC key-pair generation
- Key templates
- CKA_PRIVATE
- CKA_SENSITIVE
- CKA_EXTRACTABLE
- CKA_SIGN
- CKA_VERIFY
- CKA_ENCRYPT
- CKA_DECRYPT
- Key deletion
- Key metadata viewer

## v0.5.0 — Cryptographic Operations

- Encrypt / Decrypt
- Sign / Verify
- SHA-256 / SHA-384 / SHA-512
- RSA-PSS
- RSA-PKCS#1
- ECDSA
- AES-CBC
- AES-GCM

## v0.6.0 — Certificates & Audit

- X.509 certificate objects
- Certificate import
- Certificate viewer
- Audit events
- Session history
- Operation history
- Error/event viewer
- Structured application logs

## v0.7.0 — Provider Profiles

- Multiple PKCS#11 providers
- Provider profiles
- SoftHSMv2 profile
- Vendor HSM profile support
- Module health checks
- Provider configuration
- Slot refresh / monitoring

## v0.8.0 — Product UX

- Dashboard
- HSM overview
- Slot health
- Token health
- Search and filtering
- Key inventory
- Certificate inventory
- Activity timeline
- Improved desktop theme

## v0.9.0 — Packaging

- Windows executable
- Windows installer
- Linux package
- Automated builds
- GitHub release artifacts
- Version information
- Application icons

## v1.0.0 — POC Release

Target capabilities:

Virtual HSM Studio should demonstrate a complete HSM workflow:

1. Load or create an HSM provider
2. Discover slots
3. Initialize a token
4. Login to the token
5. Generate cryptographic keys
6. Browse token objects
7. Perform cryptographic operations
8. Inspect mechanisms
9. Review audit events

v1.0 is a proof-of-concept and development platform, not a
replacement for a certified production Hardware Security Module.
