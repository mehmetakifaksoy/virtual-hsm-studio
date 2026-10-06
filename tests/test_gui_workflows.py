"""Exercise the real Qt dialogs and buttons against isolated Virtual HSM state."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QInputDialog, QMessageBox

import softhsm_studio.presentation.main_window as main_window
from softhsm_studio.domain.models import ObjectClass, SessionRole
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.presentation.dialogs import (
    CreateSlotDialog,
    InitializeTokenDialog,
    TokenInitializationInput,
)


class SettingsStub:
    def value(self, key, default=""):
        return "__skip_autoload__.dll"


def click(button):
    assert button.isEnabled()
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    QApplication.processEvents()


def modal_action(callback, errors):
    def run():
        dialog = QApplication.activeModalWidget()
        try:
            assert dialog is not None
            callback(dialog)
        except BaseException as exc:
            errors.append(exc)
            if dialog is not None:
                dialog.reject()

    QTimer.singleShot(0, run)


def accept_form(dialog):
    click(dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok))


def test_real_gui_slot_token_and_session_flows(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(main_window, "settings", SettingsStub)
    window = main_window.MainWindow()
    provider = VirtualHsmProvider(tmp_path / "state.json")
    provider.connect()
    window.service.activate_connected(provider)
    window._render_provider()
    window._render_slots(window.service.slots())
    window.show()
    errors = []
    try:
        click(window.navigation[2])
        if not window.slots_page.advanced_button.isChecked():
            click(window.slots_page.advanced_button)

        def create(dialog):
            assert isinstance(dialog, CreateSlotDialog)
            dialog.description_edit.setText("GUI smoke slot")
            accept_form(dialog)

        modal_action(create, errors)
        click(window.slots_page.create_button)
        assert not errors
        slot_id = window.slots_page.selected_slot.slot_id
        assert window.slots_page.selected_slot.description == "GUI smoke slot"

        def initialize(dialog):
            assert isinstance(dialog, InitializeTokenDialog)
            dialog.label_edit.setText("GUI_SMOKE")
            for edit in (dialog.so_pin_edit, dialog.so_pin_confirm_edit):
                edit.setText("test-so-pin")
            for edit in (dialog.user_pin_edit, dialog.user_pin_confirm_edit):
                edit.setText("test-user-pin")
            accept_form(dialog)

        modal_action(initialize, errors)
        click(window.slots_page.initialize_button)
        assert not errors
        assert window.slots_page.selected_slot.token.initialized
        assert not window.slots_page.initialize_button.isEnabled()

        click(window.navigation[3])
        page = window.sessions_page
        page.slot_selector.setCurrentIndex(page.slot_selector.findData(slot_id))
        assert not page.read_write.isChecked()
        click(page.open_button)
        page.table.selectRow(0)
        assert not page.selected_session.read_write

        def login(role, pin):
            def choose_role(dialog):
                assert isinstance(dialog, QInputDialog)
                dialog.setTextValue(role)
                dialog.accept()
                modal_action(enter_pin, errors)

            def enter_pin(dialog):
                assert isinstance(dialog, QInputDialog)
                dialog.setTextValue(pin)
                dialog.accept()

            modal_action(choose_role, errors)
            click(page.login_button)
            assert not errors

        login("USER", "test-user-pin")
        assert page.selected_session.role is SessionRole.USER
        click(page.logout_button)
        assert page.selected_session.role is SessionRole.PUBLIC
        click(page.close_button)
        assert not window.service.sessions()

        page.read_write.setChecked(True)
        click(page.open_button)
        page.table.selectRow(0)
        assert page.selected_session.read_write
        login("SO", "test-so-pin")
        assert page.selected_session.role is SessionRole.SO
        click(page.logout_button)
        click(page.close_button)
        assert not window.service.sessions()

        click(window.navigation[2])

        def confirm(dialog):
            assert isinstance(dialog, QMessageBox)
            assert dialog.defaultButton() is dialog.button(QMessageBox.StandardButton.No)
            click(dialog.button(QMessageBox.StandardButton.Yes))

        modal_action(confirm, errors)
        click(window.slots_page.clear_button)
        assert window.slots_page.selected_slot.token is None
        modal_action(confirm, errors)
        click(window.slots_page.delete_button)
        assert slot_id not in [slot.slot_id for slot in window.service.slots()]
        assert not errors
    finally:
        window.close()
        app.processEvents()


def test_pin_repr_and_cancel_do_not_retain_secrets():
    app = QApplication.instance() or QApplication([])
    value = TokenInitializationInput("label", "test-so-pin", "test-user-pin")
    assert "test-so-pin" not in repr(value)
    assert "test-user-pin" not in repr(value)
    dialog = InitializeTokenDialog()
    dialog.so_pin_edit.setText("test-so-pin")
    dialog.user_pin_edit.setText("test-user-pin")
    dialog.reject()
    assert not dialog.so_pin_edit.text()
    assert not dialog.user_pin_edit.text()
    app.processEvents()


def test_login_exception_does_not_reveal_pin(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(main_window, "settings", SettingsStub)
    window = main_window.MainWindow()
    messages = []
    monkeypatch.setattr(window, "_show_error", messages.append)

    def unsafe_provider_error(*args):
        raise RuntimeError("vendor echoed test-user-pin")

    monkeypatch.setattr(window.service, "login_user", unsafe_provider_error)
    window._login_session(1, "USER", "test-user-pin")
    assert messages and all("test-user-pin" not in message for message in messages)
    window.close()
    app.processEvents()


def test_object_explorer_filters_safe_metadata_by_session(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(main_window, "settings", SettingsStub)
    window = main_window.MainWindow()
    provider = VirtualHsmProvider(tmp_path / "objects.json")
    provider.connect()
    provider.initialize_token(0, "OBJECTS", "test-so-pin", "test-user-pin")
    session = provider.open_session(0, read_write=True)
    provider.login(session.session_id, SessionRole.USER, "test-user-pin")
    provider.simulate_key(session.session_id, "AES-256", "Explorer test key")
    window.service.activate_connected(provider)
    window._render_provider()
    window._render_slots(window.service.slots())
    try:
        click(window.navigation[4])
        page = window.objects_page
        assert page.session_selector.count() == 1
        click(page.refresh_button)
        assert page.table.rowCount() == 1
        assert page.table.item(0, 0).text() == "Explorer test key"
        assert page.table.item(0, 1).text() == "Secret Key"
        assert page.table.item(0, 5).text() == "Yes"

        page.class_selector.setCurrentIndex(page.class_selector.findData(ObjectClass.PUBLIC_KEY))
        click(page.refresh_button)
        assert page.table.rowCount() == 0
        assert "No objects are visible" in page.message.text()
        assert "test-user-pin" not in page.details.text()
    finally:
        window.close()
        app.processEvents()
