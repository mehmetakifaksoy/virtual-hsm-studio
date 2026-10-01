from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping


class ProviderKind(StrEnum):
    """Supported HSM provider types."""

    VIRTUAL = "virtual"
    PKCS11 = "pkcs11"


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """Metadata describing an HSM provider."""

    name: str
    kind: ProviderKind
    description: str = ""
    manufacturer: str = ""
    version: str = ""
    module_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "version": self.version,
            "module_path": self.module_path,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ProviderInfo":
        raw_kind = data.get("kind", ProviderKind.PKCS11)

        kind = (
            raw_kind
            if isinstance(raw_kind, ProviderKind)
            else ProviderKind(str(raw_kind))
        )

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
    """Provider-independent token metadata."""

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
            user_pin_initialized=bool(
                data.get("user_pin_initialized", False)
            ),
            write_protected=bool(data.get("write_protected", False)),
            flags=tuple(
                str(item)
                for item in data.get("flags", ()) or ()
            ),
        )


@dataclass(frozen=True, slots=True)
class SlotInfo:
    """Provider-independent slot metadata."""

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
            hardware_version=str(
                data.get("hardware_version", "")
            ),
            firmware_version=str(
                data.get("firmware_version", "")
            ),
            token_present=bool(
                data.get("token_present", False)
            ),
            token=(
                TokenInfo.from_mapping(token_data)
                if isinstance(token_data, Mapping)
                else None
            ),
            flags=tuple(
                str(item)
                for item in data.get("flags", ()) or ()
            ),
            diagnostic=str(data.get("diagnostic", "")),
        )


class SessionRole(StrEnum):
    """Authentication role associated with an HSM session."""

    PUBLIC = "public"
    USER = "user"
    SO = "so"


class SessionState(StrEnum):
    """Provider-independent representation of PKCS#11 session state."""

    RO_PUBLIC_SESSION = "ro_public_session"
    RO_USER_FUNCTIONS = "ro_user_functions"

    RW_PUBLIC_SESSION = "rw_public_session"
    RW_USER_FUNCTIONS = "rw_user_functions"

    RW_SO_FUNCTIONS = "rw_so_functions"


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """Public representation of an active HSM session."""

    session_id: int
    slot_id: int
    state: SessionState

    role: SessionRole = SessionRole.PUBLIC
    read_write: bool = False
    opened_at: str = ""
    flags: tuple[str, ...] = ()

    @property
    def authenticated(self) -> bool:
        return self.role is not SessionRole.PUBLIC

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "slot_id": self.slot_id,
            "state": self.state.value,
            "role": self.role.value,
            "read_write": self.read_write,
            "opened_at": self.opened_at,
            "flags": list(self.flags),
        }

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
    ) -> "SessionInfo":
        raw_state = data.get(
            "state",
            SessionState.RO_PUBLIC_SESSION,
        )

        state = (
            raw_state
            if isinstance(raw_state, SessionState)
            else SessionState(str(raw_state))
        )

        raw_role = data.get(
            "role",
            SessionRole.PUBLIC,
        )

        role = (
            raw_role
            if isinstance(raw_role, SessionRole)
            else SessionRole(str(raw_role))
        )

        return cls(
            session_id=int(data["session_id"]),
            slot_id=int(data["slot_id"]),
            state=state,
            role=role,
            read_write=bool(
                data.get("read_write", False)
            ),
            opened_at=str(
                data.get("opened_at", "")
            ),
            flags=tuple(
                str(item)
                for item in data.get("flags", ()) or ()
            ),
        )


class ObjectClass(StrEnum):
    """PKCS#11 object categories exposed by the application."""

    DATA = "data"
    CERTIFICATE = "certificate"
    PUBLIC_KEY = "public_key"
    PRIVATE_KEY = "private_key"
    SECRET_KEY = "secret_key"


