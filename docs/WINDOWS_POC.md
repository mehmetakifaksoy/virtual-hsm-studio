# Windows POC guide — 0.5.0-alpha.1 local preview

This preview includes Key Sovereignty, Cloud Integration and Audit/Diagnostics.
It is an unreleased test build; older GitHub beta.2 assets do not include these pages.

## Test local protection

1. Start VirtualHsmStudio.exe and choose Virtual HSM from Dashboard.
2. Open Slots/Tokens, select a slot and prepare its demo token with a label and test PINs.
3. Open Key Sovereignty and select a disposable source file (up to 16 MiB).
4. Select the initialized token and virtual session KEK reference, then click Encrypt Locally.
5. Check the output .vhspkg path and algorithm/version/wrapping summary.
6. Open Audit/Diagnostics to inspect operation metadata without secrets.
7. Open Cloud Integration to create mock external metadata and inspect import parameters/status.

AES-256-GCM encryption is real. KEK wrapping is explicitly virtual/mock and only recoverable
while the same application session remains open. Do not use valuable data. Huawei is offline
mock; no credentials, network, file upload or native PKCS#11 wrapping are implemented.
The original source is preserved. Plaintext never uploaded.

## Preview files

Use VirtualHsmStudio-0.5.0-alpha.1-Setup.exe or extract the complete Windows-x64 ZIP.
SHA256SUMS.txt lists file checksums. Key Manager and Sign & Verify are separate companion tools.
Close an older instance before installing. Portable testing avoids updating an existing installation.

The following general install/provider guidance also applies to the preview.

## Install

Download the three independent Setup executables from the GitHub release Assets. Python is not needed.
Applications install for the current user under `%LOCALAPPDATA%\Programs\VirtualHsmStudio`,
`%LOCALAPPDATA%\Programs\HsmKeyManager` and `%LOCALAPPDATA%\Programs\HsmSignVerify`.
Close the corresponding app before installing an update. Each tool has its own uninstaller.
Uninstallation removes packaged application files and preserves token stores and unrelated files.

Portable ZIPs contain the GUI EXE, HsmWorker.exe, _internal and documentation. Extract the whole ZIP;
keep the directory intact. A short path such as `%USERPROFILE%\HsmTools` is convenient.
The builds are unsigned POC previews, not certified production HSM software.

## Connect an HSM

Use an x64 PKCS#11 module matching the application architecture. Install/configure vendor dependencies first.
Use the HSM manufacturer's module; the suite does not implement a replacement for vendor DLLs.
SoftHSM2 is an alternative software provider for real cryptographic testing. Obtain it from a trusted distribution;
no vendor DLL is included in GitHub source or release assets.

Use the same module and configuration in all three tools. In particular, `SOFTHSM2_CONF` selects the token store.
If unset, installed tools create `%LOCALAPPDATA%\VirtualHsmStudio\softhsm\softhsm2.conf` and its token directory.
Source runs preserve an existing repository `.hsm-data` directory, otherwise use the per-user location.
A different configuration can show different tokens even when the DLL is identical.
Virtual HSM demo state is separate, in `~/.softhsm_studio/virtual_hsm_v2.json` unless overridden.

## Terminology

- Slot: logical location exposed by the module. Its numeric ID need not be small or sequential.
- Token: named security container associated with a slot. It contains objects and PIN policy.
- USER PIN: access to user operations, including authorized signing.
- SO/administrator PIN: token administration; not the PIN to enter in the signing dialog.
- Session: connection used to operate on a token. Simulator session controls are separate from short-lived hardware operations.

Studio provides demo slot administration; Key Manager handles key generation; Sign & Verify consumes existing keys.
No slot/token creation or deletion is performed by the signing app.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Download ZIP contains no EXE | Use release Assets, not Code → Download ZIP or the automatic source archives. |
| Missing DLL / HsmWorker | Extract or reinstall the full distribution. Do not mix versions of _internal and EXEs. |
| No tokens | Check module configuration and initialize a token using Studio (SoftHSM2) or vendor tooling. |
| No RSA signing keys | Check the selected token and USER PIN; create an RSA key pair and ensure CKA_SIGN is enabled. AES keys are not listed. |
| PIN failure | Stop repeated attempts and check token policy. No automatic PIN retry is implemented. |
| INVALID signature | Choose the exact original bytes, matching .sig and public .pem. File names do not establish key identity. |
| Working never finishes in an old build | Update all files to beta.2; the QDialog finished-signal collision is fixed. |
| pip reports missing long PySide6 paths | Create the environment at `%USERPROFILE%\hsm-env`; see README. |
| PowerShell rejects a folder path | Quote it with `Set-Location -LiteralPath 'full path'`. |

The UI clears PIN fields after requests; it does not remember PINs. Do not include PINs or private keys in screenshots or issue reports.
