# Virtual HSM Studio

**Vendor-agnostic HSM, PKCS#11 and Key Sovereignty Platform**

## Key Sovereignty POC — source branch, unreleased

HSM management, local Protect-Before-Cloud encryption and cloud BYOK adapters behind vendor-neutral contracts.

- Real local AES-256-GCM, fresh local DEKs and nonces; authenticated versioned envelope packages.
- Explicit virtual/mock wrapping: real AES-GCM wrapping with a process-memory KEK, separate from simulator key metadata. Native PKCS#11 wrapping is not implemented.
- Offline Huawei External BYOK contracts: create external metadata, obtain import parameters, import wrapped material and inspect status. No credentials, network or upload.
- Nine modular areas: Dashboard, Providers, Slots/Tokens, Sessions, Objects, Keys, Cloud Integration, Key Sovereignty, Audit/Diagnostics.
- Closed-schema, in-memory protection/BYOK audit without PINs, raw keys, plaintext, import tokens or credentials.

**Virtual packages are recoverable only while the same process-memory KEK is available. Closing the app or switching provider discards it. Use disposable test files only.** Python memory is not a protected HSM boundary.

Run from source, choose Virtual HSM, initialize a token in Slots/Tokens, open Key Sovereignty, select a file and click **Encrypt Locally**. A uniquely named `.vhspkg` appears beside the source, without overwriting files. Maximum input: 16 MiB. The source is preserved. Decryption is available through the tested application service; this POC GUI only encrypts. **Plaintext never uploaded.** No upload operation exists.

External BYOK is a separate mode: it imports customer key material into cloud KMS and does not guarantee keys stay outside the cloud. The local protection KEK is not passed to BYOK. See [Security](SECURITY.md) and [Roadmap](ROADMAP.md).

The existing Key Manager and Sign & Verify applications remain available. SoftHSMv2 is an independent compatible/test provider; this product is not its official GUI and is not affiliated with its maintainers.

## Previous packaged preview

The installers below predate Key Sovereignty and **do not contain the new source-branch POC**.

Three Windows applications for PKCS#11 HSM workflows. **POC preview · v0.4.0-beta.2**

## Download and run — no Python required

Open [Windows releases](https://github.com/mehmetakifaksoy/virtual-hsm-studio/releases/tag/v0.4.0-beta.2) and expand **Assets**.

| Application | Windows installer | Purpose |
| --- | --- | --- |
| HSM Studio | [VirtualHsmStudio Setup](https://github.com/mehmetakifaksoy/virtual-hsm-studio/releases/download/v0.4.0-beta.2/VirtualHsmStudio-0.4.0-beta.2-Setup.exe) | Connections, slots, token preparation and simulator sessions |
| Key Manager | [HsmKeyManager Setup](https://github.com/mehmetakifaksoy/virtual-hsm-studio/releases/download/v0.4.0-beta.2/HsmKeyManager-0.4.0-beta.2-Setup.exe) | Key metadata and supported AES/RSA generation |
| Sign & Verify | [HsmSignVerify Setup](https://github.com/mehmetakifaksoy/virtual-hsm-studio/releases/download/v0.4.0-beta.2/HsmSignVerify-0.4.0-beta.2-Setup.exe) | RSA file signing, public-key export and independent verification |

Run the selected Setup and launch the application from Start. Installers are per-user and require 64-bit Windows.
They are unsigned POC builds. A clean independent Windows-machine pilot is still pending.

For portable use, download the corresponding `Windows-x64.zip`, **extract the entire archive**, and run the named EXE.
Keep `HsmWorker.exe` and `_internal` next to the GUI executable. Do not run from inside the ZIP or copy the EXE alone.
`SHA256SUMS.txt` contains release asset checksums. GitHub's **Code → Download ZIP** and automatic **Source code** archives contain source, not ready-to-run applications.

## Choose the right mode

- **Virtual HSM**: local JSON simulator for slot/token/session demos. Key operations produce metadata, not usable cryptographic keys; it cannot sign.
- **SoftHSM2**: a separate software PKCS#11 implementation that can generate real keys and sign. Install its matching x64 module separately.
  

## First signing test

1. Use Studio or your vendor tool to prepare a token. Slot creation/deletion controls in Studio are **demo-only**; generic token initialization is currently limited to SoftHSM2.
2. Open Key Manager, connect the same module and select the initialized token.
3. Generate an **RSA-2048** key pair with a recognizable label and your USER PIN.
4. Open Sign & Verify, connect the same module and select the same token.
5. Enter USER PIN, load RSA signing keys, select the key and a small document.
6. Re-enter USER PIN, sign, save the public key as `.pem`, then save the signature as `.sig`.
7. Choose **Verify File Signature** and select the original document, `.sig`, and public `.pem`.

The result should be **VALID**. Changing the document or using a different public key must produce **INVALID**.
Verification needs no HSM connection. See the [step-by-step signing guide](docs/SIGNING_GUIDE.md).

## Current limits

RSA PKCS#1 v1.5 / SHA-256, detached signatures and a 16 MiB document limit. The provider must advertise `SHA256_RSA_PKCS`.
Private/secret keys generated by Key Manager are marked sensitive and non-extractable. Only public keys are exported by Sign & Verify.
No native PKCS#11 wrapping, private-key export, certificate identity/trust validation, PDF/PAdES signing or trusted timestamps.
Hardware PKCS#11 sessions are opened inside isolated operations; Studio's persistent session-management screen is currently implemented for the simulator.

## Run from source

Install Python 3.12 x64. Open PowerShell **inside the extracted repository** (the directory containing `pyproject.toml`).
Use a short virtual-environment path to avoid Windows long-path errors in PySide6 installation:

```powershell
py -3.12 -m venv "$env:USERPROFILE\hsm-env"
& "$env:USERPROFILE\hsm-env\Scripts\python.exe" -m pip install -e ".[dev]"
& "$env:USERPROFILE\hsm-env\Scripts\python.exe" -m softhsm_studio
& "$env:USERPROFILE\hsm-env\Scripts\python.exe" -m softhsm_studio.key_manager
& "$env:USERPROFILE\hsm-env\Scripts\python.exe" -m softhsm_studio.sign_app
```

Run one application command at a time. Close it to return to the prompt, or use a second PowerShell window.
Paths containing spaces must be quoted: `Set-Location -LiteralPath 'C:\path with spaces\repository'`.
The optional `.cmd` launchers expect a `.venv` inside the repository; the commands above use the shorter external environment instead.

## Build and test

```powershell
python -m compileall src tests
python -m pytest -q --basetemp=.pytest-tmp/run
python -m softhsm_studio --smoke-test
python -m softhsm_studio.key_manager --smoke-test
python -m softhsm_studio.sign_app --smoke-test
python tools/build_release.py --makensis 'C:\path\to\NSIS\makensis.exe'
```

Release builds require Windows x64, development dependencies and NSIS 3.x. Output: `dist/release`.
Individual portable builds: `tools/build_windows.py`, `tools/build_key_manager.py`, `tools/build_sign_verify.py`.
Set `SOFTHSM_TEST_MODULE` to a SoftHSM2 module to enable native integration tests; these use temporary token stores.
Set `SIGN_TEST_FROZEN_WORKER` to a built `HsmWorker.exe` to test signing with the packaged worker.

## Documentation

- [Windows installation, configuration and troubleshooting](docs/WINDOWS_POC.md)
- [Signing walkthrough](docs/SIGNING_GUIDE.md)
- [Architecture and implemented capabilities](docs/ARCHITECTURE.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)

Licensed under [Apache-2.0](LICENSE). Packages include dependency notices in `licenses/`.
