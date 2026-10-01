"""Optional real DLL smoke test, using an isolated temporary token store."""
import os
from pathlib import Path

import pytest
from softhsm_studio.application import HsmService
from softhsm_studio.application.keys import slot_keys
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider


@pytest.mark.skipif(not os.environ.get('SOFTHSM_TEST_MODULE'), reason='Set SOFTHSM_TEST_MODULE to a matching SoftHSM DLL')
def test_admin_to_key_manager_real_dll(tmp_path, monkeypatch):
    module = Path(os.environ['SOFTHSM_TEST_MODULE'])
    tokens = tmp_path / 'tokens'
    tokens.mkdir()
    config = tmp_path / 'softhsm2.conf'
    config.write_text(f'directories.tokendir = {tokens.as_posix()}\nobjectstore.backend = file\nlog.level = ERROR\n', encoding='utf-8')
    monkeypatch.setenv('SOFTHSM2_CONF', str(config))
    admin = HsmService(Pkcs11ModuleProvider(module))
    free = next(s for s in admin.slots() if s.token and not s.token.initialized)
    result = slot_keys(admin, free.slot_id, 'initialize', label='INTEGRATION', so_pin='112233', user_pin='445566')
    assert result['message'].startswith('Token initialized.')
    admin.close()
    manager = HsmService(Pkcs11ModuleProvider(module))
    token_slot = next(s for s in manager.slots() if s.token and s.token.label == 'INTEGRATION')
    aes = slot_keys(manager, token_slot.slot_id, 'generate', pin='445566', algorithm='AES-256', label='aes-test')
    assert any(k['label'] == 'aes-test' for k in aes['keys'])
    rsa = slot_keys(manager, token_slot.slot_id, 'generate', pin='445566', algorithm='RSA-2048', label='rsa-test')
    assert len([k for k in rsa['keys'] if k['label'] == 'rsa-test']) == 2
    manager.close()
    reopened = HsmService(Pkcs11ModuleProvider(module))
    keys = slot_keys(reopened, token_slot.slot_id, 'list', pin='445566')['keys']
    assert len(keys) == 3
    reopened.close()
