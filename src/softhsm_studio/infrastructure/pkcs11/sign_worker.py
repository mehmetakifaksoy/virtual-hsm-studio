"""Isolated RSA/SHA-256 signing. No private key attributes leave the token."""
import base64
import json
import sys
from pathlib import Path

MAX_FILE_SIZE = 16 * 1024 * 1024


def read_document(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise ValueError('File exceeds the 16 MiB POC limit')
    return data


def operate(request):
    import pkcs11
    from pkcs11 import Attribute as A, ObjectClass as C, KeyType as K, Mechanism as M
    from pkcs11.util.rsa import encode_rsa_public_key
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    library = pkcs11.lib(request['module'])
    slot = next(s for s in library.get_slots() if int(s.slot_id) == request['slot_id'])
    if M.SHA256_RSA_PKCS not in set(slot.get_mechanisms()):
        raise ValueError('RSA PKCS1 v1.5 with SHA256 is not advertised')
    with slot.get_token().open(user_pin=request['pin']) as session:
        if request['action'] == 'list':
            rows = []
            for key in session.get_objects({A.CLASS:C.PRIVATE_KEY, A.KEY_TYPE:K.RSA, A.SIGN:True}):
                ident = bytes(key[A.ID])
                if ident:
                    rows.append({'label':str(key[A.LABEL]), 'id':ident.hex()})
            return {'keys':rows}
        ident = bytes.fromhex(request['key_id'])
        private = list(session.get_objects({A.CLASS:C.PRIVATE_KEY, A.KEY_TYPE:K.RSA, A.ID:ident, A.SIGN:True}))
        public = list(session.get_objects({A.CLASS:C.PUBLIC_KEY, A.KEY_TYPE:K.RSA, A.ID:ident}))
        if len(private) != 1 or len(public) != 1:
            raise ValueError('A unique RSA key pair with matching ID is required')
        pub = serialization.load_der_public_key(encode_rsa_public_key(public[0]))
        pem = pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        if request['action'] == 'export':
            return {'public_key':pem}
        if request['action'] != 'sign':
            raise ValueError('Unknown action')
        data = read_document(request['file'])
        signature = bytes(private[0].sign(data, mechanism=M.SHA256_RSA_PKCS))
        # Reject mismatched public/private pairs before offering any output.
        pub.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
        import hashlib
        return {'signature':base64.b64encode(signature).decode('ascii'), 'public_key':pem,
                'sha256':hashlib.sha256(data).hexdigest(), 'algorithm':'RSA-PKCS1-v1_5-SHA256'}


def main():
    try:
        request = json.load(sys.stdin)
        result = operate(request)
        print(json.dumps({'ok':True, 'data':result}))
        return 0
    except Exception as exc:
        print(json.dumps({'ok':False, 'error':type(exc).__name__}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
