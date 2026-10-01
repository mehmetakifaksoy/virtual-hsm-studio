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


def test_windows_dll_architecture_mismatch_is_reported(tmp_path, monkeypatch):
    import struct
    from softhsm_studio.infrastructure.pkcs11 import provider as module

    dll = tmp_path / 'vendor.dll'
    data = bytearray(128)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 80)
    data[80:84] = b'PE\x00\x00'
    opposite = 0x14c if struct.calcsize('P') == 8 else 0x8664
    struct.pack_into('<H', data, 84, opposite)
    dll.write_bytes(data)
    provider = Pkcs11ModuleProvider(dll)
    monkeypatch.setattr(module.os, 'name', 'nt')
    with pytest.raises(ProviderLoadError, match='Select a matching PKCS#11 DLL'):
        provider._validate_module_path()
