from softhsm_studio.domain.cloud import ExternalByokClient, WrappedKeyMaterial
from softhsm_studio.domain.sovereignty import KeyReference

from .audit import Operation, SafeAudit


class CloudWorkflowError(Exception):
    pass


class ExternalByokWorkflow:
    def __init__(self, client: ExternalByokClient, audit: SafeAudit):
        self.client, self.audit = client, audit

    def _call(self, operation, action, key_id="external"):
        reference = KeyReference("cloud", 0, "external", key_id)
        try:
            result = action()
        except Exception:
            self.audit.record(operation, reference, False)
            raise CloudWorkflowError("External BYOK operation failed") from None
        self.audit.record(operation, reference, True)
        return result

    def create_external_key(self):
        return self._call(Operation.CREATE_EXTERNAL, self.client.create_external_key)

    def get_import_parameters(self, key_id):
        return self._call(
            Operation.IMPORT_PARAMETERS, lambda: self.client.get_import_parameters(key_id), key_id
        )

    def import_wrapped_key_material(self, material: WrappedKeyMaterial):
        return self._call(
            Operation.IMPORT,
            lambda: self.client.import_wrapped_key_material(material),
            material.key_id,
        )

    def status(self, key_id):
        return self._call(Operation.STATUS, lambda: self.client.status(key_id), key_id)
