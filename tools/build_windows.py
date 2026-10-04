"""Build a Windows bundle and optionally the NSIS installer."""
import argparse
import os
import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--makensis', type=Path)
parser.add_argument('--skip-bundle', action='store_true')
args = parser.parse_args()
if not args.skip_bundle:
    # Prevent unrelated software on PATH (e.g. PDF tools with their own ICU)
    # from supplying DLLs in place of Windows/Qt dependencies.
    build_env = os.environ.copy()
    windows = Path(os.environ.get("SystemRoot", "C:/Windows"))
    build_env["PATH"] = os.pathsep.join(map(str, (Path(sys.executable).parent, windows/"System32", windows)))
    build_env["PYINSTALLER_CONFIG_DIR"] = str(root/"work/pyinstaller-cache")
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'packaging/windows.spec'], cwd=root, env=build_env, check=True)
bundle = root/'dist/VirtualHsmStudio'
if not (bundle/'VirtualHsmStudio.exe').is_file():
    raise SystemExit('Build the application bundle first.')
# Include dependency license texts and a version inventory with the binary.
license_root = bundle/'licenses'
license_root.mkdir(exist_ok=True)
versions = []
for name in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6', 'python-pkcs11', 'asn1crypto'):
    package = importlib.metadata.distribution(name)
    versions.append(f"{name} {package.version}")
    for file in package.files or []:
        if '.dist-info' in str(file) and ('license' in str(file).lower() or 'copying' in str(file).lower()):
            source = Path(package.locate_file(file))
            if source.is_file():
                target = license_root/name/source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
for source in (Path(sys.base_prefix)/'LICENSE.txt', Path(sys.base_prefix)/'LICENSE'):
    if source.is_file():
        shutil.copy2(source, license_root/'Python-LICENSE.txt')
(license_root/'COMPONENTS.txt').write_text("Python " + sys.version.split()[0] + "\n" + "\n".join(versions) + "\nQt/PySide6 libraries remain dynamically linked. Source and license details: https://www.qt.io/development/qt-framework/qt-for-python\n", encoding='utf-8')
shutil.copy2(root/'docs/WINDOWS_POC.md', bundle/'POC-GUIDE.md')
lines = []
for path in sorted(bundle.rglob('*')):
    if path.is_file():
        relative = str(path.relative_to(bundle)).replace('/', '\\')
        if '$' in relative or '"' in relative:
            raise SystemExit('Unsupported filename in bundle')
        lines.append(f'Delete "$INSTDIR\\{relative}"')
for path in sorted((p for p in bundle.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
    relative = str(path.relative_to(bundle)).replace('/', '\\')
    lines.append(f'RMDir "$INSTDIR\\{relative}"')
(root/'packaging/uninstall-files.nsh').write_text('\n'.join(lines)+'\n', encoding='utf-8')
(root/'dist/installer').mkdir(exist_ok=True)
if args.makensis:
    subprocess.run([str(args.makensis.resolve()), '/V2', 'packaging/windows.nsi'], cwd=root, check=True)
