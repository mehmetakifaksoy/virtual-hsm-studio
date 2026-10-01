from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip("\x00 ")
    return str(value).strip("\x00 ")


def _version(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, tuple):
        return ".".join(str(part) for part in value)
    return str(value)


def _flag_names(value: Any) -> list[str]:
    if value is None:
        return []
    enum_type = type(value)
    names: list[str] = []
    try:
        for candidate in enum_type:
            candidate_value = getattr(candidate, "value", 0)
            if candidate_value and (value & candidate) == candidate:
                names.append(candidate.name)
    except (TypeError, ValueError, AttributeError):
        rendered = str(value).strip()
        return [rendered] if rendered else []
    return names


def _token_payload(slot: Any, token_not_present: tuple[type[BaseException], ...]) -> tuple[dict[str, Any] | None, str]:
    try:
        token = slot.get_token()
    except token_not_present:
        return None, ""
    except Exception as exc:  # Vendor modules may return implementation-specific failures.
        return None, f"Token inspection failed: {type(exc).__name__}: {exc}"

    flags = _flag_names(getattr(token, "flags", None))
    return (
        {
            "label": _text(getattr(token, "label", "")),
            "manufacturer": _text(getattr(token, "manufacturer_id", "")),
            "model": _text(getattr(token, "model", "")),
            "serial": _text(getattr(token, "serial", "")),
            "initialized": "TOKEN_INITIALIZED" in flags,
            "login_required": "LOGIN_REQUIRED" in flags,
            "user_pin_initialized": "USER_PIN_INITIALIZED" in flags,
            "write_protected": "WRITE_PROTECTED" in flags,
            "flags": flags,
        },
        "",
    )


def collect_snapshot(module_path: Path) -> dict[str, Any]:
    import pkcs11
    from pkcs11 import exceptions

    library = pkcs11.lib(str(module_path))
    token_not_present = tuple(
        item
        for item in (
            getattr(exceptions, "TokenNotPresent", None),
            getattr(exceptions, "TokenNotRecognised", None),
        )
        if isinstance(item, type) and issubclass(item, BaseException)
    )

    slots: list[dict[str, Any]] = []
    for slot in library.get_slots(token_present=False):
        slot_flags = _flag_names(getattr(slot, "flags", None))
        token, diagnostic = _token_payload(slot, token_not_present)
        slots.append(
            {
                "slot_id": int(slot.slot_id),
                "description": _text(getattr(slot, "slot_description", "")),
                "manufacturer": _text(getattr(slot, "manufacturer_id", "")),
                "hardware_version": _version(getattr(slot, "hardware_version", None)),
                "firmware_version": _version(getattr(slot, "firmware_version", None)),
                "token_present": token is not None or "TOKEN_PRESENT" in slot_flags,
                "token": token,
                "flags": slot_flags,
                "diagnostic": diagnostic,
            }
        )

    version = _version(getattr(library, "library_version", None))
    description = _text(getattr(library, "library_description", ""))
    manufacturer = _text(getattr(library, "manufacturer_id", ""))
    return {
        "provider": {
            "name": description or module_path.name,
            "kind": "pkcs11",
            "description": description,
            "manufacturer": manufacturer,
            "version": version,
            "module_path": str(module_path),
        },
        "slots": slots,
    }


def _write_response(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Isolated SoftHSM Studio PKCS#11 worker")
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    module_path = Path(args.module).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    try:
        data = collect_snapshot(module_path)
        _write_response(output_path, {"ok": True, "data": data})
        return 0
    except BaseException as exc:
        # Catch BaseException in the isolated child so SystemExit and vendor binding
        # errors can still be converted to a structured response when possible.
        _write_response(
            output_path,
            {
                "ok": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=8),
                },
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
