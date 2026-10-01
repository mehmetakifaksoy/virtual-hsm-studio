from pathlib import Path

import pytest

from softhsm_studio.domain.errors import ProviderLoadError, ProviderNotConnectedError
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider


def test_nonexistent_module_is_rejected(tmp_path: Path) -> None:
    provider = Pkcs11ModuleProvider(tmp_path / "missing.dll")
    with pytest.raises(ProviderLoadError):
        provider.connect()


def test_slots_require_connection(tmp_path: Path) -> None:
    module = tmp_path / "dummy.dll"
    module.write_bytes(b"not-a-real-dll")
    provider = Pkcs11ModuleProvider(module)

    with pytest.raises(ProviderNotConnectedError):
        provider.list_slots()
