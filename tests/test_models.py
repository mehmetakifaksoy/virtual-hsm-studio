from softhsm_studio.domain.models import ProviderInfo, ProviderKind, SlotInfo, TokenInfo


def test_slot_round_trip() -> None:
    original = SlotInfo(
        slot_id=7,
        description="Test Slot",
        manufacturer="Vendor",
        token_present=True,
        token=TokenInfo(label="TEST", initialized=True, flags=("TOKEN_INITIALIZED",)),
        flags=("TOKEN_PRESENT",),
    )

    restored = SlotInfo.from_mapping(original.to_dict())
    assert restored == original
    assert restored.state == "READY"


def test_provider_kind_mapping() -> None:
    info = ProviderInfo.from_mapping({"name": "Demo", "kind": "pkcs11"})
    assert info.kind is ProviderKind.PKCS11
