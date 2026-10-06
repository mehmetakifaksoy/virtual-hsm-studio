"""Launch isolated vendor workers in source and installed applications."""
import sys
from pathlib import Path


def worker_command(operation: str) -> list[str]:
    if operation not in {"snapshot", "keys", "sign"}:
        raise ValueError("Unknown worker operation")
    if getattr(sys, "frozen", False):
        worker = Path(sys.executable).with_name("HsmWorker.exe")
        if not worker.is_file():
            raise RuntimeError("The HSM worker is missing. Repair or reinstall Virtual HSM Studio.")
        return [str(worker), operation]
    module = {"snapshot": "worker", "keys": "key_worker", "sign": "sign_worker"}[operation]
    return [sys.executable, "-m", f"softhsm_studio.infrastructure.pkcs11.{module}"]
