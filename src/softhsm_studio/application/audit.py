"""Closed-schema, in-memory security events; no messages or arbitrary payloads."""

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from softhsm_studio.domain.sovereignty import KeyReference


class Operation(StrEnum):
    ENCRYPT = "encrypt-local"
    DECRYPT = "decrypt-local"
    CREATE_EXTERNAL = "create-external-key"
    IMPORT_PARAMETERS = "get-import-parameters"
    IMPORT = "import-wrapped-material"
    STATUS = "external-key-status"


@dataclass(frozen=True)
class AuditEvent:
    operation: Operation
    provider: str
    slot: int
    key_reference: str
    result: str
    timestamp: str


class SafeAudit:
    def __init__(self):
        self._events = deque(maxlen=1000)

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def record(self, operation: Operation, reference: KeyReference, success: bool):
        if not isinstance(operation, Operation) or type(success) is not bool:
            raise ValueError("Audit accepts only typed operations and results")
        self._events.append(
            AuditEvent(
                operation,
                reference.provider,
                reference.slot,
                f"{reference.token}:{reference.key_id}",
                "success" if success else "failure",
                datetime.now(UTC).isoformat(),
            )
        )
