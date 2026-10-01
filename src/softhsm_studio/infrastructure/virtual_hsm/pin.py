from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from softhsm_studio.domain.errors import ValidationError


class PinHasher:
    """Versioned PBKDF2-SHA256 PIN hashing for the development-only virtual provider."""

    ALGORITHM = "pbkdf2_sha256"
    ITERATIONS = 600_000
    SALT_BYTES = 16
    DKLEN = 32

    @classmethod
    def hash(cls, pin: str) -> str:
        cls._validate_pin(pin)
        salt = secrets.token_bytes(cls.SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            cls.ITERATIONS,
            dklen=cls.DKLEN,
        )
        return "$".join(
            (
                cls.ALGORITHM,
                str(cls.ITERATIONS),
                base64.urlsafe_b64encode(salt).decode("ascii"),
                base64.urlsafe_b64encode(digest).decode("ascii"),
            )
        )

    @classmethod
    def verify(cls, pin: str, encoded: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, expected_text = encoded.split("$", 3)
            if algorithm != cls.ALGORITHM:
                return False
            iterations = int(iterations_text)
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
        except (ValueError, TypeError):
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)

    @staticmethod
    def _validate_pin(pin: str) -> None:
        if not isinstance(pin, str):
            raise ValidationError("PIN must be text.")
        if not 4 <= len(pin) <= 64:
            raise ValidationError("PIN must contain between 4 and 64 characters.")
