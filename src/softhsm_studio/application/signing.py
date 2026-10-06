"""Transport and independent verification for detached RSA signatures."""
import json
import subprocess
from pathlib import Path
from softhsm_studio.process_runtime import worker_command
from softhsm_studio.infrastructure.pkcs11.sign_worker import read_document


def signing_operation(request):
    try:
        result = subprocess.run(worker_command('sign'), input=json.dumps(request), text=True,
                                capture_output=True, timeout=60,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        response = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError('HSM timed out. Check the device before retrying.') from None
    except (ValueError, OSError):
        raise RuntimeError('Signing worker did not return a valid response.') from None
    if not response.get('ok'):
        raise RuntimeError('HSM operation failed. Check your PIN, RSA key permissions and SHA256_RSA_PKCS support. No automatic retry was made.')
    return response['data']


def verify_files(document, signature, public_key):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.exceptions import InvalidSignature
    key = serialization.load_pem_public_key(Path(public_key).read_bytes())
    if not isinstance(key, rsa.RSAPublicKey):
        raise ValueError('Select an RSA public key in PEM format.')
    try:
        key.verify(Path(signature).read_bytes(), read_document(document), padding.PKCS1v15(), hashes.SHA256())
        return True
    except InvalidSignature:
        return False
