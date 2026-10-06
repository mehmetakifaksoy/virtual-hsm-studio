import json
from dataclasses import replace

import pytest

from softhsm_studio.application.audit import Operation, SafeAudit
from softhsm_studio.application.sovereignty import ProtectBeforeCloud, ProtectionError
from softhsm_studio.domain.sovereignty import KeyReference
from softhsm_studio.infrastructure.envelope_store import (
    MAX_DATA_BYTES,
    decode_package,
    encode_package,
    protect_file,
)
from softhsm_studio.infrastructure.local_crypto import AesGcmCipher
from softhsm_studio.infrastructure.virtual_hsm.wrapping import VirtualMemoryKeyWrapper


@pytest.fixture
def protection():
    reference = KeyReference("virtual", 7, "token-123", "session-kek")
    wrapper = VirtualMemoryKeyWrapper()
    wrapper.provision(reference)
    audit = SafeAudit()
    return ProtectBeforeCloud(AesGcmCipher(), wrapper, audit), reference


@pytest.mark.parametrize(
    "data",
    [b"", b"customer-plaintext-marker", bytes(range(256)) * 2048],
    ids=["empty", "text", "binary"],
)
def test_encrypt_decrypt_and_metadata_roundtrip(protection, data):
    service, reference = protection
    package = service.encrypt(data, reference)
    restored = decode_package(encode_package(package))
    assert restored == package
    assert restored.metadata.dek.bits == 256
    assert restored.metadata.wrapping_mode == "virtual-memory-aes-gcm"
    assert service.decrypt(restored) == data
    assert [e.result for e in service.audit.events] == ["success", "success"]


@pytest.mark.parametrize("field", ["ciphertext", "tag", "nonce", "wrapped_dek", "key_reference"])
def test_tampered_package_is_rejected(protection, field):
    service, reference = protection
    package = service.encrypt(b"private-data", reference)
    if field == "key_reference":
        alternate = replace(reference, key_id="different-key")
        service.wrapper.provision(alternate)
        broken = replace(package, metadata=replace(package.metadata, key_reference=alternate))
    elif field in ("nonce", "wrapped_dek"):
        value = getattr(package.metadata, field)
        broken = replace(
            package,
            metadata=replace(
                package.metadata,
                **{field: bytes([value[0] ^ 1]) + value[1:]},
            ),
        )
    else:
        value = getattr(package, field)
        broken = replace(package, **{field: bytes([value[0] ^ 1]) + value[1:]})
    with pytest.raises(ProtectionError, match="authentication"):
        service.decrypt(broken)
    assert service.audit.events[-1].result == "failure"


def test_dek_generation_and_wrapping(protection):
    service, reference = protection
    first, second = service.cipher.generate_dek(), service.cipher.generate_dek()
    assert len(first) == len(second) == 32 and first != second
    wrapped = service.wrapper.wrap(reference, first)
    assert len(wrapped) == 60 and first not in wrapped
    assert service.wrapper.unwrap(reference, wrapped) == first
    assert wrapped != service.wrapper.wrap(reference, first)
    package = service.encrypt(b"same", reference)
    assert package.metadata.nonce != service.encrypt(b"same", reference).metadata.nonce
    service.wrapper.close()
    with pytest.raises(ProtectionError):
        service.decrypt(package)


def test_no_secret_persistence_or_logs(protection, tmp_path, caplog, monkeypatch):
    service, reference = protection
    secret = b"PLAINTEXT-DO-NOT-LOG-12345"
    dek = b"secret-dek-marker".ljust(32, b"!")
    assert len(dek) == 32
    monkeypatch.setattr(service.cipher, "generate_dek", lambda: dek)
    source, output = tmp_path / "source", tmp_path / "protected.vhspkg"
    source.write_bytes(secret)
    protect_file(service, source, output, reference)
    assert service.decrypt(decode_package(output.read_text())) == secret
    combined = output.read_text() + repr(service.audit.events) + caplog.text
    assert secret.decode() not in combined and dek.decode() not in combined
    assert sorted(p.name for p in tmp_path.iterdir()) == ["protected.vhspkg", "source"]
    assert set(json.loads(output.read_text())) == {"metadata", "ciphertext", "tag"}


def test_unsupported_wrapper_and_errors_do_not_echo_secrets(protection, caplog, monkeypatch):
    service, reference = protection

    def unsafe(*args):
        raise RuntimeError("PIN private-key credential plaintext SUPER_SECRET")

    monkeypatch.setattr(service.wrapper, "wrap", unsafe)
    with pytest.raises(ProtectionError) as caught:
        service.encrypt(b"SUPER_SECRET", reference)
    assert "SUPER_SECRET" not in str(caught.value) + repr(service.audit.events) + caplog.text
    service.wrapper.close()
    with pytest.raises(ProtectionError):
        service.encrypt(b"secret", reference)
    with pytest.raises(ValueError):
        service.wrapper.provision(replace(reference, provider="pkcs11"))
    with pytest.raises(ValueError):
        service.audit.record("SUPER_SECRET", reference, True)


def test_file_size_limit_and_exclusive_output(protection, tmp_path):
    service, reference = protection
    source, output = tmp_path / "source", tmp_path / "result"
    source.write_bytes(b"small")
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        protect_file(service, source, output, reference)
    assert output.read_bytes() == b"existing"
    with source.open("wb") as stream:
        stream.truncate(MAX_DATA_BYTES + 1)
    with pytest.raises(ValueError, match="16 MiB"):
        protect_file(service, source, tmp_path / "oversize", reference)
    assert not (tmp_path / "oversize").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", 2),
        ("algorithm", "AES-CBC"),
        ("nonce", "bad-base64!"),
        ("wrapping_mode", "unknown"),
    ],
)
def test_invalid_metadata_rejected(protection, field, value):
    service, reference = protection
    data = json.loads(encode_package(service.encrypt(b"data", reference)))
    data["metadata"][field] = value
    with pytest.raises((ValueError, TypeError)):
        decode_package(json.dumps(data))


def test_audit_closed_schema(protection):
    service, reference = protection
    service.audit.record(Operation.ENCRYPT, reference, True)
    event = service.audit.events[0]
    assert set(event.__dataclass_fields__) == {
        "operation",
        "provider",
        "slot",
        "key_reference",
        "result",
        "timestamp",
    }
    assert event.timestamp.endswith("+00:00")
