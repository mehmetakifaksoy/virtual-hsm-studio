from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from softhsm_studio.application.audit import SafeAudit
from softhsm_studio.application.cloud import CloudWorkflowError, ExternalByokWorkflow
from softhsm_studio.domain.cloud import WrappedKeyMaterial
from softhsm_studio.infrastructure.cloud.mock import MockCloudKmsAdapter


def wrapped(parameters, data=None):
    if data is None:
        data = b"customer-key-marker".ljust(32, b"!")
    assert len(data) == 32
    public = serialization.load_der_public_key(parameters.public_key)
    ciphertext = public.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return WrappedKeyMaterial(parameters.key_id, ciphertext, parameters.import_token)


def test_offline_external_byok_contract_and_no_secret_logs(caplog):
    audit = SafeAudit()
    adapter = MockCloudKmsAdapter()
    flow = ExternalByokWorkflow(adapter, audit)
    metadata = flow.create_external_key()
    assert metadata.origin == "external" and metadata.mock
    assert flow.status(metadata.key_id).status == "pending-import"
    parameters = flow.get_import_parameters(metadata.key_id)
    material = wrapped(parameters)
    assert flow.import_wrapped_key_material(material).status == "enabled"
    assert flow.status(metadata.key_id).status == "enabled"
    with pytest.raises(CloudWorkflowError):
        flow.import_wrapped_key_material(material)
    logs = repr(parameters) + repr(material) + repr(audit.events) + caplog.text
    assert parameters.import_token.hex() not in logs
    assert repr(parameters.import_token) not in logs
    assert "customer-owned-key-material" not in logs
    assert not adapter._imports  # import tokens and ephemeral RSA keys released
    assert not hasattr(adapter, "upload") and not hasattr(adapter, "encrypt")


@pytest.mark.parametrize("failure", ["raw", "wrong-token", "expired", "cross-key"])
def test_invalid_imports_are_rejected(failure):
    now = datetime.now(UTC)
    clock = [now]
    flow = ExternalByokWorkflow(MockCloudKmsAdapter(clock=lambda: clock[0]), SafeAudit())
    metadata = flow.create_external_key()
    parameters = flow.get_import_parameters(metadata.key_id)
    material = wrapped(parameters)
    if failure == "raw":
        material = replace(material, ciphertext=b"customer-owned-key-material-12345")
    elif failure == "wrong-token":
        material = replace(material, import_token=b"wrong")
    elif failure == "cross-key":
        other = flow.create_external_key()
        flow.get_import_parameters(other.key_id)
        material = replace(material, key_id=other.key_id)
    else:
        clock[0] = now + timedelta(minutes=11)
    with pytest.raises(CloudWorkflowError):
        flow.import_wrapped_key_material(material)
    assert flow.status(metadata.key_id).status == "pending-import"
    assert any(e.result == "failure" for e in flow.audit.events)
