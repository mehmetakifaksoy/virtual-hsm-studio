"""Vendor-neutral envelope contracts. References never contain key material."""

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class KeyReference:
    provider: str
    slot: int
    token: str
    key_id: str

    def __post_init__(self):
        if type(self.slot) is not int or self.slot < 0:
            raise ValueError("Invalid slot reference")
        for value in (self.provider, self.token, self.key_id):
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
                raise ValueError("Use opaque identifiers for key references")


@dataclass(frozen=True)
class DekMetadata:
    algorithm: str = "AES-256-GCM"
    bits: int = 256
    origin: str = "local-csprng"

    def __post_init__(self):
        if (self.algorithm, self.bits, self.origin) != ("AES-256-GCM", 256, "local-csprng"):
            raise ValueError("Unsupported DEK metadata")


@dataclass(frozen=True)
class EnvelopeMetadata:
    key_reference: KeyReference
    wrapping_mode: str
    nonce: bytes
    wrapped_dek: bytes = field(repr=False)
    dek: DekMetadata = field(default_factory=DekMetadata)
    version: int = 1
    algorithm: str = "AES-256-GCM"

    def __post_init__(self):
        if type(self.version) is not int or self.version != 1 or self.algorithm != "AES-256-GCM":
            raise ValueError("Unsupported envelope format")
        if (
            not isinstance(self.nonce, bytes)
            or len(self.nonce) != 12
            or not isinstance(self.wrapped_dek, bytes)
            or not 1 <= len(self.wrapped_dek) <= 65536
        ):
            raise ValueError("Invalid envelope metadata")
        if self.wrapping_mode not in ("virtual-memory-aes-gcm", "pkcs11"):
            raise ValueError("Unsupported wrapping mode")

    def authenticated_header(self) -> bytes:
        # Bind reference, algorithm, version and wrapping output to the data tag.
        data = asdict(self)
        data["nonce"] = self.nonce.hex()
        data["wrapped_dek"] = self.wrapped_dek.hex()
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class EnvelopePackage:
    metadata: EnvelopeMetadata
    ciphertext: bytes = field(repr=False)
    tag: bytes = field(repr=False)

    def __post_init__(self):
        if (
            not isinstance(self.ciphertext, bytes)
            or not isinstance(self.tag, bytes)
            or len(self.tag) != 16
        ):
            raise ValueError("Invalid authentication tag")


class KeyWrappingCapability(Protocol):
    mode: str

    def supports(self, reference: KeyReference) -> bool: ...
    def wrap(self, reference: KeyReference, dek: bytes) -> bytes: ...
    def unwrap(self, reference: KeyReference, wrapped: bytes) -> bytes: ...


class LocalCipher(Protocol):
    def generate_dek(self) -> bytes: ...
    def nonce(self) -> bytes: ...
    def encrypt(self, key: bytes, nonce: bytes, data: bytes, aad: bytes) -> bytes: ...
    def decrypt(self, key: bytes, nonce: bytes, data: bytes, aad: bytes) -> bytes: ...
