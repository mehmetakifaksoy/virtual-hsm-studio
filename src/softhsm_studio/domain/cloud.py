"""Vendor-neutral External BYOK contracts. This port has no data upload operation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class ExternalKeyMetadata:
    key_id: str
    status: str
    origin: str = "external"
    mock: bool = True


@dataclass(frozen=True)
class ImportParameters:
    key_id: str
    public_key: bytes = field(repr=False)
    import_token: bytes = field(repr=False)
    expires_at: datetime
    wrapping_algorithm: str = "RSAES_OAEP_SHA_256"


@dataclass(frozen=True)
class WrappedKeyMaterial:
    key_id: str
    ciphertext: bytes = field(repr=False)
    import_token: bytes = field(repr=False)


class ExternalByokClient(Protocol):
    def create_external_key(self) -> ExternalKeyMetadata: ...
    def get_import_parameters(self, key_id: str) -> ImportParameters: ...
    def import_wrapped_key_material(self, material: WrappedKeyMaterial) -> ExternalKeyMetadata: ...
    def status(self, key_id: str) -> ExternalKeyMetadata: ...
