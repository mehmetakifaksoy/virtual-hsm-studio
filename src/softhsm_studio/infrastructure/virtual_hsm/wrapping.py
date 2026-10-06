"""Explicit virtual capability. Ephemeral KEKs, separate from simulated HSM objects."""

import json
import os
from dataclasses import asdict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from softhsm_studio.domain.sovereignty import KeyReference


class VirtualMemoryKeyWrapper:
    mode = "virtual-memory-aes-gcm"

    def __init__(self):
        self._keys = {}

    def provision(self, reference: KeyReference):
        if reference.provider != "virtual":
            raise ValueError("Only explicit virtual references are supported")
        if reference not in self._keys:
            self._keys[reference] = AESGCM.generate_key(bit_length=256)

    def supports(self, reference):
        return reference in self._keys

    def wrap(self, reference, dek):
        if len(dek) != 32:
            raise ValueError("Expected a 256-bit DEK")
        nonce = os.urandom(12)
        aad = json.dumps(asdict(reference), sort_keys=True).encode()
        return nonce + AESGCM(self._keys[reference]).encrypt(nonce, dek, aad)

    def unwrap(self, reference, wrapped):
        if len(wrapped) != 60:
            raise ValueError("Invalid wrapped DEK")
        aad = json.dumps(asdict(reference), sort_keys=True).encode()
        return AESGCM(self._keys[reference]).decrypt(wrapped[:12], wrapped[12:], aad)

    def close(self):
        self._keys.clear()
