# Windows POC preview (0.4.0 beta 1)

## Install and start

1. Run `VirtualHsmStudio-0.4.0-beta.1-Setup.exe` on 64-bit Windows 10/11.
2. The installer uses your Windows account and does not require Python or administrator access.
3. Open **Virtual HSM Studio** from the Start menu.
4. Choose **Start Virtual HSM** on the Dashboard.

This preview is unsigned. Use your organization's normal policy for unsigned internal POC software. A signed build is required before broad distribution.

## Five-minute walkthrough

1. **Slots:** select a slot and choose **Initialize Token**. Enter a label and choose your own administrator (SO) and USER PINs.
2. **Sessions:** select the initialized token, keep read-only selected, then choose **Open Session**.
3. Select the session row and choose **Login**, then **USER** and your USER PIN.
4. Try **Logout** and **Close Session**.
5. Open a read/write session. With all read-only sessions closed, choose **SO** to test administration authentication.
6. **Slots → Manage Keys:** simulate a named AES or RSA key. Virtual mode creates metadata, not usable cryptographic key material.
7. On test data only, try **Clear Token** and **Delete Slot**. Confirmations default to No.

Virtual state persists in `~/.softhsm_studio/virtual_hsm_v2.json`. Uninstalling keeps this data. The app does not preconfigure or display a demo PIN.

## Optional real HSM

Use **Providers → Choose module** and select a trusted x64 PKCS#11 DLL installed with your vendor client. Vendor DLLs and SoftHSM binaries are not bundled. Slot/token discovery and the isolated key workflow are available; persistent generic PKCS#11 sessions are not yet implemented. The UI displays unsupported capabilities explicitly. Token initialization is currently limited to SoftHSM; follow your vendor's administration workflow for other devices.

If SoftHSM has no externally configured `SOFTHSM2_CONF`, an installed build uses `%LOCALAPPDATA%\VirtualHsmStudio\softhsm`. Existing source checkouts retain their existing `.hsm-data` location.

## Build from source

Use x64 Python 3.12 and install `requirements-dev.txt`. Install or extract the official NSIS 3.13 compiler, then run:

```powershell
python -m compileall src tests
python -m pytest -q
python tools/build_windows.py --makensis 'C:/path/to/nsis-3.13/makensis.exe'
```

Outputs:

- `dist/VirtualHsmStudio/`: portable directory; copy the entire directory.
- `dist/installer/VirtualHsmStudio-0.4.0-beta.1-Setup.exe`: installer.

The GUI is windowed; a separate console worker preserves stdin/stdout for isolated PKCS#11 operations. PINs travel through pipes, not process arguments. Application files and persistent token data remain separate. The uninstaller removes only files listed in the generated bundle manifest.

## POC feedback

Record Windows version, app version, provider type, exact action, expected result, and observed result. Include a screenshot if useful. Never include PINs, credentials, private key material, or production token data.