@dataclass(frozen=True, slots=True)
class ObjectInfo:
    """Safe metadata representation of a token object.

    Secret or private key material must never be stored
    in this model.
    """

    object_id: str
    object_class: ObjectClass

    label: str = ""
    cka_id: str = ""
    key_type: str = ""

    token_object: bool = True
    private: bool = False
    sensitive: bool = False
    extractable: bool = True

    modifiable: bool = True
    copyable: bool = True
    destroyable: bool = True

    attributes: tuple[
        tuple[str, Any],
        ...
    ] = ()

    @property
    def attribute_map(self) -> dict[str, Any]:
        return dict(self.attributes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "object_class": self.object_class.value,
            "label": self.label,
            "cka_id": self.cka_id,
            "key_type": self.key_type,
            "token_object": self.token_object,
            "private": self.private,
            "sensitive": self.sensitive,
            "extractable": self.extractable,
            "modifiable": self.modifiable,
            "copyable": self.copyable,
            "destroyable": self.destroyable,
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
    ) -> "ObjectInfo":
        raw_class = data.get(
            "object_class",
            ObjectClass.DATA,
        )

        object_class = (
            raw_class
            if isinstance(raw_class, ObjectClass)
            else ObjectClass(str(raw_class))
        )

        raw_attributes = data.get(
            "attributes",
            {},
        )

        attributes: tuple[
            tuple[str, Any],
            ...
        ]

        if isinstance(raw_attributes, Mapping):
            attributes = tuple(
                (str(key), value)
                for key, value
                in raw_attributes.items()
            )

        elif isinstance(
            raw_attributes,
            (list, tuple),
        ):
            attributes = tuple(
                (
                    str(item[0]),
                    item[1],
                )
                for item in raw_attributes
                if isinstance(item, (list, tuple))
                and len(item) == 2
            )

        else:
            attributes = ()

        return cls(
            object_id=str(data["object_id"]),
            object_class=object_class,
            label=str(
                data.get("label", "")
            ),
            cka_id=str(
                data.get("cka_id", "")
            ),
            key_type=str(
                data.get("key_type", "")
            ),
            token_object=bool(
                data.get("token_object", True)
            ),
            private=bool(
                data.get("private", False)
            ),
            sensitive=bool(
                data.get("sensitive", False)
            ),
            extractable=bool(
                data.get("extractable", True)
            ),
            modifiable=bool(
                data.get("modifiable", True)
            ),
            copyable=bool(
                data.get("copyable", True)
            ),
            destroyable=bool(
                data.get("destroyable", True)
            ),
            attributes=attributes,
        )


@dataclass(frozen=True, slots=True)
class MechanismInfo:
    """Cryptographic capability exposed by an HSM provider."""

    name: str

    mechanism_id: int | None = None
    min_key_size: int | None = None
    max_key_size: int | None = None

    flags: tuple[str, ...] = ()

    def supports(
        self,
        capability: str,
    ) -> bool:
        normalized = capability.strip().upper()

        return normalized in {
            flag.upper()
            for flag in self.flags
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mechanism_id": self.mechanism_id,
            "min_key_size": self.min_key_size,
            "max_key_size": self.max_key_size,
            "flags": list(self.flags),
        }

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
    ) -> "MechanismInfo":
        raw_mechanism_id = data.get(
            "mechanism_id"
        )

        raw_min_key_size = data.get(
            "min_key_size"
        )

        raw_max_key_size = data.get(
            "max_key_size"
        )

        return cls(
            name=str(data["name"]),
            mechanism_id=(
                int(raw_mechanism_id)
                if raw_mechanism_id is not None
                else None
            ),
            min_key_size=(
                int(raw_min_key_size)
                if raw_min_key_size is not None
                else None
            ),
            max_key_size=(
                int(raw_max_key_size)
                if raw_max_key_size is not None
                else None
            ),
            flags=tuple(
                str(item)
                for item in data.get("flags", ()) or ()
            ),
        )