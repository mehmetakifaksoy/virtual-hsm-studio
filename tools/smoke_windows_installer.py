"""Install into an isolated directory, validate, then uninstall only that test install."""
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import winreg

root=Path(__file__).resolve().parents[1]
install=root/'work'/('installed-poc-'+uuid.uuid4().hex[:8])
registry=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio'
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry):
        raise SystemExit('An existing installation is registered; refusing to replace it during smoke testing.')
except FileNotFoundError:
    pass
if install.exists():
    raise SystemExit('Test destination already exists; choose a fresh directory.')
setup=root/'dist/installer/VirtualHsmStudio-0.4.0-beta.2-Setup.exe'
# NSIS requires the final /D path to be unquoted, including paths with spaces.
subprocess.run(f'"{setup}" /S /D={install}',timeout=120,check=True)
assert (install/'VirtualHsmStudio.exe').is_file()
assert (install/'HsmWorker.exe').is_file()
assert (install/'POC-GUIDE.md').is_file()
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry) as key:
    assert Path(winreg.QueryValueEx(key,'InstallLocation')[0])==install
print('Setup install and registration: passed',flush=True)
subprocess.run([sys.executable,str(root/'tools/smoke_windows_bundle.py'),str(install)],timeout=60,check=True)
sentinel=install/'preserve-unrelated-test-file.txt'
sentinel.write_text('Installer smoke test sentinel.',encoding='utf-8')
subprocess.run([str(install/'Uninstall.exe'),'/S'],timeout=60,check=True)
for _ in range(300):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry):
            registered = True
    except FileNotFoundError:
        registered = False
    if not registered and not (install/'VirtualHsmStudio.exe').exists():
        break
    time.sleep(.2)
assert not (install/'VirtualHsmStudio.exe').exists()
assert sentinel.is_file()
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry):
        raise AssertionError('Uninstall registry entry was not removed')
except FileNotFoundError:
    pass
print('Uninstall removes application, preserves unrelated files: passed',flush=True)
