# Architecture

SoftHSM Studio uses a provider architecture so the GUI is independent of any specific HSM implementation.

```text
Presentation (PySide6)
        |
        v
Application Service
        |
        v
Domain HsmProvider Port
      /               \
     v                 v
VirtualHsmProvider   Pkcs11ModuleProvider
     |                 |
JsonStateStore       subprocess
                       |
                       v
                  PKCS#11 Worker
                       |
                       v
                 Vendor DLL/SO
```

## Layers

### Domain

Contains immutable public models, controlled exceptions, and provider interfaces. It has no GUI, filesystem, subprocess, or PKCS#11 dependency.

### Application

`HsmService` owns the active provider and exposes provider-independent operations to the presentation layer.

### Infrastructure

`VirtualHsmProvider` persists development state to JSON. `Pkcs11ModuleProvider` invokes a short-lived isolated worker for native module inspection.

### Presentation

PySide6 widgets display slot/token state and invoke application operations. Potentially slow provider connect/refresh calls execute in `QThread` workers.

## Why the PKCS#11 worker is separate

Native PKCS#11 libraries execute inside the process that loads them. A vendor module can block, crash, initialize global state, or conflict with another PKCS#11 implementation. SoftHSM Studio therefore performs discovery in a separate process and exchanges only JSON snapshots with the GUI process.

## Planned next adapters/features

- Session/login model
- PKCS#11 mechanism browser
- Object explorer
- AES key generation
- RSA/EC key pair generation
- Certificate objects
- CKA_ID / CKA_LABEL / CKA_SENSITIVE / CKA_EXTRACTABLE views
- Sign/verify and encrypt/decrypt test console
- SoftHSM2 native administration adapter
- Vendor-specific provider extensions without GUI coupling
