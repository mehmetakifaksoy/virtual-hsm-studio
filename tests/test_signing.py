import base64
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
from softhsm_studio.application.signing import signing_operation, verify_files
from softhsm_studio.process_runtime import worker_command
from softhsm_studio.infrastructure.pkcs11.sign_worker import read_document


def test_document_limit(tmp_path):
    path = tmp_path/'large.bin'
    with path.open('wb') as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    with pytest.raises(ValueError):
        read_document(path)


def test_real_hsm_sign_export_verify_and_tamper(tmp_path, monkeypatch):
    frozen = os.environ.get('SIGN_TEST_FROZEN_WORKER')
    if frozen:
        command = lambda operation: [frozen, operation]
        monkeypatch.setitem(globals(), 'worker_command', command)
        monkeypatch.setattr('softhsm_studio.application.signing.worker_command', command)
    module = os.environ.get('SOFTHSM_TEST_MODULE')
    if not module:
        pytest.skip('Set SOFTHSM_TEST_MODULE')
    tokens=tmp_path/'tokens';tokens.mkdir()
    config=tmp_path/'softhsm.conf'
    config.write_text(f'directories.tokendir = {tokens.as_posix()}\nobjectstore.backend = file\nlog.level = ERROR\n')
    monkeypatch.setenv('SOFTHSM2_CONF',str(config))
    def snapshot():
        dest=tmp_path/'snapshot.json'
        subprocess.run(worker_command('snapshot')+['--module',module,'--output',str(dest)],check=True)
        return json.loads(dest.read_text(encoding='utf-8'))['data']['slots']
    def keys(**request):
        result=subprocess.run(worker_command('keys'), input=json.dumps(dict(module=module,**request)),text=True,capture_output=True)
        payload=json.loads(result.stdout)
        assert payload['ok'],payload
        return payload['data']
    free=next(s for s in snapshot() if s.get('token') and not s['token']['initialized'])
    keys(action='initialize',slot_id=free['slot_id'],label='SIGN_TEST',so_pin='12345678',user_pin='87654321')
    slot=next(s for s in snapshot() if s.get('token') and s['token']['label']=='SIGN_TEST')
    keys(action='generate',slot_id=slot['slot_id'],pin='87654321',algorithm='RSA-2048',label='signing-key')
    base=dict(module=module,slot_id=slot['slot_id'],pin='87654321')
    rows=signing_operation(dict(base,action='list'))['keys']
    assert len(rows)==1
    document=tmp_path/'document.txt';document.write_bytes(b'POC signing test')
    result=signing_operation(dict(base,action='sign',key_id=rows[0]['id'],file=str(document)))
    assert set(result)=={'signature','public_key','sha256','algorithm'}
    signature=tmp_path/'document.sig';signature.write_bytes(base64.b64decode(result['signature']))
    public=tmp_path/'public.pem';public.write_text(result['public_key'])
    assert verify_files(document,signature,public)
    document.write_bytes(b'Changed document')
    assert not verify_files(document,signature,public)
    document.write_bytes(b'POC signing test')
    signature.write_bytes(b'wrong signature')
    assert not verify_files(document,signature,public)
    signature.write_bytes(base64.b64decode(result['signature']))
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    wrong = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    public.write_bytes(wrong.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    assert not verify_files(document, signature, public)
    exported=signing_operation(dict(base,action='export',key_id=rows[0]['id']))
    assert exported['public_key']==result['public_key']


def test_sign_app_starts_without_simulator_or_private_export():
    from PySide6.QtWidgets import QApplication
    from softhsm_studio.sign_app import SignWindow
    app = QApplication.instance() or QApplication([])
    window = SignWindow()
    assert window.demo_button.isHidden()
    assert not window.open_button.isEnabled()
    assert window.windowTitle() == 'HSM Sign & Verify'
    window.close()


def test_sign_dialog_finishes_key_loading_without_dialog_signal_collision(monkeypatch):
    from types import SimpleNamespace
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from softhsm_studio.sign_app import SignDialog
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr('softhsm_studio.sign_app.signing_operation', lambda request: {'keys':[{'label':'test', 'id':'01'}]})
    dialog = SignDialog(SimpleNamespace(provider=SimpleNamespace(module_path='unused.dll')), SimpleNamespace(slot_id=0), None)
    dialog.show()
    dialog.pin.setText('test-pin')
    dialog.load.click()
    for _ in range(300):
        QTest.qWait(10)
        if dialog.worker is None:
            break
    assert dialog.worker is None
    assert dialog.keys.count() == 1
    assert dialog.load.isEnabled()
    assert dialog.pin.text() == ''
    assert 'Working' not in dialog.status.text()
    dialog.reject()
