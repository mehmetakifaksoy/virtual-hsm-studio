"""Local protection use cases. No cloud or upload dependency exists here."""

from softhsm_studio.domain.sovereignty import (
    EnvelopeMetadata,
    EnvelopePackage,
    KeyReference,
    KeyWrappingCapability,
    LocalCipher,
)

from .audit import Operation, SafeAudit


class ProtectionError(Exception):
    """Safe public error with no provider messages or sensitive payloads."""


class ProtectBeforeCloud:
    def __init__(self, cipher: LocalCipher, wrapper: KeyWrappingCapability, audit: SafeAudit):
        self.cipher, self.wrapper, self.audit = cipher, wrapper, audit

    def encrypt(self, data: bytes, reference: KeyReference) -> EnvelopePackage:
        try:
            if not self.wrapper.supports(reference):
                raise ProtectionError("Key wrapping capability unavailable")
            dek = self.cipher.generate_dek()
            if len(dek) != 32:
                raise ProtectionError("Expected a 256-bit DEK")
            metadata = EnvelopeMetadata(
                reference,
                self.wrapper.mode,
                self.cipher.nonce(),
                self.wrapper.wrap(reference, dek),
            )
            sealed = self.cipher.encrypt(dek, metadata.nonce, data, metadata.authenticated_header())
            package = EnvelopePackage(metadata, sealed[:-16], sealed[-16:])
        except Exception:
            self.audit.record(Operation.ENCRYPT, reference, False)
            raise ProtectionError("Local encryption failed; check wrapping capability") from None
        self.audit.record(Operation.ENCRYPT, reference, True)
        return package

    def decrypt(self, package: EnvelopePackage) -> bytes:
        metadata = package.metadata
        try:
            if self.wrapper.mode != metadata.wrapping_mode or not self.wrapper.supports(
                metadata.key_reference
            ):
                raise ProtectionError("Key wrapping capability unavailable")
            dek = self.wrapper.unwrap(metadata.key_reference, metadata.wrapped_dek)
            if len(dek) != 32:
                raise ProtectionError("Expected a 256-bit DEK")
            data = self.cipher.decrypt(
                dek,
                metadata.nonce,
                package.ciphertext + package.tag,
                metadata.authenticated_header(),
            )
        except Exception:
            self.audit.record(Operation.DECRYPT, metadata.key_reference, False)
            raise ProtectionError("Package authentication or key resolution failed") from None
        self.audit.record(Operation.DECRYPT, metadata.key_reference, True)
        return data
