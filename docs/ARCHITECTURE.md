# Architecture

The suite has three independent PySide6 entry points:

- `softhsm_studio`: modular Home, Connections, Slots and Sessions console.
- `softhsm_studio.key_manager`: initialized-token selection and a key management dialog.
- `softhsm_studio.sign_app`: file signing and independent public-key verification.

`HsmService` owns provider selection and delegates to domain capability interfaces.
`VirtualHsmProvider` persists simulator metadata. `Pkcs11ModuleProvider` discovers external modules in isolated workers.
Simulator capabilities do not imply equivalent hardware-adapter support. Persistent hardware sessions are not exposed by the console adapter yet.

## Worker boundaries

`HsmWorker.exe` dispatches snapshot, keys and sign operations. Source runs use the equivalent Python modules.
Native modules are loaded in the worker; connection and key/sign operations are dispatched from GUI QThreads.
JSON requests go through stdin (PINs are not process arguments). Replies contain metadata, public keys or signatures, never private-key values.
Workers suppress vendor exception text on key/sign failure. Timeout does not imply a mutating HSM operation was rolled back.
Do not automatically repeat operations after an uncertain result.

Verification uses cryptography locally without a PKCS#11 connection. Signatures use explicit SHA256_RSA_PKCS;
key selection requires a unique RSA private/public pair with matching CKA_ID and a signing-capable private key.
A produced signature is checked against its public key before it is returned.

## Presentation

Console pages and shared cards live under presentation/pages and presentation/widgets.
Slot/token and session action handlers are separated from the main window.
Demo administration and technical details are collapsed by default. Slot pages contain no key-generation action.
Key Manager and signing dialogs guard against closure while a worker runs and clear PIN fields after submission.
The signing completion callback has a distinct name from QDialog.finished(int).

## Distribution

Three PyInstaller specifications produce independent directories with GUI EXE, worker EXE and _internal.
`tools/build_release.py` builds these, includes licenses/guides, creates per-user NSIS installers and portable ZIPs,
and writes checksums. Build PATH is limited to Python and Windows directories to avoid unrelated ICU/Qt DLL capture.
Applications share an explicitly selected SoftHSM configuration, not an in-memory process session.

## Still planned

Hardware-provider pilot, richer mechanism/attribute views, key wrapping policy, certificate workflows,
additional signing algorithms and long-lived hardware session management.
