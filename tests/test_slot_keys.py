import pytest

from softhsm_studio.application import HsmService
from softhsm_studio.application.keys import slot_keys
from softhsm_studio.domain.errors import AuthenticationError, ValidationError
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider


def initialized_service(path):
    service = HsmService(VirtualHsmProvider(path))
    service.initialize_virtual_token(0, 'test', '112233', '445566')
    return service


def test_simulated_pair_persists_without_key_material(tmp_path):
    path = tmp_path / 'state.json'
    service = initialized_service(path)
    result = slot_keys(service, 0, 'generate', pin='445566', algorithm='RSA-2048', label='signing')
    assert 'No cryptographic key material' in result['message']
    assert service.sessions() == []
    service.close()
    reopened = HsmService(VirtualHsmProvider(path))
    keys = slot_keys(reopened, 0, 'list', pin='445566')['keys']
    assert len(keys) == 2
    assert {k['kind'] for k in keys} == {'public_key', 'private_key'}
    assert len({k['id'] for k in keys}) == 1
    assert reopened.sessions() == []
    reopened.close()


def test_wrong_pin_and_duplicate_do_not_create_extra_objects(tmp_path):
    service = initialized_service(tmp_path / 'state.json')
    with pytest.raises(AuthenticationError):
        slot_keys(service, 0, 'generate', pin='incorrect', algorithm='AES-256', label='aes')
    assert service.sessions() == []
    slot_keys(service, 0, 'generate', pin='445566', algorithm='AES-256', label='aes')
    with pytest.raises(ValidationError):
        slot_keys(service, 0, 'generate', pin='445566', algorithm='AES-256', label='aes')
    assert len(slot_keys(service, 0, 'list', pin='445566')['keys']) == 1
    assert service.sessions() == []
    service.close()


def test_public_listing_hides_private_keys(tmp_path):
    service = initialized_service(tmp_path / 'state.json')
    slot_keys(service, 0, 'generate', pin='445566', algorithm='RSA-2048', label='pair')
    public = slot_keys(service, 0, 'list')['keys']
    assert len(public) == 1
    assert public[0]['kind'] == 'public_key'
    authenticated = slot_keys(service, 0, 'list', pin='445566')['keys']
    assert len(authenticated) == 2
    assert service.sessions() == []
    service.close()
