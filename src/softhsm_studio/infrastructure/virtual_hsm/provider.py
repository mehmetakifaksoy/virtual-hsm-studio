from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from softhsm_studio.domain.errors import (
    ProviderNotConnectedError,
    StateStoreError,
    ValidationError,
)
from softhsm_studio.domain.models import ProviderInfo, ProviderKind, SlotInfo, TokenInfo
from softhsm_studio.domain.ports import HsmProvider

from .pin import PinHasher
from .store import JsonStateStore


class VirtualHsmProvider(HsmProvider):
    """Persistent PKCS#11-style development HSM simulator.

    This provider intentionally models Slot -> Token semantics, but it is not a
    hardware security boundary and must not be used to protect production keys.
    """

    SCHEMA_VERSION = 2
    DEFAULT_SLOT_COUNT = 2

    def __init__(self, state_path: Path | None = None) -> None:
        self._state_path = state_path or self.default_state_path()
        self._store = JsonStateStore(self._state_path)
        self._state: dict[str, Any] | None = None

    @staticmethod
    def default_state_path() -> Path:
        override = os.getenv("SOFTHSM_STUDIO_STATE")
        if override:
            return Path(override).expanduser().resolve()
        return Path.home() / ".softhsm_studio" / "virtual_hsm_v2.json"

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="Virtual HSM",
            kind=ProviderKind.VIRTUAL,
            description="Persistent slot/token simulator for development and testing",
            manufacturer="SoftHSM Studio",
            version="0.2.0",
            module_path=str(self._state_path),
        )

    def connect(self) -> None:
        state = self._store.load_or_create(self._initial_state)
        self._validate_state(state)
        self._state = state

    def close(self) -> None:
        self._state = None

    def list_slots(self) -> list[SlotInfo]:
        state = self._require_state()
        slots = [self._slot_to_public(record) for record in state["slots"]]
        return sorted(slots, key=lambda item: item.slot_id)

    def create_slot(self, description: str) -> SlotInfo:
        state = self._require_state()
        description = description.strip()
        if not description:
            raise ValidationError("Slot description cannot be empty.")
        if len(description) > 128:
            raise ValidationError("Slot description cannot exceed 128 characters.")

        used_ids = {int(record["slot_id"]) for record in state["slots"]}
        slot_id = next(candidate for candidate in range(0, 2**31) if candidate not in used_ids)
        record = self._empty_slot(slot_id, description)
        state["slots"].append(record)
        self._save()
        return self._slot_to_public(record)

    def delete_slot(self, slot_id: int) -> None:
        state = self._require_state()
        before = len(state["slots"])
        state["slots"] = [record for record in state["slots"] if int(record["slot_id"]) != slot_id]
        if len(state["slots"]) == before:
            raise ValidationError(f"Slot {slot_id} does not exist.")
        self._save()

    def initialize_token(self, slot_id: int, label: str, so_pin: str, user_pin: str) -> None:
        label = label.strip()
        self._validate_token_label(label)
        record = self._slot_record(slot_id)

        token = {
            "label": label,
            "manufacturer": "SoftHSM Studio",
            "model": "VHSM-DEV",
            "serial": secrets.token_hex(8).upper(),
            "initialized": True,
            "login_required": True,
            "user_pin_initialized": True,
            "write_protected": False,
            "flags": ["RNG", "LOGIN_REQUIRED", "TOKEN_INITIALIZED", "USER_PIN_INITIALIZED"],
            "auth": {
                "so": PinHasher.hash(so_pin),
                "user": PinHasher.hash(user_pin),
            },
            "objects": [],
            "initialized_at": self._utc_now(),
        }
        record["token"] = token
        record["token_present"] = True
        self._save()

    def clear_token(self, slot_id: int) -> None:
        record = self._slot_record(slot_id)
        record["token"] = None
        record["token_present"] = False
        self._save()

    def verify_user_pin(self, slot_id: int, pin: str) -> bool:
        return self._verify_pin(slot_id, pin, "user")

    def verify_so_pin(self, slot_id: int, pin: str) -> bool:
        return self._verify_pin(slot_id, pin, "so")

    def _verify_pin(self, slot_id: int, pin: str, role: str) -> bool:
        record = self._slot_record(slot_id)
        token = record.get("token")
        if not isinstance(token, Mapping):
            return False
        auth = token.get("auth")
        if not isinstance(auth, Mapping):
            return False
        encoded = auth.get(role)
        return isinstance(encoded, str) and PinHasher.verify(pin, encoded)

    def _slot_record(self, slot_id: int) -> dict[str, Any]:
        state = self._require_state()
        for record in state["slots"]:
            if int(record["slot_id"]) == slot_id:
                return record
        raise ValidationError(f"Slot {slot_id} does not exist.")

    def _slot_to_public(self, record: Mapping[str, Any]) -> SlotInfo:
        token_record = record.get("token")
        token = None
        if isinstance(token_record, Mapping):
            token = TokenInfo.from_mapping(token_record)
        return SlotInfo(
            slot_id=int(record["slot_id"]),
            description=str(record.get("description", "")),
            manufacturer=str(record.get("manufacturer", "SoftHSM Studio")),
            hardware_version=str(record.get("hardware_version", "1.0")),
            firmware_version=str(record.get("firmware_version", "0.2.0")),
            token_present=bool(record.get("token_present", token is not None)),
            token=token,
            flags=tuple(str(item) for item in record.get("flags", ()) or ()),
        )

    def _save(self) -> None:
        state = self._require_state()
        state["updated_at"] = self._utc_now()
        state["slots"].sort(key=lambda record: int(record["slot_id"]))
        self._store.save(state)

    def _require_state(self) -> dict[str, Any]:
        if self._state is None:
            raise ProviderNotConnectedError("Virtual HSM provider is not connected.")
        return self._state

    def _validate_state(self, state: Mapping[str, Any]) -> None:
        if state.get("schema_version") != self.SCHEMA_VERSION:
            raise StateStoreError(
                "Unsupported Virtual HSM state schema. "
                "Use a new state file or migrate the existing state."
            )
        slots = state.get("slots")
        if not isinstance(slots, list):
            raise StateStoreError("Virtual HSM state is invalid: 'slots' must be a list.")
        seen: set[int] = set()
        for record in slots:
            if not isinstance(record, dict) or "slot_id" not in record:
                raise StateStoreError("Virtual HSM state contains an invalid slot record.")
            slot_id = int(record["slot_id"])
            if slot_id in seen:
                raise StateStoreError(f"Virtual HSM state contains duplicate slot ID {slot_id}.")
            seen.add(slot_id)

    @classmethod
    def _initial_state(cls) -> dict[str, Any]:
        now = cls._utc_now()
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "created_at": now,
            "updated_at": now,
            "slots": [
                cls._empty_slot(slot_id, f"Virtual Slot {slot_id}")
                for slot_id in range(cls.DEFAULT_SLOT_COUNT)
            ],
        }

    @staticmethod
    def _empty_slot(slot_id: int, description: str) -> dict[str, Any]:
        return {
            "slot_id": slot_id,
            "description": description,
            "manufacturer": "SoftHSM Studio",
            "hardware_version": "1.0",
            "firmware_version": "0.2.0",
            "token_present": False,
            "token": None,
            "flags": ["SOFTWARE_SLOT"],
        }

    @staticmethod
    def _validate_token_label(label: str) -> None:
        if not label:
            raise ValidationError("Token label cannot be empty.")
        if len(label.encode("utf-8")) > 32:
            raise ValidationError("Token label must fit within 32 UTF-8 bytes.")

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")
