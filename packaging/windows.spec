# Build with: python -m PyInstaller --noconfirm packaging/windows.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

root = Path(SPECPATH).parent
pkcs11_imports = collect_submodules('pkcs11')
notices = [(str(root / 'LICENSE'), 'licenses/VirtualHsmStudio')]
for package in ('PySide6', 'shiboken6', 'pkcs11'):
    notices += collect_data_files(package, includes=['**/*LICENSE*', '**/*COPYING*'])
gui = Analysis([str(root / 'packaging/gui_entry.py')], pathex=[str(root/'src')],
               binaries=[], datas=notices, hiddenimports=[], excludes=['tkinter', 'pytest'])
worker = Analysis([str(root / 'packaging/worker_entry.py')], pathex=[str(root/'src')],
                  binaries=[], datas=[], hiddenimports=pkcs11_imports, excludes=['PySide6', 'tkinter', 'pytest'])
gui_exe = EXE(PYZ(gui.pure), gui.scripts, [], exclude_binaries=True,
              name='VirtualHsmStudio', console=False)
worker_exe = EXE(PYZ(worker.pure), worker.scripts, [], exclude_binaries=True,
                 name='HsmWorker', console=True)
COLLECT(gui_exe, worker_exe, gui.binaries, gui.datas, worker.binaries, worker.datas,
        strip=False, upx=False, name='VirtualHsmStudio')
