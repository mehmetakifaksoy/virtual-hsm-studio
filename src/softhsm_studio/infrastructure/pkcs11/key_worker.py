"""One isolated operation. PIN arrives through stdin, never through argv or files."""
import json
import secrets
import sys


def operate(request):
    import pkcs11
    from pkcs11 import Attribute as A, KeyType as K, Mechanism as M, ObjectClass as C

    library = pkcs11.lib(request['module'])
    slot = next((s for s in library.get_slots() if int(s.slot_id) == request['slot_id']), None)
    if slot is None:
        raise ValueError('The selected slot is no longer available. Refresh the slot list.')
    token = slot.get_token()
    if request['action'] == 'initialize':
        # PKCS#11 has no generic CreateSlot call. SoftHSM exposes a free slot;
        # C_InitToken initializes it and SoftHSM then publishes another free slot.
        import ctypes
        if 'softhsm' not in (str(library.library_description) + str(library.manufacturer_id)).lower():
            raise ValueError('Generic vendor initialization is not enabled; use its admin client.')
        if token.flags & pkcs11.TokenFlag.TOKEN_INITIALIZED:
            raise ValueError('This token is already initialized. Select the free slot.')
        label = request['label'].strip().encode('utf-8')
        if not 1 <= len(label) <= 32:
            raise ValueError('Token name must be 1–32 UTF-8 bytes.')
        for item in library.get_slots(token_present=True):
            if item.get_token().label.strip() == request['label'].strip():
                raise ValueError('That token name already exists.')
        pin = request['so_pin'].encode('utf-8')
        if not pin or not request['user_pin']:
            raise ValueError('Both PINs are required.')
        native = ctypes.CDLL(request['module'])
        initialize = native.C_InitToken
        initialize.argtypes = [ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p]
        initialize.restype = ctypes.c_ulong
        code = initialize(slot.slot_id, pin, len(pin), label.ljust(32, b' '))
        if code:
            raise RuntimeError(f'C_InitToken returned {code}')
        # SoftHSM can reassign the slot ID when the token receives a serial.
        try:
            initialized = next(s.get_token() for s in library.get_slots(token_present=True)
                               if s.get_token().label.strip() == request['label'].strip())
            with initialized.open(rw=True, so_pin=request['so_pin']) as session:
                session.init_pin(request['user_pin'])
        except Exception:
            return {'message': 'Token created, but USER PIN setup failed. Use the SoftHSM admin utility to finish setup; do not initialize this token again.'}
        return {'message': 'Token initialized. Open Key Manager and load the same DLL to create keys.'}
    available = set(slot.get_mechanisms())
    choices = []
    if M.AES_KEY_GEN in available:
        choices.extend(['AES-128', 'AES-192', 'AES-256'])
    if M.RSA_PKCS_KEY_PAIR_GEN in available:
        choices.extend(['RSA-2048', 'RSA-3072', 'RSA-4096'])
    if request['action'] == 'capabilities':
        return {'choices': choices}
    with token.open(rw=request['action'] == 'generate', user_pin=request.get('pin') or None) as session:
        if request['action'] == 'generate':
            choice = request['algorithm']
            if choice not in choices:
                raise ValueError('This HSM does not advertise the requested generation mechanism.')
            label = request['label'].strip()
            if not label:
                raise ValueError('Enter a key name.')
            if next(iter(session.get_objects({A.LABEL: label})), None) is not None:
                raise ValueError('That key name already exists. Choose another name.')
            algorithm, bits = choice.split('-')
            params = dict(label=label, id=secrets.token_bytes(16), store=True)
            protected = {A.PRIVATE: True, A.SENSITIVE: True, A.EXTRACTABLE: False}
            if algorithm == 'AES':
                session.generate_key(K.AES, int(bits), template=protected, **params)
            else:
                session.generate_keypair(K.RSA, int(bits), private_template=protected, **params)
            # Continue listing in the same authenticated session.
        rows = []
        for obj in session.get_objects():
            def read(attribute, default=''):
                try:
                    return obj[attribute]
                except pkcs11.exceptions.PKCS11Error:
                    return default
            category = read(A.CLASS)
            if category not in (C.SECRET_KEY, C.PUBLIC_KEY, C.PRIVATE_KEY):
                continue
            ident = read(A.ID, b'')
            rows.append({'label': str(read(A.LABEL)), 'kind': getattr(category, 'name', str(category)),
                         'algorithm': getattr(read(A.KEY_TYPE), 'name', ''),
                         'id': ident.hex() if isinstance(ident, bytes) else str(ident)})
        return {'keys': rows, 'message': 'Key generated and stored on the HSM.' if request['action'] == 'generate' else ''}


def main():
    try:
        request = json.load(sys.stdin)
        result = operate(request)
        print(json.dumps({'ok': True, 'data': result}))
    except Exception as exc:
        # Never echo vendor messages: they may include authentication input.
        print(json.dumps({'ok': False, 'error': type(exc).__name__}))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
