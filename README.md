# SoftHSM Studio 0.2.0

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
- Unit tests for core domain and virtual HSM behavior

## Windows setup

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

## Separate DLL tools

Run `Start Admin Tool.cmd` to load the PKCS#11 DLL and initialize a free
SoftHSM token with its label, SO PIN and USER PIN. Run `Start Key Manager.cmd`
separately to select that token, view keys and generate AES/RSA keys.
The tools remember the same DLL; no PIN is saved in settings.

The bundled local test DLL is
`tools/softhsm2/SoftHSM2/lib/softhsm2-x64.dll` (SoftHSM 2.5.0 portable,
https://github.com/disig/SoftHSM2-for-Windows). Its licenses remain in the package.
Binary packages and token stores are ignored by Git. In a fresh checkout obtain
that portable package and extract it under `tools/softhsm2`.

Unless `SOFTHSM2_CONF` already points to your own configuration, both tools use
`.hsm-data/softhsm2.conf` and `.hsm-data/tokens`. They create real software-HSM
keys through the DLL; the old JSON metadata simulator is not used by these tools.
SoftHSM exposes an uninitialized slot; initializing its token assigns a slot ID
and exposes another free slot. Generic PKCS#11 does not provide CreateSlot.
Vendor hardware setup remains in the vendor administration software.

Run `Test DLL Workflow.cmd` to compile source and run tests including an isolated
DLL workflow: initialize token, generate AES and RSA objects, reopen and verify
persistence. This integration test uses a temporary token directory, separate
from your application tokens. Tests have not been run in the restricted agent
runtime because the virtual-environment interpreter cannot execute there.
