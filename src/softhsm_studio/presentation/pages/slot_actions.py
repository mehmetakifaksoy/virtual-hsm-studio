"""Slot/token action handlers used by the console coordinator."""
from PySide6.QtWidgets import QDialog, QMessageBox
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from ..dialogs import CreateSlotDialog, InitializeTokenDialog
from ..key_dialog import KeyOperation, SlotKeysDialog


class SlotActions:
    def _open_slot_keys(self) -> None:
        slot = self._selected_slot()
        if self._busy or slot is None:
            return
        if slot.token is None or not slot.token.initialized:
            self._show_error("Initialize a token in this slot before managing keys.")
            return
        SlotKeysDialog(self.service, slot, self).exec()

    def _create_slot(self) -> None:
        dialog = CreateSlotDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            created = self.service.create_virtual_slot(dialog.description)
            self._reload_virtual_slots(
                f"Slot {created.slot_id} created. Initialize its token to continue.",
                created.slot_id,
            )
        except Exception as exc:
            self._show_error(str(exc))

    def _initialize_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        dialog = InitializeTokenDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        value = dialog.value
        dialog.clear_pins()
        if isinstance(self.service.provider, Pkcs11ModuleProvider):
            self._set_busy(True, "Initializing the selected token…")
            worker = KeyOperation(
                self.service,
                slot.slot_id,
                "initialize",
                self,
                label=value.label,
                so_pin=value.so_pin,
                user_pin=value.user_pin,
            )
            self._threads.add(worker)
            worker.succeeded.connect(self._token_initialized)
            worker.failed.connect(self._token_initialize_failed)
            worker.finished.connect(lambda: self._release_thread(worker))
            worker.start()
            return
        try:
            self.service.initialize_virtual_token(
                slot.slot_id,
                value.label,
                value.so_pin,
                value.user_pin,
            )
            self._reload_virtual_slots(f"Token initialized in slot {slot.slot_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _token_initialized(self, result) -> None:
        try:
            self._render_slots(self.service.refresh())
        except Exception as exc:
            self._set_busy(
                False,
                "Initialization completed, but slot refresh failed. Refresh before retrying.",
            )
            self._show_error(str(exc))
            return
        self._set_busy(False, result["message"])

    def _token_initialize_failed(self, message: str) -> None:
        self._set_busy(False, "Token initialization failed. Refresh slots before retrying.")
        self._show_error(message)

    def _clear_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        if slot.token is None:
            self._show_error("The selected slot is already empty.")
            return
        result = QMessageBox.question(
            self,
            "Clear Virtual Token",
            f"Clear the token from virtual slot {slot.slot_id}?\n\n"
            "The token and all its stored objects will be permanently removed. "
            "The slot will remain available.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.clear_virtual_token(slot.slot_id)
            self._reload_virtual_slots(f"Token cleared from slot {slot.slot_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _delete_slot(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        result = QMessageBox.question(
            self,
            "Delete Virtual Slot",
            f"Delete virtual slot {slot.slot_id} ({slot.description})?\n\n"
            "The slot, its token and any stored objects will be permanently removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_virtual_slot(slot.slot_id)
            self._reload_virtual_slots(f"Slot {slot.slot_id} deleted")
        except Exception as exc:
            self._show_error(str(exc))

    def _reload_virtual_slots(
        self,
        status: str,
        selected_id: int | None = None,
    ) -> None:
        self._render_slots(self.service.slots(), selected_id)
        self._set_status(status)

    def _update_virtual_buttons(self) -> None:
        selected = self._selected_slot()
        is_virtual_admin = self.service.supports_virtual_admin
        can_initialize = (
            selected is not None
            and (selected.token is None or not selected.token.initialized)
            and (is_virtual_admin or self.service.supports_token_initialization)
        )
        initialized = (
            selected is not None and selected.token is not None and selected.token.initialized
        )
        self.slots_page.set_action_availability(
            can_create=is_virtual_admin and not self._busy,
            can_initialize=can_initialize and not self._busy,
            can_clear=(
                is_virtual_admin
                and selected is not None
                and selected.token is not None
                and not self._busy
            ),
            can_delete=is_virtual_admin and selected is not None and not self._busy,
            can_manage_keys=initialized and self.service.supports_key_management and not self._busy,
        )
