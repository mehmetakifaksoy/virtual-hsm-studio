from pathlib import Path

import pytest

from softhsm_studio.domain.errors import ValidationError
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider


def test_initial_state_has_two_empty_slots(tmp_path: Path) -> None:
    provider = VirtualHsmProvider(tmp_path / "state.json")
    provider.connect()

    slots = provider.list_slots()
    assert [slot.slot_id for slot in slots] == [0, 1]
    assert all(slot.token is None for slot in slots)


def test_create_initialize_verify_and_clear_token(tmp_path: Path) -> None:
    provider = VirtualHsmProvider(tmp_path / "state.json")
    provider.connect()

    slot = provider.create_slot("QA Slot")
    provider.initialize_token(slot.slot_id, "QA_TOKEN", "112233", "445566")

    selected = next(item for item in provider.list_slots() if item.slot_id == slot.slot_id)
    assert selected.token_present is True
    assert selected.token is not None
    assert selected.token.label == "QA_TOKEN"
    assert provider.verify_user_pin(slot.slot_id, "445566") is True
    assert provider.verify_user_pin(slot.slot_id, "000000") is False
    assert provider.verify_so_pin(slot.slot_id, "112233") is True

    provider.clear_token(slot.slot_id)
    selected = next(item for item in provider.list_slots() if item.slot_id == slot.slot_id)
    assert selected.token is None
    assert selected.token_present is False


def test_state_persists(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    first = VirtualHsmProvider(state_path)
    first.connect()
    created = first.create_slot("Persistent Slot")
    first.initialize_token(created.slot_id, "PERSIST", "1234", "5678")

    second = VirtualHsmProvider(state_path)
    second.connect()
    restored = next(item for item in second.list_slots() if item.slot_id == created.slot_id)
    assert restored.description == "Persistent Slot"
    assert restored.token is not None
    assert restored.token.label == "PERSIST"
    assert second.verify_user_pin(created.slot_id, "5678") is True


def test_token_label_enforces_pkcs11_style_32_byte_limit(tmp_path: Path) -> None:
    provider = VirtualHsmProvider(tmp_path / "state.json")
    provider.connect()

    with pytest.raises(ValidationError):
        provider.initialize_token(0, "X" * 33, "1234", "5678")


def test_state_does_not_store_plaintext_pins(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    provider = VirtualHsmProvider(state_path)
    provider.connect()
    provider.initialize_token(0, "SECRET_TEST", "so-12345", "user-67890")

    raw = state_path.read_text(encoding="utf-8")
    assert "so-12345" not in raw
    assert "user-67890" not in raw
    assert "pbkdf2_sha256$" in raw

    public_token = provider.list_slots()[0].token
    assert public_token is not None
    assert not hasattr(public_token, "auth")
