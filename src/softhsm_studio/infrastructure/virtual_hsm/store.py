from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from softhsm_studio.domain.errors import StateStoreError


class JsonStateStore:
    """Small atomic JSON store used only by the virtual development provider."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_or_create(self, factory: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            state = factory()
            self.save(state)
            return state

        try:
            raw = self.path.read_text(encoding="utf-8")
            state = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise StateStoreError(f"Virtual HSM state could not be read: {exc}") from exc

        if not isinstance(state, dict):
            raise StateStoreError("Virtual HSM state root must be a JSON object.")
        return state

    def save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = -1
        temp_path: Path | None = None
        try:
            fd, temp_name = tempfile.mkstemp(
                dir=str(self.path.parent),
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                text=True,
            )
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                fd = -1
                json.dump(state, handle, indent=2, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            self._restrict_permissions(self.path)
        except OSError as exc:
            raise StateStoreError(f"Virtual HSM state could not be saved: {exc}") from exc
        finally:
            if fd >= 0:
                os.close(fd)
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _restrict_permissions(path: Path) -> None:
        if os.name != "nt":
            try:
                path.chmod(0o600)
            except OSError:
                pass
