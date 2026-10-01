# Security Model

## Virtual HSM

Virtual HSM mode is intentionally a development simulator. It does **not** provide tamper resistance, hardware key isolation, secure zeroization, FIPS validation, or a protected execution boundary.

PINs are not stored as plaintext. They are hashed with salted PBKDF2-SHA256. This protects against casual state-file disclosure, but it does not turn the simulator into a real HSM.

Never place production private keys, master keys, customer secrets, or regulated cryptographic material in the virtual state file.

## PKCS#11 modules

Vendor PKCS#11 libraries are native code and run with the privileges of the current user. SoftHSM Studio loads them in a separate worker process so a crash or bad library initialization is less likely to terminate the GUI process.

Only load modules obtained from a trusted source. Isolation here is process separation, not a malware sandbox.
