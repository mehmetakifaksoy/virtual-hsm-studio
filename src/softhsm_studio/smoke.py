"""Non-destructive smoke check for the actual installed GUI binary."""
import tempfile
import json
import os
from pathlib import Path

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
            stage = "close-session"
            window.sessions_page.table.selectRow(0)
            window.sessions_page.close_button.click()
            assert not window.service.sessions()
            stage = "close-window"
            window.close()
        app.exit(0)
    except Exception as exc:
        report = os.environ.get("SOFTHSM_STUDIO_SMOKE_REPORT")
        if report:
            Path(report).write_text(json.dumps({"stage": stage, "error_type": type(exc).__name__}), encoding="utf-8")
        window.close()
        app.exit(1)
