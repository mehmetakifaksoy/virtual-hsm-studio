from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import softhsm_studio.presentation.main_window as main_window
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.presentation.workers import ProviderConnectThread


class _SettingsStub:
    def value(self, key: str, default: str = "") -> str:
        return "__skip_autoload__.dll" if key == "module" else default


def _disable_module_autoload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main_window, "settings", _SettingsStub)


def test_provider_connect_worker_closes_failed_provider() -> None:
    provider = Mock()
    provider.connect.side_effect = RuntimeError("connection failed")
    errors: list[str] = []
    worker = ProviderConnectThread(provider)
    worker.failed.connect(errors.append)

    worker.run()

    provider.close.assert_called_once_with()
    assert errors == ["connection failed"]


def test_console_navigation_has_all_management_pages(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    _disable_module_autoload(monkeypatch)
    window = main_window.MainWindow()
    try:
        assert window.page_stack.count() == 4
        assert [button.text() for button in window.navigation] == [
            "Dashboard",
            "Providers",
            "Slots",
            "Sessions",
        ]
        for index, button in enumerate(window.navigation):
            button.click()
            assert window.page_stack.currentIndex() == index
        assert "does not support session management" in window.sessions_page.message.text()
    finally:
        window.close()
        app.processEvents()


def test_sessions_page_tracks_virtual_provider_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    app = QApplication.instance() or QApplication([])
    _disable_module_autoload(monkeypatch)
    window = main_window.MainWindow()
    provider = VirtualHsmProvider(tmp_path / "state.json")
    provider.connect()
    window.service.activate_connected(provider)
    window.service.initialize_virtual_token(0, "CONSOLE_TEST", "112233", "445566")
    window._render_provider()
    window._render_slots(window.service.slots())
    try:
        assert window.sessions_page.slot_selector.count() == 1
        window.sessions_page.open_button.click()
        assert len(window.service.sessions()) == 1
        window.sessions_page.table.selectRow(0)
        assert window.sessions_page.login_button.isEnabled()
        session_id = window.sessions_page.selected_session.session_id
        window._login_session(session_id, "USER", "445566")
        assert window.sessions_page.logout_button.isEnabled()
        window.sessions_page.logout_button.click()
        assert not window.service.sessions()[0].authenticated
        window.sessions_page.close_button.click()
        assert not window.service.sessions()
    finally:
        window.close()
        app.processEvents()
