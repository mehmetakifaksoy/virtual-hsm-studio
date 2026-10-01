from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from .models import ProviderInfo, SlotInfo


class HsmProvider(ABC):
    """Provider boundary used by the application and GUI layers."""

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        raise NotImplementedError

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_slots(self) -> list[SlotInfo]:
        raise NotImplementedError

    def refresh(self) -> list[SlotInfo]:
        return self.list_slots()

    def close(self) -> None:
        """Release resources. Providers without resources may keep the default implementation."""


@runtime_checkable
class VirtualHsmAdmin(Protocol):
    """Administrative operations available only on the development virtual HSM."""

    def create_slot(self, description: str) -> SlotInfo: ...

    def delete_slot(self, slot_id: int) -> None: ...

    def initialize_token(self, slot_id: int, label: str, so_pin: str, user_pin: str) -> None: ...

    def clear_token(self, slot_id: int) -> None: ...

    def verify_user_pin(self, slot_id: int, pin: str) -> bool: ...

    def verify_so_pin(self, slot_id: int, pin: str) -> bool: ...
