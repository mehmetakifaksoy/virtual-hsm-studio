# Windows POC guide — 0.4.0-beta.2

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
Procenne uses its vendor module; the suite does not implement a replacement for that DLL.
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
