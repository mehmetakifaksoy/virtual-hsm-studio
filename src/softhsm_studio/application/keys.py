"""Slot key operations with vendor isolation and explicit virtual simulation."""
import json
import os
import secrets
import subprocess
import sys

from softhsm_studio.domain.models import ObjectClass, ObjectInfo
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from softhsm_studio.process_runtime import worker_command


def slot_keys(service, slot_id, action, pin='', algorithm='', label='', so_pin='', user_pin=''):
    provider = service.provider
    if isinstance(provider, Pkcs11ModuleProvider):
        request = dict(module=str(provider.module_path), slot_id=slot_id, action=action,
                       pin=pin, algorithm=algorithm, label=label, so_pin=so_pin, user_pin=user_pin)
        try:
            result = subprocess.run(
                worker_command("keys"),
                input=json.dumps(request), capture_output=True, text=True, timeout=60,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError('The HSM did not respond. Refresh before retrying; generation may have completed.') from None
        try:
            response = json.loads(result.stdout)
        except ValueError:
            raise RuntimeError('The HSM worker stopped without a response. Refresh before retrying.') from None
        if not response.get('ok'):
            name = response.get('error', 'HSM error')
            raise RuntimeError(f'{name}: operation failed. Check your PIN, token permissions and supported key sizes. Do not retry a failed PIN repeatedly.')
        return response['data']
    if not service.supports_virtual_admin:
        raise RuntimeError('Key management is not available for this provider.')
    if action == 'capabilities':
        return {'choices': ['AES-128', 'AES-192', 'AES-256', 'RSA-2048', 'RSA-3072', 'RSA-4096']}
    session = service.open_session(slot_id, read_write=True)
    try:
        if pin:
            service.login_user(session.session_id, pin)
        message = ''
        if action == 'generate':
            message = provider.simulate_key(session.session_id, algorithm, label)
        return {'keys': [dict(label=o.label, kind=o.object_class.value, algorithm=o.key_type,
                             id=o.cka_id) for o in service.objects(session.session_id)], 'message': message}
    finally:
        service.close_session(session.session_id)
