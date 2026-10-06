# Security Model

## Virtual HSM

Virtual HSM mode is intentionally a development simulator. It does **not** provide tamper resistance, hardware key isolation, secure zeroization, FIPS validation, or a protected execution boundary.

PINs are not stored as plaintext. They are hashed with salted PBKDF2-SHA256. This protects against casual state-file disclosure, but it does not turn the simulator into a real HSM.

Never place production private keys, master keys, customer secrets, or regulated cryptographic material in the virtual state file.

## PKCS#11 modules

Vendor PKCS#11 libraries are native code and run with the privileges of the current user. SoftHSM Studio loads them in a separate worker process so a crash or bad library initialization is less likely to terminate the GUI process.

Only load modules obtained from a trusted source. Isolation here is process separation, not a malware sandbox.

## Key Manager and Sign & Verify

New private/secret keys are generated sensitive and non-extractable. Existing objects may have different policies.
Only public keys are exported by the signing client. Signing uses existing HSM keys; no private-key material is displayed.
PIN fields clear after submission and requests use stdin. Python memory is not guaranteed to be securely zeroized.

RSA/SHA-256 verification checks signature integrity with the supplied key; it does not validate identity, certificates,
revocation or timestamps. Treat the public key as a trust input. POC files are limited to 16 MiB.

Packaged applications are unsigned previews. Native-module process isolation is not a malware sandbox.
Vendor hardware validation, production hardening and a clean-machine distribution pilot remain outstanding.
