"""Build three independent Windows distributions, installers and checksums."""
import argparse
import hashlib
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.5.0-alpha.2'
TOOLS = (
    ('VirtualHsmStudio', 'Virtual HSM Studio', 'windows.spec'),
    ('HsmKeyManager', 'HSM Key Manager', 'key_manager.spec'),
    ('HsmSignVerify', 'HSM Sign & Verify', 'sign.spec'),
)


def compile_installer(compiler, name, product, output, app_id=None):
    bundle = ROOT/'dist'/name
    manifest = ROOT/'work'/f'{name}-uninstall.nsh'
    lines = []
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            relative = str(path.relative_to(bundle)).replace('/', '\\')
            if '$' in relative or '"' in relative:
                raise ValueError('Unsupported filename')
            lines.append(f'Delete "$INSTDIR\\{relative}"')
    for path in sorted((p for p in bundle.rglob('*') if p.is_dir()), key=lambda p:len(p.parts), reverse=True):
        relative = str(path.relative_to(bundle)).replace('/', '\\')
        lines.append(f'RMDir "$INSTDIR\\{relative}"')
    manifest.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    values = dict(PRODUCT=product, VERSION=VERSION, APP_ID=app_id or name,
                  EXECUTABLE=name+'.exe', OUTPUT=output, BUNDLE=bundle,
                  LICENSE_FILE=ROOT/'LICENSE', MANIFEST=manifest)
    subprocess.run([str(compiler), '/V2', *[f'/D{k}={v}' for k,v in values.items()],
                    str(ROOT/'packaging/tool_installer.nsi')], check=True)


def add_notices(bundle):
    dest = bundle/'licenses'
    dest.mkdir(exist_ok=True)
    versions = []
    for name in ('PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','python-pkcs11','asn1crypto','cryptography','cffi','pycparser'):
        package = importlib.metadata.distribution(name)
        versions.append(f'{name} {package.version}')
        for item in package.files or []:
            if '.dist-info' in str(item) and any(x in str(item).lower() for x in ('license','copying')):
                source = Path(package.locate_file(item))
                if source.is_file():
                    target=dest/name/source.name
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(source,target)
    for candidate in ('LICENSE.txt','LICENSE'):
        source=Path(sys.base_prefix)/candidate
        if source.is_file():
            shutil.copy2(source,dest/'Python-LICENSE.txt')
    (dest/'COMPONENTS.txt').write_text('Python '+sys.version.split()[0]+'\n'+'\n'.join(versions)+'\nQt libraries are dynamically linked. https://www.qt.io/qt-for-python\n',encoding='utf-8')
    shutil.copy2(ROOT/'docs/WINDOWS_POC.md',bundle/'POC-GUIDE.md')
    shutil.copy2(ROOT/'docs/SIGNING_GUIDE.md',bundle/'SIGNING-GUIDE.md')
    shutil.copy2(ROOT/'LICENSE',bundle/'LICENSE.txt')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--makensis',type=Path,required=True)
    parser.add_argument('--skip-build',action='store_true')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'dist/release')
    parser.add_argument('--tool', choices=[item[0] for item in TOOLS], action='append')
    args=parser.parse_args()
    output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=True)
    (ROOT/'work').mkdir(exist_ok=True)
    env=os.environ.copy()
    windows=Path(os.environ.get('SystemRoot','C:/Windows'))
    env['PATH']=os.pathsep.join(map(str,(Path(sys.executable).parent,windows/'System32',windows)))
    env['PYINSTALLER_CONFIG_DIR']=str(ROOT/'work/pyinstaller-cache')
    assets=[]
    for name,product,spec in TOOLS:
        if args.tool and name not in args.tool:
            continue
        print('Building '+name,flush=True)
        if not args.skip_build:
            with (ROOT/'work'/f'{name}-release-build.log').open('w',encoding='utf-8') as log:
                subprocess.run([sys.executable,'-m','PyInstaller','--clean','--noconfirm',str(ROOT/'packaging'/spec)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        bundle=ROOT/'dist'/name
        add_notices(bundle)
        installer=output/f'{name}-{VERSION}-Setup.exe'
        compile_installer(args.makensis.resolve(),name,product,installer)
        assets.append(installer)
        archive=shutil.make_archive(str(output/f'{name}-{VERSION}-Windows-x64'), 'zip', root_dir=ROOT/'dist',base_dir=name)
        assets.append(Path(archive))
        print('Packaged '+name,flush=True)
    checksums=''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in assets)
    (output/'SHA256SUMS.txt').write_text(checksums,encoding='utf-8')


if __name__=='__main__':
    main()
