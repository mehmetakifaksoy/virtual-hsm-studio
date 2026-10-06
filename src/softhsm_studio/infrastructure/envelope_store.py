"""Versioned ciphertext-only package storage; exclusive creation prevents overwrite."""

import base64
import json
from dataclasses import asdict
from pathlib import Path

from softhsm_studio.domain.sovereignty import (
    DekMetadata,
    EnvelopeMetadata,
    EnvelopePackage,
    KeyReference,
)

MAX_DATA_BYTES = 16 * 1024 * 1024


def encode_package(package: EnvelopePackage) -> str:
    metadata = asdict(package.metadata)
    for name in ("nonce", "wrapped_dek"):
        metadata[name] = base64.b64encode(metadata[name]).decode("ascii")
    return json.dumps(
        {
            "metadata": metadata,
            "ciphertext": base64.b64encode(package.ciphertext).decode("ascii"),
            "tag": base64.b64encode(package.tag).decode("ascii"),
        },
        sort_keys=True,
    )


def decode_package(data: str) -> EnvelopePackage:
    if len(data) > MAX_DATA_BYTES * 2:
        raise ValueError("Package exceeds POC size limit")
    value = json.loads(data)
    if set(value) != {"metadata", "ciphertext", "tag"}:
        raise ValueError("Unexpected package fields")
    metadata = value["metadata"]
    metadata["key_reference"] = KeyReference(**metadata["key_reference"])
    metadata["dek"] = DekMetadata(**metadata["dek"])
    for name in ("nonce", "wrapped_dek"):
        metadata[name] = base64.b64decode(metadata[name], validate=True)
    return EnvelopePackage(
        EnvelopeMetadata(**metadata),
        base64.b64decode(value["ciphertext"], validate=True),
        base64.b64decode(value["tag"], validate=True),
    )


def protect_file(service, source: Path, output: Path, reference: KeyReference):
    # Read at most limit+1 even if the source grows after stat().
    with source.open("rb") as stream:
        data = stream.read(MAX_DATA_BYTES + 1)
    if len(data) > MAX_DATA_BYTES:
        raise ValueError("POC supports files up to 16 MiB")
    package = service.encrypt(data, reference)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(encode_package(package))
    return package
