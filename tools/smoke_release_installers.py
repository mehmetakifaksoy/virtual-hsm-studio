"""Test all installers with isolated product IDs; never replace user installations."""
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import winreg
from build_release import ROOT, TOOLS, compile_installer


def main():
    compiler=Path(sys.argv[1]).resolve()
    for name,product,_ in TOOLS:
        test_id=name+'-Smoke-'+uuid.uuid4().hex[:8]
        install=ROOT/'work'/test_id
        setup=ROOT/'work'/(test_id+'-Setup.exe')
        registry='Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\'+test_id
        compile_installer(compiler,name,product+' (isolated test)',setup,app_id=test_id)
        subprocess.run(f'"{setup}" /S /D={install}',timeout=120,check=True)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,registry) as key:
            assert Path(winreg.QueryValueEx(key,'InstallLocation')[0])==install
        subprocess.run([sys.executable,str(ROOT/'tools/smoke_windows_bundle.py'),str(install),'--executable',name+'.exe'],timeout=60,check=True)
        sentinel=install/'preserve-unrelated.txt'
        sentinel.write_text('Keep this unrelated test file.',encoding='utf-8')
        subprocess.run([str(install/'Uninstall.exe'),'/S'],timeout=60,check=True)
        for _ in range(300):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,registry):
                    registered=True
            except FileNotFoundError:
                registered=False
            if not registered and not (install/(name+'.exe')).exists():
                break
            time.sleep(.2)
        assert not registered
        assert not (install/(name+'.exe')).exists()
        assert sentinel.is_file()
        print(name+': installation, launch and uninstall passed; unrelated file preserved',flush=True)


if __name__=='__main__':
    main()
