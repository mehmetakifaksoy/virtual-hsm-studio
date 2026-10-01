from __future__ import annotations

from softhsm_studio.domain.errors import OperationNotSupportedError
from softhsm_studio.domain.models import (
    MechanismInfo,
    ObjectClass,
    ObjectInfo,
    ProviderInfo,
    SessionInfo,
    SessionRole,
    SlotInfo,
)
from softhsm_studio.domain.ports import (
    HsmProvider,
    MechanismCapability,
    ObjectCapability,
    SessionCapability,
    VirtualHsmAdmin,
)


class HsmService:
    """Application service for the currently active HSM provider.

    The presentation layer should communicate with providers through this
    service instead of depending directly on provider implementations.

    Optional HSM capabilities are detected at runtime. This allows Virtual HSM
    and PKCS#11 providers to evolve independently without breaking the GUI.
    """

    def __init__(
        self,
        provider: HsmProvider,
    ) -> None:
        provider.connect()
        self._provider = provider

    @property
    def provider(self) -> HsmProvider:
        """Return the currently active provider."""
        return self._provider

    @property
    def provider_info(self) -> ProviderInfo:
        """Return metadata for the active provider."""
        return self._provider.info

    # ------------------------------------------------------------------
    # Capability discovery
    # ------------------------------------------------------------------

    @property
    def supports_virtual_admin(self) -> bool:
        return isinstance(
            self._provider,
            VirtualHsmAdmin,
        )

    @property
    def supports_sessions(self) -> bool:
        return isinstance(
            self._provider,
            SessionCapability,
        )

    @property
    def supports_objects(self) -> bool:
        return isinstance(
            self._provider,
            ObjectCapability,
        )

    @property
    def supports_mechanisms(self) -> bool:
        return isinstance(
            self._provider,
            MechanismCapability,
        )

    # ------------------------------------------------------------------
    # Provider lifecycle
    # ------------------------------------------------------------------

    def activate_connected(
        self,
        provider: HsmProvider,
    ) -> None:
        """Activate a provider that is already connected.

        This method is useful when provider initialization has already been
        completed in a background worker.

        The previous provider is closed after the new provider becomes active.
        """

        old_provider = self._provider

        self._provider = provider

        if old_provider is not provider:
            old_provider.close()

    def close(self) -> None:
        """Close the currently active provider."""
        self._provider.close()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def slots(self) -> list[SlotInfo]:
        """Return all slots exposed by the active provider."""
        return self._provider.list_slots()

    def refresh(self) -> list[SlotInfo]:
        """Refresh provider state and return the current slots."""
        return self._provider.refresh()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def open_session(
        self,
        slot_id: int,
        *,
        read_write: bool = False,
    ) -> SessionInfo:
        """Open a provider session for the selected slot."""

        return self._session_capability().open_session(
            slot_id,
            read_write=read_write,
        )

    def close_session(
        self,
        session_id: int,
    ) -> None:
        """Close an active provider session."""

        self._session_capability().close_session(
            session_id
        )

    def sessions(
        self,
        slot_id: int | None = None,
    ) -> list[SessionInfo]:
        """Return active sessions.

        If slot_id is specified, only sessions belonging to that slot are
        returned.
        """

        return self._session_capability().list_sessions(
            slot_id
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login_user(
        self,
        session_id: int,
        pin: str,
    ) -> SessionInfo:
        """Authenticate a session as the normal token USER."""

        return self._session_capability().login(
            session_id,
            SessionRole.USER,
            pin,
        )

    def login_so(
        self,
        session_id: int,
        pin: str,
    ) -> SessionInfo:
        """Authenticate a session as the Security Officer."""

        return self._session_capability().login(
            session_id,
            SessionRole.SO,
            pin,
        )

    def logout(
        self,
        session_id: int,
    ) -> SessionInfo:
        """Logout the current USER/SO authentication state."""

        return self._session_capability().logout(
            session_id
        )

    # ------------------------------------------------------------------
    # Objects
    # ------------------------------------------------------------------

    def objects(
        self,
        session_id: int,
        object_class: ObjectClass | None = None,
    ) -> list[ObjectInfo]:
        """Return objects visible to a session."""

        return self._object_capability().list_objects(
            session_id,
            object_class,
        )

    # ------------------------------------------------------------------
    # Mechanisms
    # ------------------------------------------------------------------

    def mechanisms(
        self,
        slot_id: int,
    ) -> list[MechanismInfo]:
        """Return cryptographic mechanisms exposed by a slot."""

        return self._mechanism_capability().list_mechanisms(
            slot_id
        )

    # ------------------------------------------------------------------
    # Virtual HSM administration
    # ------------------------------------------------------------------

    def create_virtual_slot(
        self,
        description: str,
    ) -> SlotInfo:
        return self._virtual_admin().create_slot(
            description
        )

    def delete_virtual_slot(
        self,
        slot_id: int,
    ) -> None:
        self._virtual_admin().delete_slot(
            slot_id
        )

    def initialize_virtual_token(
        self,
        slot_id: int,
        label: str,
        so_pin: str,
        user_pin: str,
    ) -> None:
        self._virtual_admin().initialize_token(
            slot_id,
            label,
            so_pin,
            user_pin,
        )

    def clear_virtual_token(
        self,
        slot_id: int,
    ) -> None:
        self._virtual_admin().clear_token(
            slot_id
        )

    # ------------------------------------------------------------------
    # Capability guards
    # ------------------------------------------------------------------

    def _session_capability(
        self,
    ) -> SessionCapability:
        provider = self._provider

        if not isinstance(
            provider,
            SessionCapability,
        ):
            raise OperationNotSupportedError(
                "The active HSM provider does not support "
                "session management."
            )

        return provider

    def _object_capability(
        self,
    ) -> ObjectCapability:
        provider = self._provider

        if not isinstance(
            provider,
            ObjectCapability,
        ):
            raise OperationNotSupportedError(
                "The active HSM provider does not support "
                "object discovery."
            )

        return provider

    def _mechanism_capability(
        self,
    ) -> MechanismCapability:
        provider = self._provider

        if not isinstance(
            provider,
            MechanismCapability,
        ):
            raise OperationNotSupportedError(
                "The active HSM provider does not support "
                "mechanism discovery."
            )

        return provider

    def _virtual_admin(
        self,
    ) -> VirtualHsmAdmin:
        provider = self._provider

        if not isinstance(
            provider,
            VirtualHsmAdmin,
        ):
            raise OperationNotSupportedError(
                "This operation is only available "
                "for the Virtual HSM provider."
            )

        return provider