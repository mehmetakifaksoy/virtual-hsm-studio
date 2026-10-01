from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping


class ProviderKind(StrEnum):
    VIRTUAL = "virtual"
    PKCS11 = "pkcs11"


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    name: str
    kind: ProviderKind
    description: str = ""
    manufacturer: str = ""
    version: str = ""
    module_path: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ProviderInfo":
        raw_kind = data.get("kind", ProviderKind.PKCS11)
        kind = raw_kind if isinstance(raw_kind, ProviderKind) else ProviderKind(str(raw_kind))
        return cls(
            name=str(data.get("name", "")),
            kind=kind,
            description=str(data.get("description", "")),
            manufacturer=str(data.get("manufacturer", "")),
            version=str(data.get("version", "")),
            module_path=str(data.get("module_path", "")),
        )


@dataclass(frozen=True, slots=True)
class TokenInfo:
    label: str = ""
    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    initialized: bool = False
    login_required: bool = False
    user_pin_initialized: bool = False
    write_protected: bool = False
    flags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["flags"] = list(self.flags)
        return data

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TokenInfo":
        return cls(
            label=str(data.get("label", "")),
            manufacturer=str(data.get("manufacturer", "")),
            model=str(data.get("model", "")),
            serial=str(data.get("serial", "")),
            initialized=bool(data.get("initialized", False)),
            login_required=bool(data.get("login_required", False)),
            user_pin_initialized=bool(data.get("user_pin_initialized", False)),
            write_protected=bool(data.get("write_protected", False)),
            flags=tuple(str(item) for item in data.get("flags", ()) or ()),
        )


@dataclass(frozen=True, slots=True)
class SlotInfo:
    slot_id: int
    description: str
    manufacturer: str = ""
    hardware_version: str = ""
    firmware_version: str = ""
    token_present: bool = False
    token: TokenInfo | None = None
    flags: tuple[str, ...] = ()
    diagnostic: str = ""

    @property
    def state(self) -> str:
        if not self.token_present:
            return "EMPTY"
        if self.token is not None and self.token.initialized:
            return "READY"
        return "TOKEN PRESENT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "hardware_version": self.hardware_version,
            "firmware_version": self.firmware_version,
            "token_present": self.token_present,
            "token": self.token.to_dict() if self.token else None,
            "flags": list(self.flags),
            "diagnostic": self.diagnostic,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SlotInfo":
        token_data = data.get("token")
        return cls(
            slot_id=int(data["slot_id"]),
            description=str(data.get("description", "")),
            manufacturer=str(data.get("manufacturer", "")),
            hardware_version=str(data.get("hardware_version", "")),
            firmware_version=str(data.get("firmware_version", "")),
            token_present=bool(data.get("token_present", False)),
            token=TokenInfo.from_mapping(token_data) if isinstance(token_data, Mapping) else None,
            flags=tuple(str(item) for item in data.get("flags", ()) or ()),
            diagnostic=str(data.get("diagnostic", "")),
        )
