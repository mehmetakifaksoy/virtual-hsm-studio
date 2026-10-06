import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AesGcmCipher:
    def generate_dek(self) -> bytes:
        return AESGCM.generate_key(bit_length=256)

    def nonce(self) -> bytes:
        return os.urandom(12)

    def encrypt(self, key, nonce, data, aad):
        return AESGCM(key).encrypt(nonce, data, aad)

    def decrypt(self, key, nonce, data, aad):
        return AESGCM(key).decrypt(nonce, data, aad)
