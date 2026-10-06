from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from softhsm_studio.domain.errors import ProviderLoadError, ProviderNotConnectedError
from softhsm_studio.domain.models import ProviderInfo, ProviderKind, SlotInfo
from softhsm_studio.domain.ports import HsmProvider

from .protocol import Pkcs11Snapshot


class Pkcs11ModuleProvider(HsmProvider):
    """PKCS#11 provider that inspects vendor modules in an isolated subprocess."""

    supports_key_management = True
    DEFAULT_TIMEOUT_SECONDS = 20

    def __init__(
        self, module_path: str | Path, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    ) -> None:
        self.module_path = Path(module_path).expanduser().resolve()
        self.timeout_seconds = timeout_seconds
        self._snapshot: Pkcs11Snapshot | None = None
        self._info = ProviderInfo(
            name=self.module_path.name or "PKCS#11 Module",
            kind=ProviderKind.PKCS11,
            description="PKCS#11 module",
            module_path=str(self.module_path),
        )

    @property
    def info(self) -> ProviderInfo:
        return self._snapshot.provider if self._snapshot else self._info

    @property
    def supports_token_initialization(self) -> bool:
        """Current initialization adapter is limited to SoftHSM modules."""
        return (
            self._snapshot is not None
            and "softhsm"
            in (f"{self.info.name} {self.info.description} {self.info.manufacturer}").lower()
        )

    def connect(self) -> None:
        self._validate_module_path()
        self._snapshot = self._read_snapshot()

    def list_slots(self) -> list[SlotInfo]:
        if self._snapshot is None:
            raise ProviderNotConnectedError("PKCS#11 provider is not connected.")
        return list(self._snapshot.slots)

    def refresh(self) -> list[SlotInfo]:
        if self._snapshot is None:
            raise ProviderNotConnectedError("PKCS#11 provider is not connected.")
        self._snapshot = self._read_snapshot()
        return list(self._snapshot.slots)

    def close(self) -> None:
        self._snapshot = None

    def _validate_module_path(self) -> None:
        if not self.module_path.exists():
            raise ProviderLoadError(f"PKCS#11 module does not exist: {self.module_path}")
        if not self.module_path.is_file():
            raise ProviderLoadError(f"PKCS#11 module path is not a file: {self.module_path}")

        if os.name == "nt" and self.module_path.suffix.lower() == ".dll":
            try:
                with self.module_path.open("rb") as module:
                    if module.read(2) != b"MZ":
                        return
                    module.seek(60)
                    offset = struct.unpack("<I", module.read(4))[0]
                    module.seek(offset)
                    if module.read(4) != b"PE\x00\x00":
                        return
                    machine = struct.unpack("<H", module.read(2))[0]
                expected = 0x8664 if struct.calcsize("P") == 8 else 0x14C
                if machine in (0x14C, 0x8664) and machine != expected:
                    bits = 32 if machine == 0x14C else 64
                    raise ProviderLoadError(
                        f"This DLL is {bits}-bit, but the application runs on {struct.calcsize('P') * 8}-bit Python. "
                        "Select a matching PKCS#11 DLL from your HSM vendor client package."
                    )
            except (OSError, struct.error) as exc:
                raise ProviderLoadError("Could not inspect the DLL architecture.") from exc

    def _read_snapshot(self) -> Pkcs11Snapshot:
        payload = self._run_worker()
        if payload.get("ok") is not True:
            error = payload.get("error", {})
            if isinstance(error, dict):
                error_type = str(error.get("type", "ProviderError"))
                message = str(error.get("message", "Unknown PKCS#11 worker error"))
                raise ProviderLoadError(f"{error_type}: {message}")
            raise ProviderLoadError("PKCS#11 worker returned an invalid error response.")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ProviderLoadError("PKCS#11 worker returned an invalid snapshot response.")
        try:
            return Pkcs11Snapshot.from_mapping(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderLoadError(f"Invalid PKCS#11 worker payload: {exc}") from exc

    def _run_worker(self) -> dict[str, Any]:
        fd, output_name = tempfile.mkstemp(prefix="softhsm-studio-pkcs11-", suffix=".json")
        os.close(fd)
        output_path = Path(output_name)
        command = [
            sys.executable,
            "-m",
            "softhsm_studio.infrastructure.pkcs11.worker",
            "--module",
            str(self.module_path),
            "--output",
            str(output_path),
        ]

        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                creationflags=creationflags,
                env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderLoadError(
                f"PKCS#11 module did not respond within {self.timeout_seconds} seconds."
            ) from exc
        except OSError as exc:
            raise ProviderLoadError(f"Could not start PKCS#11 worker: {exc}") from exc

        try:
            if output_path.stat().st_size == 0:
                stderr = completed.stderr.strip()
                detail = f" Worker stderr: {stderr}" if stderr else ""
                raise ProviderLoadError(
                    f"PKCS#11 worker exited with code {completed.returncode} without a response.{detail}"
                )
            try:
                payload = json.loads(output_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ProviderLoadError(f"Could not parse PKCS#11 worker response: {exc}") from exc
        finally:
            with suppress(OSError):
                output_path.unlink(missing_ok=True)

        if not isinstance(payload, dict):
            raise ProviderLoadError("PKCS#11 worker response root must be a JSON object.")
        return payload
