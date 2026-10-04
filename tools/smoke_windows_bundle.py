"""Verify the built binaries without relying on the developer Python environment."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser=argparse.ArgumentParser()
parser.add_argument('bundle',type=Path)
parser.add_argument('--module',type=Path)
args=parser.parse_args()
bundle=args.bundle.resolve()
env=os.environ.copy()
for key in ('PYTHONPATH','PYTHONHOME','SOFTHSM2_CONF','SOFTHSM_STUDIO_STATE'):
    env.pop(key,None)
env['QT_QPA_PLATFORM']='offscreen'
flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
report=bundle.parent/'smoke-report.json'
env['SOFTHSM_STUDIO_SMOKE_REPORT']=str(report)
result=subprocess.run([str(bundle/'VirtualHsmStudio.exe'),'--smoke-test'],env=env,timeout=45,creationflags=flags)
if result.returncode:
    diagnostic=report.read_text(encoding='utf-8') if report.exists() else 'No smoke diagnostic; check executable startup.'
    raise RuntimeError(f'GUI smoke failed: {result.returncode}; {diagnostic}')
print('Packaged GUI and Virtual HSM smoke: passed')
worker=str(bundle/'HsmWorker.exe')
with tempfile.TemporaryDirectory(prefix='hsm-packaged-test-') as directory:
    root=Path(directory)
    invalid=subprocess.run([worker,'keys'],input='{}',text=True,capture_output=True,env=env,timeout=30,creationflags=flags)
    assert json.loads(invalid.stdout)['ok'] is False
    print('Packaged worker stdin/stdout: passed')
    if args.module:
        tokens=root/'tokens';tokens.mkdir()
        config=root/'softhsm2.conf'
        config.write_text(f'directories.tokendir = {tokens.as_posix()}\nobjectstore.backend = file\nlog.level = ERROR\n',encoding='utf-8')
        env['SOFTHSM2_CONF']=str(config)
        def snapshot():
            response=root/'snapshot.json'
            subprocess.run([worker,'snapshot','--module',str(args.module.resolve()),'--output',str(response)],env=env,timeout=30,check=True,creationflags=flags)
            payload=json.loads(response.read_text(encoding='utf-8'))
            assert payload['ok']
            return payload['data']
        free=next(s for s in snapshot()['slots'] if s.get('token') and not s['token']['initialized'])
        def operation(**values):
            request={'module':str(args.module.resolve()),**values}
            response=subprocess.run([worker,'keys'],input=json.dumps(request),text=True,capture_output=True,env=env,timeout=45,creationflags=flags)
            payload=json.loads(response.stdout)
            assert payload['ok'], payload.get('error','Worker failure')
            return payload['data']
        operation(action='initialize',slot_id=free['slot_id'],label='PACKAGED_SMOKE',so_pin='smoke-so-pin',user_pin='smoke-user-pin')
        slot=next(s for s in snapshot()['slots'] if s.get('token') and s['token']['label']=='PACKAGED_SMOKE')
        result=operation(action='generate',slot_id=slot['slot_id'],pin='smoke-user-pin',algorithm='AES-256',label='test-key')
        assert any(row['label']=='test-key' for row in result['keys'])
        assert all(set(row)<= {'label','kind','algorithm','id'} for row in result['keys'])
        print('Packaged real SoftHSM initialize / AES generation / metadata-only response: passed')
