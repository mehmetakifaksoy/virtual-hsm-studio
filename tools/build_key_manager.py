"""Build the separate Windows Key Manager distribution."""
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
windows = Path(os.environ.get('SystemRoot', 'C:/Windows'))
env['PATH'] = os.pathsep.join(map(str, (Path(sys.executable).parent, windows/'System32', windows)))
env['PYINSTALLER_CONFIG_DIR'] = str(root/'work/pyinstaller-cache')
subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'packaging/key_manager.spec'], cwd=root, env=env, check=True)
