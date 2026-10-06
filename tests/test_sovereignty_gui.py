import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from softhsm_studio.infrastructure.envelope_store import decode_package
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.presentation.main_window import MainWindow


def test_gui_protect_and_mock_cloud_flow(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    provider = VirtualHsmProvider(tmp_path / "state.json")
    provider.connect()
    provider.initialize_token(0, "LOCAL", "so-pin-test", "user-pin-test")
    window._provider_connected(provider, provider.list_slots())
    window.show()
    try:
        for index, button in enumerate(window.navigation):
            button.click()
            assert window.page_stack.currentIndex() == index
        window.navigation[7].click()
        page = window.sovereignty_page
        assert page.encrypt_button.isEnabled()
        assert "No wrapping capability" not in page.result.toPlainText()
        source = tmp_path / "input.txt"
        source.write_bytes(b"gui-confidential-marker")
        monkeypatch.setattr(
            "softhsm_studio.presentation.pages.sovereignty.QFileDialog.getOpenFileName",
            lambda *args: (str(source), ""),
        )
        page.choose_button.click()
        assert page.source.text() == str(source)
        page.encrypt_button.click()
        packages = list(tmp_path.glob("*.vhspkg"))
        assert len(packages) == 1
        package = decode_package(packages[0].read_text())
        assert window.protection.decrypt(package) == b"gui-confidential-marker"
        assert "Plaintext never uploaded" in page.result.toPlainText()
        assert "VIRTUAL / MOCK" in page.result.toPlainText()
        assert "gui-confidential-marker" not in page.result.toPlainText()
        window.navigation[6].click()
        cloud = window.cloud_page
        cloud.create_button.click()
        cloud.parameters_button.click()
        assert "RSAES_OAEP_SHA_256" in cloud.result.toPlainText()
        cloud.status_button.click()
        assert "pending-import" in cloud.result.toPlainText()
        window.audit_page.refresh()
        assert "encrypt-local" in window.audit_page.result.toPlainText()
        assert "user-pin-test" not in window.audit_page.result.toPlainText()
        # Remove token after selection: stale context cannot encrypt.
        provider.clear_token(0)
        page.encrypt_button.click()
        assert "failed" in page.result.toPlainText()
        assert len(list(tmp_path.glob("*.vhspkg"))) == 1
    finally:
        window.close()
        app.processEvents()


def test_gui_has_no_wrapping_when_disconnected():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert not window.sovereignty_page.encrypt_button.isEnabled()
    assert "No wrapping capability" in window.sovereignty_page.result.toPlainText()
    window.close()
    app.processEvents()
