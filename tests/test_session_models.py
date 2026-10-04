from softhsm_studio.domain.models import (
    MechanismInfo,
    ObjectClass,
    ObjectInfo,
    SessionInfo,
    SessionRole,
    SessionState,
)


def test_session_info_authenticated_user() -> None:
    session = SessionInfo(
        session_id=1001,
        slot_id=0,
        state=SessionState.RW_USER_FUNCTIONS,
        role=SessionRole.USER,
        read_write=True,
    )

    assert session.authenticated is True
    assert session.role is SessionRole.USER
    assert session.read_write is True


def test_public_session_is_not_authenticated() -> None:
    session = SessionInfo(
        session_id=1002,
        slot_id=1,
        state=SessionState.RO_PUBLIC_SESSION,
    )

    assert session.authenticated is False
    assert session.role is SessionRole.PUBLIC


def test_session_round_trip() -> None:
    original = SessionInfo(
        session_id=44,
        slot_id=2,
        state=SessionState.RW_SO_FUNCTIONS,
        role=SessionRole.SO,
        read_write=True,
        flags=("SERIAL_SESSION", "RW_SESSION"),
    )

    restored = SessionInfo.from_mapping(original.to_dict())

    assert restored == original


def test_private_key_object_metadata() -> None:
    obj = ObjectInfo(
        object_id="obj-001",
        object_class=ObjectClass.PRIVATE_KEY,
        label="signing-key",
        cka_id="01",
        key_type="RSA",
        private=True,
        sensitive=True,
        extractable=False,
    )

    assert obj.object_class is ObjectClass.PRIVATE_KEY
    assert obj.private is True
    assert obj.sensitive is True
    assert obj.extractable is False


def test_object_round_trip() -> None:
    original = ObjectInfo(
        object_id="obj-002",
        object_class=ObjectClass.SECRET_KEY,
        label="aes-data-key",
        cka_id="02",
        key_type="AES",
        private=True,
        sensitive=True,
        extractable=False,
        attributes=(
            ("CKA_ENCRYPT", True),
            ("CKA_DECRYPT", True),
        ),
    )

    restored = ObjectInfo.from_mapping(original.to_dict())

    assert restored == original
    assert restored.attribute_map["CKA_ENCRYPT"] is True


def test_mechanism_capabilities() -> None:
    mechanism = MechanismInfo(
        name="CKM_AES_GCM",
        mechanism_id=0x00001087,
        min_key_size=16,
        max_key_size=32,
        flags=("ENCRYPT", "DECRYPT"),
    )

    assert mechanism.supports("encrypt") is True
    assert mechanism.supports("SIGN") is False


def test_mechanism_round_trip() -> None:
    original = MechanismInfo(
        name="CKM_RSA_PKCS",
        mechanism_id=1,
        min_key_size=1024,
        max_key_size=4096,
        flags=("SIGN", "VERIFY", "ENCRYPT", "DECRYPT"),
    )

    restored = MechanismInfo.from_mapping(original.to_dict())

    assert restored == original
