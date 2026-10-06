# Architecture

## Key Sovereignty and Cloud BYOK

Virtual HSM Studio is a Vendor-agnostic HSM, PKCS#11 and Key Sovereignty Platform.
Domain contracts in `domain/sovereignty.py` describe reference-only KEKs, DEK/envelope
metadata, packages and optional cipher/wrapping capabilities. `domain/cloud.py` describes
generic External BYOK metadata, import parameters, wrapped material and client operations.
Domain and application have no vendor SDK, PKCS#11 library or Qt dependency.

`application/sovereignty.py` orchestrates local DEK generation, capability checks, wrapping
and authenticated encryption/decryption. It receives cipher, wrapping and audit ports;
no cloud or upload dependency exists. Wrapping is separate from existing HSM/session ports,
so unsupported providers remain usable. `application/cloud.py` orchestrates separate BYOK.

Infrastructure contains `local_crypto.py`, `envelope_store.py`, explicit
`virtual_hsm/wrapping.py` and offline `cloud/mock/fake.py`. Future live Cloud KMS code stays
behind the same port. Native wrapping is absent and fails closed in the GUI, with no silent
virtual fallback. Virtual KEKs belong to the POC capability, not persistent simulator objects.

MainWindow composes adapters and use cases. Existing provider/slot/session/object pages
remain, alongside Keys, Cloud KMS Integration, Key Sovereignty and Audit/Diagnostics. Pages emit
signals and handlers invoke use cases. Pages are scrollable. HSM connect/refresh workers remain;
local protection is synchronous with a 16 MiB cap. Standalone Key Manager and Sign & Verify
remain available. Native modules require explicit selection on every launch.

Envelope v1 JSON contains metadata (key_reference, wrapping_mode, nonce, wrapped_dek, dek,
version, algorithm), ciphertext and tag. Binary fields use strict base64. Known algorithms,
nonce/tag lengths and wrapping modes are validated. Canonical sorted JSON metadata is GCM AAD.
Plaintext is returned only after authentication; persisted packages contain no plaintext DEK/KEK.

The vendor-neutral External BYOK contract contains create-external-key, get-import-parameters, import-wrapped-key-material and status operations. Live providers will implement adapters behind this interface.

The fake uses transient RSA-2048/RSAES_OAEP_SHA_256 parameters and generic pending-import/enabled
states rather than provider-specific wire enums. No HTTP requests or imported-key persistence occur.
SoftHSMv2 is an independent compatible/test provider; no official affiliation is implied.

Virtual HSM Studio uses a provider architecture so the GUI is independent of any specific HSM implementation.

```text
Presentation (PySide6)
  â”œâ”€â”€ Dashboard
  â”œâ”€â”€ Providers
  â”œâ”€â”€ Slots
  â”œâ”€â”€ Sessions
  â””â”€â”€ Objects
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

The PySide6 console is split into Dashboard, Providers, Slots, and Sessions
pages. Page widgets live under `presentation/pages`; reusable shell layout is
built by `presentation/widgets/console.py`. Slot and session action handlers
are separated from the window coordinator. Pages emit Qt signals and do not
call provider implementations directly; `MainWindow` routes actions through
`HsmService`.
Potentially slow provider connect/refresh calls execute in `QThread` workers.
Session controls are shown only when the active provider implements the
optional session capability. Providers that do not implement a capability
remain usable for the operations they do support.

GUI workflow tests exercise the real dialogs and controls using isolated
Virtual HSM state, including slot/token administration and RO/RW session
authentication flows. The Object Explorer queries metadata through the
application service using an active session and deliberately does not display
object attribute values or cryptographic key material.

## Why the PKCS#11 worker is separate

Native PKCS#11 libraries execute inside the process that loads them. A vendor module can block, crash, initialize global state, or conflict with another PKCS#11 implementation. Virtual HSM Studio therefore performs discovery in a separate process and exchanges only JSON snapshots with the GUI process.

## Planned next adapters/features

- PKCS#11 mechanism browser
- AES key generation
- RSA/EC key pair generation
- Certificate objects
- CKA_ID / CKA_LABEL / CKA_SENSITIVE / CKA_EXTRACTABLE views
- Sign/verify and encrypt/decrypt test console
- SoftHSM2 native administration adapter
- Vendor-specific provider extensions without GUI coupling
