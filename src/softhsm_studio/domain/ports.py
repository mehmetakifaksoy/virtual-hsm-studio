from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from .models import (
    MechanismInfo,
    ObjectClass,
    ObjectInfo,
    ProviderInfo,
    SessionInfo,
    SessionRole,
    SlotInfo,
)


class HsmProvider(ABC):
    """Base provider boundary used by the application and GUI layers.

    The base interface intentionally contains only the capabilities that every
    provider must support.

    Optional capabilities such as sessions, objects, mechanisms and virtual
    HSM administration are exposed through separate runtime-checkable
    protocols below.

    This allows providers to evolve independently without forcing every
    provider implementation to immediately implement every feature.
    """

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Return provider metadata."""
        raise NotImplementedError

    @abstractmethod
    def connect(self) -> None:
        """Initialize or connect to the provider."""
        raise NotImplementedError

    @abstractmethod
    def list_slots(self) -> list[SlotInfo]:
        """Return all slots exposed by the provider."""
        raise NotImplementedError

    def refresh(self) -> list[SlotInfo]:
        """Refresh provider state and return the current slot list."""
        return self.list_slots()

    def close(self) -> None:
        """Release provider resources.

        Providers without persistent resources may keep this default
        implementation.
        """


@runtime_checkable
class SessionCapability(Protocol):
    """Session lifecycle and authentication capability.

    Providers implementing this protocol expose PKCS#11-style session
    behavior without requiring the base HsmProvider interface to change.
    """

    def open_session(
        self,
        slot_id: int,
        *,
        read_write: bool = False,
    ) -> SessionInfo:
        """Open a session on a slot."""
        ...

    def close_session(
        self,
        session_id: int,
    ) -> None:
        """Close one active session."""
        ...

    def list_sessions(
        self,
        slot_id: int | None = None,
    ) -> list[SessionInfo]:
        """Return active sessions.

        When slot_id is provided, only sessions belonging to that slot should
        be returned.
        """
        ...

    def login(
        self,
        session_id: int,
        role: SessionRole,
        pin: str,
    ) -> SessionInfo:
        """Authenticate an existing session.

        Supported roles are expected to include USER and SO.
        """
        ...

    def logout(
        self,
        session_id: int,
    ) -> SessionInfo:
        """Return an authenticated session to PUBLIC state."""
        ...


@runtime_checkable
class ObjectCapability(Protocol):
    """Object discovery capability for token/session objects."""

    def list_objects(
        self,
        session_id: int,
        object_class: ObjectClass | None = None,
    ) -> list[ObjectInfo]:
        """Return visible objects for a session.

        object_class may be used to filter the result.
        """
        ...


@runtime_checkable
class MechanismCapability(Protocol):
    """Mechanism discovery capability."""

    def list_mechanisms(
        self,
        slot_id: int,
    ) -> list[MechanismInfo]:
        """Return cryptographic mechanisms supported by a slot/token."""
        ...


@runtime_checkable
class VirtualHsmAdmin(Protocol):
    """Administrative operations available only on the development Virtual HSM.

    These methods are intentionally kept separate from HsmProvider because
    physical/vendor HSM providers may not expose the same administrative
    workflow.
    """

    def create_slot(
        self,
        description: str,
    ) -> SlotInfo:
        """Create a new virtual slot."""
        ...

    def delete_slot(
        self,
        slot_id: int,
    ) -> None:
        """Delete an existing virtual slot."""
        ...

    def initialize_token(
        self,
        slot_id: int,
        label: str,
        so_pin: str,
        user_pin: str,
    ) -> None:
        """Initialize a token inside a virtual slot."""
        ...

    def clear_token(
        self,
        slot_id: int,
    ) -> None:
        """Remove token state from a virtual slot."""
        ...

    def verify_user_pin(
        self,
        slot_id: int,
        pin: str,
    ) -> bool:
        """Verify the configured USER PIN."""
        ...

    def verify_so_pin(
        self,
        slot_id: int,
        pin: str,
    ) -> bool:
        """Verify the configured Security Officer PIN."""
        ...


@runtime_checkable
class SessionObjectProvider(
    SessionCapability,
    ObjectCapability,
    MechanismCapability,
    Protocol,
):
    """Convenience protocol for providers implementing all v0.3 capabilities."""

    pass