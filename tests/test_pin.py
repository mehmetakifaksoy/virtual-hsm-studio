import pytest

from softhsm_studio.domain.errors import ValidationError
from softhsm_studio.infrastructure.virtual_hsm.pin import PinHasher


def test_pin_hash_is_salted_and_verifiable() -> None:
    first = PinHasher.hash("123456")
    second = PinHasher.hash("123456")

    assert first != second
    assert PinHasher.verify("123456", first) is True
    assert PinHasher.verify("bad-pin", first) is False


def test_short_pin_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PinHasher.hash("123")
