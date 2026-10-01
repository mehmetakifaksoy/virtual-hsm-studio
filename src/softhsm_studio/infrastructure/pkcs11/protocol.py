from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from softhsm_studio.domain.models import ProviderInfo, SlotInfo


@dataclass(frozen=True, slots=True)
class Pkcs11Snapshot:
    provider: ProviderInfo
    slots: tuple[SlotInfo, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Pkcs11Snapshot":
        provider_data = data.get("provider")
        slots_data = data.get("slots")
        if not isinstance(provider_data, Mapping):
            raise ValueError("Worker response is missing provider metadata.")
        if not isinstance(slots_data, list):
            raise ValueError("Worker response is missing slot data.")
        return cls(
            provider=ProviderInfo.from_mapping(provider_data),
            slots=tuple(SlotInfo.from_mapping(item) for item in slots_data),
        )
