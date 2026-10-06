"""Offline Huawei-shaped BYOK scaffold, never a live KMS client.

RSA OAEP validates fake imports, but no imported material is retained.
No credentials, network, filesystem persistence, encrypt/decrypt or upload API.
"""

import hmac
import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from softhsm_studio.domain.cloud import ExternalKeyMetadata, ImportParameters


def oaep():
    return padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


class FakeHuaweiByokAdapter:
    mock = True

    def __init__(self, clock=None):
        self._clock = clock or (lambda: datetime.now(UTC))
        self._keys = {}
        self._imports = {}

    def create_external_key(self):
        metadata = ExternalKeyMetadata(str(uuid4()), "pending-import")
        self._keys[metadata.key_id] = metadata
        return metadata

    def get_import_parameters(self, key_id):
        if self.status(key_id).status != "pending-import":
            raise ValueError("Key is not pending import")
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        parameters = ImportParameters(
            key_id,
            private.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ),
            os.urandom(32),
            self._clock() + timedelta(minutes=10),
        )
        self._imports[key_id] = (parameters, private)
        return parameters

    def import_wrapped_key_material(self, material):
        parameters, private = self._imports[material.key_id]
        if parameters.expires_at <= self._clock() or not hmac.compare_digest(
            parameters.import_token, material.import_token
        ):
            raise ValueError("Invalid import parameters")
        # Only RSA-wrapped AES-256 material is accepted by this fake.
        if len(material.ciphertext) != 256:
            raise ValueError("Expected wrapped key material")
        value = private.decrypt(material.ciphertext, oaep())
        if len(value) != 32:
            raise ValueError("Expected AES-256 material")
        del value
        self._imports.pop(material.key_id)
        self._keys[material.key_id] = replace(self._keys[material.key_id], status="enabled")
        return self.status(material.key_id)

    def status(self, key_id):
        return self._keys[key_id]
