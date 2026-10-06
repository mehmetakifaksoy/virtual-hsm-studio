# Security Model

## Key Sovereignty POC

AES-256-GCM is real local cryptography supplied by cryptography/OpenSSL. Each operation
uses a fresh CSPRNG-generated 32-byte DEK, 12-byte nonce and 16-byte tag.
Canonical authenticated metadata binds algorithm, version, DEK metadata, key reference,
wrapping mode, nonce and wrapped DEK. Tampered data, tags and references fail closed.
Master/KEK references are opaque identifiers, not material. Never enter secrets in identifiers.

Virtual wrapping holds separate randomly generated KEKs in process memory. It is explicitly
mock/virtual and does not turn simulated key objects into real HSM keys. No KEK or plaintext
DEK is persisted. App close or provider switch clears the registry and makes packages
unrecoverable. Use disposable test files only. Python, swap and crash dumps prevent a secure
zeroization guarantee. No hardware isolation, FIPS or durable recovery claim is made.

The file flow preserves the source and exclusively creates ciphertext-only packages, up to
16 MiB input. Partial ciphertext output may remain after an I/O failure. Processing is synchronous
and intended for small test files. No cloud client is passed to ProtectBeforeCloud and no upload
endpoint exists. Source filenames and package/reference metadata are not confidential.

Audit uses a closed schema and latest-1000 in-memory protection/BYOK events: operation,
provider, slot, key reference, result and UTC timestamp. It accepts no arbitrary message payloads,
PINs, private/secret key bytes, plaintext, import tokens or credentials. References are opaque
labels, not a secret-detection mechanism. Audit is not durable/tamper-evident and does not yet
cover every existing HSM operation. Public POC errors do not echo adapter exceptions.

Huawei is an offline fake. Import tokens and private wrapping keys exist transiently in memory,
have a ten-minute acceptance window and are removed after valid import. RSA-OAEP-SHA-256
wrapped AES-256 material is validated but not retained. Invalid, expired, wrong-key and replay
imports fail. No credentials are accepted, persisted or logged. Real External BYOK would import
customer material into cloud KMS; it does not establish cloud-external key custody.

Production release requires native wrapping, durable recovery, authenticated key access,
live-cloud verification, protected audit, packaging validation and independent review.

## Virtual HSM

Virtual HSM mode is intentionally a development simulator. It does **not** provide tamper resistance, hardware key isolation, secure zeroization, FIPS validation, or a protected execution boundary.

PINs are not stored as plaintext. They are hashed with salted PBKDF2-SHA256. This protects against casual state-file disclosure, but it does not turn the simulator into a real HSM.

Never place production private keys, master keys, customer secrets, or regulated cryptographic material in the virtual state file.

## PKCS#11 modules

Vendor PKCS#11 libraries are native code and run with the privileges of the current user. Virtual HSM Studio loads them in a separate worker process so a crash or bad library initialization is less likely to terminate the GUI process.

Only load modules obtained from a trusted source. Isolation here is process separation, not a malware sandbox.

## Key Manager and Sign & Verify

New private/secret keys are generated sensitive and non-extractable. Existing objects may have different policies.
Only public keys are exported by the signing client. Signing uses existing HSM keys; no private-key material is displayed.
PIN fields clear after submission and requests use stdin. Python memory is not guaranteed to be securely zeroized.

RSA/SHA-256 verification checks signature integrity with the supplied key; it does not validate identity, certificates,
revocation or timestamps. Treat the public key as a trust input. POC files are limited to 16 MiB.

Packaged applications are unsigned previews. Native-module process isolation is not a malware sandbox.
Vendor hardware validation, production hardening and a clean-machine distribution pilot remain outstanding.
