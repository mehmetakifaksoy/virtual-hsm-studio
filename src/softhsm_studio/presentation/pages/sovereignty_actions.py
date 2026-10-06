from pathlib import Path
from uuid import uuid4

from softhsm_studio.domain.models import ProviderKind
from softhsm_studio.domain.sovereignty import KeyReference
from softhsm_studio.infrastructure.envelope_store import protect_file


class SovereigntyActions:
    def _refresh_protection_context(self):
        self.sovereignty_page.set_context(
            self.service.provider_info,
            self.slots,
            self.service.provider_info.kind is ProviderKind.VIRTUAL,
            self._busy,
        )

    def _encrypt_locally(self):
        page = self.sovereignty_page
        selection = page.slot.currentData()
        if not page.source.text() or not selection:
            page.result.setPlainText("Select a source file and initialized virtual token.")
            return
        try:
            if self.service.provider_info.kind is not ProviderKind.VIRTUAL:
                raise ValueError("No wrapping capability")
            slot_id, serial = selection
            # Revalidate against current provider, avoiding stale token selections.
            slot = next(s for s in self.service.slots() if s.slot_id == slot_id)
            if not slot.token or not slot.token.initialized or slot.token.serial != serial:
                raise ValueError("Token changed")
            reference = KeyReference("virtual", slot_id, serial, page.master.currentData())
            self.key_wrapper.provision(reference)
            source = Path(page.source.text())
            output = source.with_name(f"{source.name}.{uuid4().hex[:12]}.vhspkg")
            package = protect_file(self.protection, source, output, reference)
        except Exception:
            # Never display provider exception text or source data.
            page.result.setPlainText(
                "Encryption failed. Check source access, 16 MiB limit, output directory and token."
            )
            return
        page.result.setPlainText(
            f"Output package: {output}\nAlgorithm: {package.metadata.algorithm}\n"
            f"Version: {package.metadata.version}\nProvider: {reference.provider}\n"
            f"Slot: {reference.slot}\nToken reference: {reference.token}\n"
            f"Master reference: {reference.key_id}\nNonce: {package.metadata.nonce.hex()}\n"
            f"Tag: {package.tag.hex()}\nWrapped DEK: {len(package.metadata.wrapped_dek)} bytes\n"
            "Wrapping: VIRTUAL / MOCK · process-memory KEK\nPlaintext never uploaded."
        )
        self.audit_page.refresh()

    def _cloud_create(self):
        page = self.cloud_page
        try:
            metadata = self.cloud_workflow.create_external_key()
        except Exception:
            page.result.setPlainText("Mock BYOK operation failed.")
            return
        page.key_id = metadata.key_id
        page.parameters_button.setEnabled(True)
        page.status_button.setEnabled(True)
        page.result.setPlainText(f"OFFLINE MOCK\nKey: {metadata.key_id}\nStatus: {metadata.status}")
        self.audit_page.refresh()

    def _cloud_parameters(self):
        page = self.cloud_page
        try:
            parameters = self.cloud_workflow.get_import_parameters(page.key_id)
        except Exception:
            page.result.setPlainText("Mock BYOK operation failed.")
            return
        page.result.setPlainText(
            f"OFFLINE MOCK\nKey: {parameters.key_id}\n"
            f"Wrapping: {parameters.wrapping_algorithm}\n"
            f"Expires: {parameters.expires_at.isoformat()}\n"
            "Import token and key material are not displayed or logged."
        )
        self.audit_page.refresh()

    def _cloud_status(self):
        page = self.cloud_page
        try:
            metadata = self.cloud_workflow.status(page.key_id)
        except Exception:
            page.result.setPlainText("Mock BYOK operation failed.")
            return
        page.result.setPlainText(f"OFFLINE MOCK\nKey: {metadata.key_id}\nStatus: {metadata.status}")
        self.audit_page.refresh()
