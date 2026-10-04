# Virtual HSM Studio 0.4.0 beta 1

A clean, slot-oriented desktop HSM simulator and PKCS#11 module explorer.

## Goals

SoftHSM Studio has two provider modes behind the same application boundary:

1. **Virtual HSM** — a persistent development simulator with Slot -> Token semantics.
2. **PKCS#11 Module** — loads a `.dll`, `.so`, or `.dylib` in a separate worker process and enumerates the slots and token metadata exposed by that module.

The GUI never depends directly on a specific HSM vendor. New provider adapters can be added without rewriting the presentation layer.

## Current features

- PySide6 desktop GUI
- Slot-based virtual HSM
- Persistent JSON state with atomic writes
- SO PIN and User PIN hashing with PBKDF2-SHA256
- Create/delete virtual slots
- Initialize/clear virtual tokens
- Drag-and-drop PKCS#11 modules
- PKCS#11 slot enumeration
- Token label, serial, manufacturer, model and flag inspection
- Isolated PKCS#11 worker with timeout and structured errors
- Background provider load/refresh threads so vendor modules do not freeze the GUI
- Modular management console with Dashboard, Providers, Slots and Sessions screens
- Capability-aware session opening, login, logout and close workflows
- Unit tests for core domain and virtual HSM behavior

## Windows POC installer

The Windows POC build includes Python and Qt. Start with **Start Virtual HSM**; real PKCS#11 modules are optional. See [Windows POC installation, walkthrough and build instructions](docs/WINDOWS_POC.md).

## Windows setup (from source)

Recommended: 64-bit Python 3.11 or 3.12.

```bat
setup_windows.bat
run.bat
```

Manual setup:

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m softhsm_studio
```

## Loading a real PKCS#11 module

Click **Load PKCS#11 Module...** or drag a module file into the application.

Examples of module file types:

- Windows: `*.dll`
- Linux: `*.so`
- macOS: `*.dylib`

The module architecture must match Python architecture. For example, a 64-bit Python process requires a compatible 64-bit PKCS#11 module.

## Virtual state

By default virtual state is stored at:

- Windows/Linux/macOS: `~/.softhsm_studio/virtual_hsm_v2.json`

Override it with:

```text
SOFTHSM_STUDIO_STATE=/custom/path/state.json
```

## Tests

```bash
python -m pytest
```

## Security notice

Virtual HSM mode is a simulator, not a hardware security module. It is suitable for UI development, integration tests and PKCS#11 workflow simulation. Do not store production secrets or production private keys in the virtual JSON state.

See `SECURITY.md` and `docs/ARCHITECTURE.md`.

## Three separate applications

| Application | Run from source | Purpose |
| --- | --- | --- |
| HSM Studio | `python -m softhsm_studio` | Connections, slots, tokens and sessions |
| Key Manager | `python -m softhsm_studio.key_manager` | List key metadata and generate supported AES/RSA keys |
| Sign & Verify | `python -m softhsm_studio.sign_app` | Sign files with HSM RSA keys, export public keys and verify independently |

Install dependencies with `python -m pip install -e .[dev]`.

Studio separates local demo controls from external PKCS#11 providers. Slot administration
contains no key-generation controls. Advanced demo actions and technical details start collapsed.
The local Virtual HSM stores simulation metadata only and cannot produce cryptographic signatures.
Use SoftHSM2 or an actual HSM vendor module for signing. Procenne hardware has not been validated.
Applications never automatically load a previously selected DLL.

### Sign and verify a file

1. Initialize a token using Studio (SoftHSM2) or the vendor administration tool.
2. Generate an RSA key pair in Key Manager on that token.
3. In Sign & Verify, connect the same module, select the token and open signing.
4. Enter USER PIN and load RSA signing keys. Select the key and document.
5. Re-enter USER PIN and sign. Save the public key as PEM and the detached signature as `.sig`.
6. Choose Verify File Signature and select the original document, signature and public key.

The POC implements RSA PKCS#1 v1.5 with SHA-256 and a 16 MiB document limit.
Public keys may be exported; private keys stay on the HSM. Key wrapping, private-key export,
certificate trust validation, PDF/PAdES signing and timestamps are not implemented.
Verification checks document/signature/key consistency, not the identity of the key owner.
PINs travel to isolated workers through stdin, never command-line arguments or log files.
The signing dialog clears the PIN after each request and does not automatically retry login.

### Windows builds

```powershell
python tools/build_windows.py
python tools/build_key_manager.py
python tools/build_sign_verify.py
```

Outputs are `dist/VirtualHsmStudio`, `dist/HsmKeyManager` and `dist/HsmSignVerify`.
Each directory contains its own GUI executable, `HsmWorker.exe` and `_internal` dependencies.
Keep the entire directory together; copying only the EXE is insufficient.
Builds sanitize PATH to avoid collecting unrelated Qt/ICU dependencies.
Vendor DLLs, local token stores and built binaries are excluded from Git.

Set `SOFTHSM2_CONF` to use an explicit SoftHSM2 token store. Otherwise the packaged apps use
`%LOCALAPPDATA%/VirtualHsmStudio/softhsm`; source runs preserve an existing `.hsm-data`
store or use the same per-user location. All tools must use the same configuration to see the same tokens.

### Validation

```powershell
python -m compileall src tests
python -m pytest -q
python -m softhsm_studio --smoke-test
python -m softhsm_studio.key_manager --smoke-test
python -m softhsm_studio.sign_app --smoke-test
```

Set `SOFTHSM_TEST_MODULE` to a SoftHSM2 DLL/library to enable integration tests; they use
isolated temporary token stores. Signing tests cover real RSA signatures, public-key export,
altered documents, invalid signatures and wrong public keys. GUI regression tests cover the
signing-key loading callback, including the Qt dialog signal collision fix.
