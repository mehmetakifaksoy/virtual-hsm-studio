from __future__ import annotations

import os
import secrets
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from softhsm_studio.domain.errors import (
    AuthenticationError,
    ProviderNotConnectedError,
    SessionError,
    StateStoreError,
    ValidationError,
)
from softhsm_studio.domain.models import (
    MechanismInfo,
    ObjectClass,
    ObjectInfo,
    ProviderInfo,
    ProviderKind,
    SessionInfo,
    SessionRole,
    SessionState,
    SlotInfo,
    TokenInfo,
)
from softhsm_studio.domain.ports import HsmProvider

from .pin import PinHasher
from .store import JsonStateStore


class VirtualHsmProvider(HsmProvider):
    """Persistent PKCS#11-style development HSM simulator.

    Persistent state models:

        Slot -> Token -> Objects

    Session and authentication state are process-local and are discarded
    when the provider disconnects.

    This provider is intended only for development, testing and POC usage.
    It is not a hardware-backed security boundary.
    """

    SCHEMA_VERSION = 2
    DEFAULT_SLOT_COUNT = 2
    VERSION = "0.3.0"

    def __init__(
        self,
        state_path: Path | None = None,
    ) -> None:
        self._state_path = (
            state_path
            or self.default_state_path()
        )

        self._store = JsonStateStore(
            self._state_path
        )

        self._state: dict[str, Any] | None = None

        self._sessions: dict[
            int,
            SessionInfo,
        ] = {}

        self._slot_roles: dict[
            int,
            SessionRole,
        ] = {}

        self._next_session_id = 1

    @staticmethod
    def default_state_path() -> Path:
        override = os.getenv(
            "SOFTHSM_STUDIO_STATE"
        )

        if override:
            return (
                Path(override)
                .expanduser()
                .resolve()
            )

        return (
            Path.home()
            / ".softhsm_studio"
            / "virtual_hsm_v2.json"
        )

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="Virtual HSM",
            kind=ProviderKind.VIRTUAL,
            description=(
                "Persistent slot/token simulator "
                "for development and testing"
            ),
            manufacturer="Virtual HSM Studio",
            version=self.VERSION,
            module_path=str(
                self._state_path
            ),
        )

    def connect(self) -> None:
        state = self._store.load_or_create(
            self._initial_state
        )

        self._validate_state(state)

        self._state = state

        self._sessions.clear()
        self._slot_roles.clear()

        self._next_session_id = 1

    def close(self) -> None:
        self._sessions.clear()
        self._slot_roles.clear()

        self._state = None

    # ------------------------------------------------------------------
    # Slot management
    # ------------------------------------------------------------------

    def list_slots(self) -> list[SlotInfo]:
        state = self._require_state()

        slots = [
            self._slot_to_public(record)
            for record in state["slots"]
        ]

        return sorted(
            slots,
            key=lambda item: item.slot_id,
        )

    def create_slot(
        self,
        description: str,
    ) -> SlotInfo:
        state = self._require_state()

        description = description.strip()

        if not description:
            raise ValidationError(
                "Slot description cannot be empty."
            )

        if len(description) > 128:
            raise ValidationError(
                "Slot description cannot exceed "
                "128 characters."
            )

        used_ids = {
            int(record["slot_id"])
            for record in state["slots"]
        }

        slot_id = next(
            candidate
            for candidate in range(
                0,
                2**31,
            )
            if candidate not in used_ids
        )

        record = self._empty_slot(
            slot_id,
            description,
        )

        state["slots"].append(record)

        self._save()

        return self._slot_to_public(
            record
        )

    def delete_slot(
        self,
        slot_id: int,
    ) -> None:
        state = self._require_state()

        self._ensure_no_open_sessions(
            slot_id
        )

        before = len(
            state["slots"]
        )

        state["slots"] = [
            record
            for record in state["slots"]
            if int(record["slot_id"])
            != slot_id
        ]

        if len(state["slots"]) == before:
            raise ValidationError(
                f"Slot {slot_id} does not exist."
            )

        self._slot_roles.pop(
            slot_id,
            None,
        )

        self._save()

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def initialize_token(
        self,
        slot_id: int,
        label: str,
        so_pin: str,
        user_pin: str,
    ) -> None:
        self._ensure_no_open_sessions(
            slot_id
        )

        label = label.strip()

        self._validate_token_label(
            label
        )

        record = self._slot_record(
            slot_id
        )

        token = {
            "label": label,
            "manufacturer": (
                "Virtual HSM Studio"
            ),
            "model": "VHSM-DEV",
            "serial": (
                secrets
                .token_hex(8)
                .upper()
            ),
            "initialized": True,
            "login_required": True,
            "user_pin_initialized": True,
            "write_protected": False,
            "flags": [
                "RNG",
                "LOGIN_REQUIRED",
                "TOKEN_INITIALIZED",
                "USER_PIN_INITIALIZED",
            ],
            "auth": {
                "so": PinHasher.hash(
                    so_pin
                ),
                "user": PinHasher.hash(
                    user_pin
                ),
            },
            "objects": [],
            "initialized_at": (
                self._utc_now()
            ),
        }

        record["token"] = token
        record["token_present"] = True

        self._slot_roles.pop(
            slot_id,
            None,
        )

        self._save()

    def clear_token(
        self,
        slot_id: int,
    ) -> None:
        self._ensure_no_open_sessions(
            slot_id
        )

        record = self._slot_record(
            slot_id
        )

        record["token"] = None
        record["token_present"] = False

        self._slot_roles.pop(
            slot_id,
            None,
        )

        self._save()

    # ------------------------------------------------------------------
    # PIN verification
    # ------------------------------------------------------------------

    def verify_user_pin(
        self,
        slot_id: int,
        pin: str,
    ) -> bool:
        return self._verify_pin(
            slot_id,
            pin,
            "user",
        )

    def verify_so_pin(
        self,
        slot_id: int,
        pin: str,
    ) -> bool:
        return self._verify_pin(
            slot_id,
            pin,
            "so",
        )

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def open_session(
        self,
        slot_id: int,
        *,
        read_write: bool = False,
    ) -> SessionInfo:
        self._require_initialized_token(
            slot_id
        )

        role = self._slot_roles.get(
            slot_id,
            SessionRole.PUBLIC,
        )

        if (
            role is SessionRole.SO
            and not read_write
        ):
            raise SessionError(
                "A read-only session cannot "
                "be opened while the SO "
                "is logged in."
            )

        session_id = (
            self._next_session_id
        )

        self._next_session_id += 1

        flags = (
            (
                "SERIAL_SESSION",
                "RW_SESSION",
            )
            if read_write
            else (
                "SERIAL_SESSION",
            )
        )

        session = SessionInfo(
            session_id=session_id,
            slot_id=slot_id,
            state=self._state_for(
                read_write,
                role,
            ),
            role=role,
            read_write=read_write,
            opened_at=self._utc_now(),
            flags=flags,
        )

        self._sessions[
            session_id
        ] = session

        return session

    def close_session(
        self,
        session_id: int,
    ) -> None:
        session = self._session(
            session_id
        )

        del self._sessions[
            session_id
        ]

        remaining = any(
            item.slot_id
            == session.slot_id
            for item
            in self._sessions.values()
        )

        if not remaining:
            self._slot_roles.pop(
                session.slot_id,
                None,
            )

    def list_sessions(
        self,
        slot_id: int | None = None,
    ) -> list[SessionInfo]:
        self._require_state()

        sessions = list(
            self._sessions.values()
        )

        if slot_id is not None:
            self._slot_record(
                slot_id
            )

            sessions = [
                item
                for item in sessions
                if item.slot_id
                == slot_id
            ]

        return sorted(
            sessions,
            key=lambda item:
            item.session_id,
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(
        self,
        session_id: int,
        role: SessionRole,
        pin: str,
    ) -> SessionInfo:
        session = self._session(
            session_id
        )

        if role is SessionRole.PUBLIC:
            raise AuthenticationError(
                "PUBLIC is not an "
                "authentication role."
            )

        current_role = (
            self._slot_roles.get(
                session.slot_id,
                SessionRole.PUBLIC,
            )
        )

        if (
            current_role
            is not SessionRole.PUBLIC
        ):
            if current_role is role:
                raise AuthenticationError(
                    f"{role.value.upper()} "
                    "is already logged in."
                )

            raise AuthenticationError(
                "Cannot login as "
                f"{role.value.upper()} "
                "while "
                f"{current_role.value.upper()} "
                "is logged in."
            )

        if role is SessionRole.SO:
            if not session.read_write:
                raise SessionError(
                    "SO login requires "
                    "a read-write session."
                )

            read_only_exists = any(
                item.slot_id
                == session.slot_id
                and not item.read_write
                for item
                in self._sessions.values()
            )

            if read_only_exists:
                raise SessionError(
                    "SO login is not allowed "
                    "while read-only sessions "
                    "are open."
                )

            valid = self.verify_so_pin(
                session.slot_id,
                pin,
            )

        else:
            valid = (
                self.verify_user_pin(
                    session.slot_id,
                    pin,
                )
            )

        if not valid:
            raise AuthenticationError(
                "PIN verification failed."
            )

        self._slot_roles[
            session.slot_id
        ] = role

        self._apply_slot_role(
            session.slot_id,
            role,
        )

        return self._session(
            session_id
        )

    def logout(
        self,
        session_id: int,
    ) -> SessionInfo:
        session = self._session(
            session_id
        )

        current_role = (
            self._slot_roles.get(
                session.slot_id,
                SessionRole.PUBLIC,
            )
        )

        if (
            current_role
            is SessionRole.PUBLIC
        ):
            raise AuthenticationError(
                "No USER or SO is "
                "currently logged in."
            )

        self._slot_roles.pop(
            session.slot_id,
            None,
        )

        self._apply_slot_role(
            session.slot_id,
            SessionRole.PUBLIC,
        )

        return self._session(
            session_id
        )

    # ------------------------------------------------------------------
    # Objects
    # ------------------------------------------------------------------

    def list_objects(
        self,
        session_id: int,
        object_class: (
            ObjectClass | None
        ) = None,
    ) -> list[ObjectInfo]:
        session = self._session(
            session_id
        )

        token = self._token_record(
            session.slot_id
        )

        raw_objects = token.get(
            "objects",
            [],
        )

        if not isinstance(
            raw_objects,
            list,
        ):
            raise StateStoreError(
                "Virtual token 'objects' "
                "must be a list."
            )

        objects: list[
            ObjectInfo
        ] = []

        for raw_object in raw_objects:
            if not isinstance(
                raw_object,
                Mapping,
            ):
                continue

            try:
                item = (
                    ObjectInfo
                    .from_mapping(
                        raw_object
                    )
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            if (
                item.private
                and not session.authenticated
            ):
                continue

            if (
                object_class is not None
                and item.object_class
                is not object_class
            ):
                continue

            objects.append(
                item
            )

        return sorted(
            objects,
            key=lambda item: (
                item.label,
                item.object_id,
            ),
        )

    # ------------------------------------------------------------------
    # Mechanisms
    # ------------------------------------------------------------------

    def list_mechanisms(
        self,
        slot_id: int,
    ) -> list[MechanismInfo]:
        self._require_initialized_token(
            slot_id
        )

        # Crypto operations will be added in later milestones.
        # We intentionally do not advertise mechanisms that
        # the Virtual HSM cannot execute yet.

        return []

    # ------------------------------------------------------------------
    # Internal session helpers
    # ------------------------------------------------------------------

    def _apply_slot_role(
        self,
        slot_id: int,
        role: SessionRole,
    ) -> None:
        for (
            session_id,
            session,
        ) in tuple(
            self._sessions.items()
        ):
            if (
                session.slot_id
                != slot_id
            ):
                continue

            self._sessions[
                session_id
            ] = replace(
                session,
                role=role,
                state=self._state_for(
                    session.read_write,
                    role,
                ),
            )

    @staticmethod
    def _state_for(
        read_write: bool,
        role: SessionRole,
    ) -> SessionState:
        if role is SessionRole.SO:
            if not read_write:
                raise SessionError(
                    "SO sessions must "
                    "be read-write."
                )

            return (
                SessionState
                .RW_SO_FUNCTIONS
            )

        if role is SessionRole.USER:
            return (
                SessionState
                .RW_USER_FUNCTIONS
                if read_write
                else SessionState
                .RO_USER_FUNCTIONS
            )

        return (
            SessionState
            .RW_PUBLIC_SESSION
            if read_write
            else SessionState
            .RO_PUBLIC_SESSION
        )

    def _session(
        self,
        session_id: int,
    ) -> SessionInfo:
        self._require_state()

        try:
            return self._sessions[
                session_id
            ]

        except KeyError as exc:
            raise SessionError(
                f"Session {session_id} "
                "does not exist."
            ) from exc

    def _ensure_no_open_sessions(
        self,
        slot_id: int,
    ) -> None:
        self._slot_record(
            slot_id
        )

        open_session_exists = any(
            item.slot_id == slot_id
            for item
            in self._sessions.values()
        )

        if open_session_exists:
            raise SessionError(
                f"Slot {slot_id} has "
                "open sessions. Close them "
                "before changing the "
                "slot/token."
            )

    # ------------------------------------------------------------------
    # Internal token helpers
    # ------------------------------------------------------------------

    def _require_initialized_token(
        self,
        slot_id: int,
    ) -> Mapping[str, Any]:
        token = self._token_record(
            slot_id
        )

        if not bool(
            token.get(
                "initialized",
                False,
            )
        ):
            raise ValidationError(
                f"Token in slot {slot_id} "
                "is not initialized."
            )

        return token

    def _token_record(
        self,
        slot_id: int,
    ) -> Mapping[str, Any]:
        record = self._slot_record(
            slot_id
        )

        token = record.get(
            "token"
        )

        if (
            not record.get(
                "token_present"
            )
            or not isinstance(
                token,
                Mapping,
            )
        ):
            raise ValidationError(
                f"Slot {slot_id} does "
                "not contain a token."
            )

        return token

    def _verify_pin(
        self,
        slot_id: int,
        pin: str,
        role: str,
    ) -> bool:
        record = self._slot_record(
            slot_id
        )

        token = record.get(
            "token"
        )

        if not isinstance(
            token,
            Mapping,
        ):
            return False

        auth = token.get(
            "auth"
        )

        if not isinstance(
            auth,
            Mapping,
        ):
            return False

        encoded = auth.get(
            role
        )

        return (
            isinstance(
                encoded,
                str,
            )
            and PinHasher.verify(
                pin,
                encoded,
            )
        )

    # ------------------------------------------------------------------
    # Internal slot/state helpers
    # ------------------------------------------------------------------

    def _slot_record(
        self,
        slot_id: int,
    ) -> dict[str, Any]:
        state = self._require_state()

        for record in state["slots"]:
            if (
                int(record["slot_id"])
                == slot_id
            ):
                return record

        raise ValidationError(
            f"Slot {slot_id} "
            "does not exist."
        )

    def _slot_to_public(
        self,
        record: Mapping[str, Any],
    ) -> SlotInfo:
        token_record = record.get(
            "token"
        )

        token = None

        if isinstance(
            token_record,
            Mapping,
        ):
            token = (
                TokenInfo
                .from_mapping(
                    token_record
                )
            )

        return SlotInfo(
            slot_id=int(
                record["slot_id"]
            ),
            description=str(
                record.get(
                    "description",
                    "",
                )
            ),
            manufacturer=str(
                record.get(
                    "manufacturer",
                    "Virtual HSM Studio",
                )
            ),
            hardware_version=str(
                record.get(
                    "hardware_version",
                    "1.0",
                )
            ),
            firmware_version=str(
                record.get(
                    "firmware_version",
                    self.VERSION,
                )
            ),
            token_present=bool(
                record.get(
                    "token_present",
                    token is not None,
                )
            ),
            token=token,
            flags=tuple(
                str(item)
                for item
                in record.get(
                    "flags",
                    (),
                ) or ()
            ),
        )

    def _save(self) -> None:
        state = self._require_state()

        state["updated_at"] = (
            self._utc_now()
        )

        state["slots"].sort(
            key=lambda record:
            int(record["slot_id"])
        )

        self._store.save(
            state
        )

    def _require_state(
        self,
    ) -> dict[str, Any]:
        if self._state is None:
            raise (
                ProviderNotConnectedError(
                    "Virtual HSM provider "
                    "is not connected."
                )
            )

        return self._state

    def _validate_state(
        self,
        state: Mapping[str, Any],
    ) -> None:
        if (
            state.get(
                "schema_version"
            )
            != self.SCHEMA_VERSION
        ):
            raise StateStoreError(
                "Unsupported Virtual HSM "
                "state schema. Use a new "
                "state file or migrate "
                "the existing state."
            )

        slots = state.get(
            "slots"
        )

        if not isinstance(
            slots,
            list,
        ):
            raise StateStoreError(
                "Virtual HSM state is "
                "invalid: 'slots' must "
                "be a list."
            )

        seen: set[int] = set()

        for record in slots:
            if (
                not isinstance(
                    record,
                    dict,
                )
                or "slot_id"
                not in record
            ):
                raise StateStoreError(
                    "Virtual HSM state "
                    "contains an invalid "
                    "slot record."
                )

            slot_id = int(
                record["slot_id"]
            )

            if slot_id in seen:
                raise StateStoreError(
                    "Virtual HSM state "
                    "contains duplicate "
                    f"slot ID {slot_id}."
                )

            seen.add(
                slot_id
            )

    @classmethod
    def _initial_state(
        cls,
    ) -> dict[str, Any]:
        now = cls._utc_now()

        return {
            "schema_version": (
                cls.SCHEMA_VERSION
            ),
            "created_at": now,
            "updated_at": now,
            "slots": [
                cls._empty_slot(
                    slot_id,
                    f"Virtual Slot {slot_id}",
                )
                for slot_id in range(
                    cls.DEFAULT_SLOT_COUNT
                )
            ],
        }

    @classmethod
    def _empty_slot(
        cls,
        slot_id: int,
        description: str,
    ) -> dict[str, Any]:
        return {
            "slot_id": slot_id,
            "description": description,
            "manufacturer": (
                "Virtual HSM Studio"
            ),
            "hardware_version": "1.0",
            "firmware_version": (
                cls.VERSION
            ),
            "token_present": False,
            "token": None,
            "flags": [
                "SOFTWARE_SLOT"
            ],
        }

    @staticmethod
    def _validate_token_label(
        label: str,
    ) -> None:
        if not label:
            raise ValidationError(
                "Token label cannot "
                "be empty."
            )

        if (
            len(
                label.encode(
                    "utf-8"
                )
            )
            > 32
        ):
            raise ValidationError(
                "Token label must fit "
                "within 32 UTF-8 bytes."
            )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(
            UTC
        ).isoformat(
            timespec="seconds"
        )