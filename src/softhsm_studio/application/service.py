from __future__ import annotations

from softhsm_studio.domain.errors import OperationNotSupportedError
from softhsm_studio.domain.models import ProviderInfo, SlotInfo
from softhsm_studio.domain.ports import HsmProvider, VirtualHsmAdmin


class HsmService:
    """Application service that owns the currently active HSM provider."""

    def __init__(self, provider: HsmProvider) -> None:
        provider.connect()
        self._provider = provider

    @property
    def provider(self) -> HsmProvider:
        return self._provider

    @property
    def provider_info(self) -> ProviderInfo:
        return self._provider.info

    @property
    def supports_virtual_admin(self) -> bool:
        return isinstance(self._provider, VirtualHsmAdmin)

    def activate_connected(self, provider: HsmProvider) -> None:
        """Activate a provider that has already connected successfully in a worker thread."""
        old_provider = self._provider
        self._provider = provider
        if old_provider is not provider:
            old_provider.close()

    def slots(self) -> list[SlotInfo]:
        return self._provider.list_slots()

    def refresh(self) -> list[SlotInfo]:
        return self._provider.refresh()

    def create_virtual_slot(self, description: str) -> SlotInfo:
        return self._virtual_admin().create_slot(description)

    def delete_virtual_slot(self, slot_id: int) -> None:
        self._virtual_admin().delete_slot(slot_id)

    def initialize_virtual_token(
        self,
        slot_id: int,
        label: str,
        so_pin: str,
        user_pin: str,
    ) -> None:
        self._virtual_admin().initialize_token(slot_id, label, so_pin, user_pin)

    def clear_virtual_token(self, slot_id: int) -> None:
        self._virtual_admin().clear_token(slot_id)

    def _virtual_admin(self) -> VirtualHsmAdmin:
        provider = self._provider
        if not isinstance(provider, VirtualHsmAdmin):
            raise OperationNotSupportedError(
                "This operation is only available for the Virtual HSM provider."
            )
        return provider
