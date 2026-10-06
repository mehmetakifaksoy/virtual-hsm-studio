"""Non-destructive smoke check for the actual installed GUI binary."""

import json
import os
import tempfile
from pathlib import Path

from .domain.models import SessionRole
from .infrastructure.envelope_store import decode_package
from .infrastructure.virtual_hsm import VirtualHsmProvider


def run_smoke(window, app):
    stage = "create-provider"
    try:
        with tempfile.TemporaryDirectory(prefix="hsm-studio-smoke-") as directory:
            provider = VirtualHsmProvider(Path(directory) / "state.json")
            provider.connect()
            stage = "activate-provider"
            window._provider_connected(provider, provider.list_slots())
            stage = "initialize-token"
            window.service.initialize_virtual_token(0, "SMOKE", "smoke-so-pin", "smoke-user-pin")
            window._render_slots(window.service.slots())
            stage = "navigation"
            for button in window.navigation:
                button.click()
                app.processEvents()
            stage = "open-session"
            window.sessions_page.open_button.click()
            assert len(window.service.sessions()) == 1
            stage = "user-so-login"
            session_id = window.service.sessions()[0].session_id
            window.service.login_user(session_id, "smoke-user-pin")
            assert window.service.sessions()[0].role is SessionRole.USER
            window.service.logout(session_id)
            window.service.close_session(session_id)
            session = window.service.open_session(0, read_write=True)
            window.service.login_so(session.session_id, "smoke-so-pin")
            assert window.service.sessions()[0].role is SessionRole.SO
            window.service.logout(session.session_id)
            window._refresh_sessions()
            stage = "close-session"
            window.sessions_page.table.selectRow(0)
            window.sessions_page.close_button.click()
            assert not window.service.sessions()
            stage = "local-protection"
            source = Path(directory) / "disposable.txt"
            source.write_bytes(b"local smoke plaintext")
            window.sovereignty_page.source.setText(str(source))
            window.sovereignty_page.encrypt_button.click()
            packages = list(Path(directory).glob("*.vhspkg"))
            assert len(packages) == 1
            package = decode_package(packages[0].read_text())
            assert window.protection.decrypt(package) == source.read_bytes()
            stage = "mock-cloud"
            window.cloud_page.create_button.click()
            window.cloud_page.parameters_button.click()
            window.cloud_page.status_button.click()
            assert "pending-import" in window.cloud_page.result.toPlainText()
            stage = "close-window"
            window.close()
        app.exit(0)
    except Exception as exc:
        report = os.environ.get("SOFTHSM_STUDIO_SMOKE_REPORT")
        if report:
            Path(report).write_text(
                json.dumps({"stage": stage, "error_type": type(exc).__name__}), encoding="utf-8"
            )
        window.close()
        app.exit(1)
