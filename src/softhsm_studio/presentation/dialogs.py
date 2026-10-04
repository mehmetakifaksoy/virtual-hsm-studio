from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)


@dataclass(frozen=True, slots=True)
class TokenInitializationInput:
    label: str
    so_pin: str = field(repr=False)
    user_pin: str = field(repr=False)


class CreateSlotDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Virtual Slot")
        self.setMinimumWidth(430)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("e.g. Development or Signing")

        form = QFormLayout()
        form.addRow("Slot name", self.description_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create Slot")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("PrimaryButton")
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        help_text = QLabel("Give this slot a recognizable name. Initialize its token after creating it.")
        help_text.setWordWrap(True)
        help_text.setObjectName("Muted")
        layout.addWidget(help_text)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @property
    def description(self) -> str:
        return self.description_edit.text().strip()

    def _accept_if_valid(self) -> None:
        if not self.description:
            QMessageBox.warning(self, "Validation", "Slot description cannot be empty.")
            return
        self.accept()


class InitializeTokenDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Initialize Token")
        self.setMinimumWidth(470)

        self.label_edit = QLineEdit()
        self.so_pin_edit = self._password_edit("4–64 characters")
        self.so_pin_confirm_edit = self._password_edit("Repeat administrator PIN")
        self.user_pin_edit = self._password_edit("4–64 characters")
        self.user_pin_confirm_edit = self._password_edit("Repeat User PIN")

        self.label_edit.setPlaceholderText("DEV_TOKEN")

        form = QFormLayout()
        form.addRow("Token label", self.label_edit)
        form.addRow("Administrator PIN", self.so_pin_edit)
        form.addRow("Confirm administrator PIN", self.so_pin_confirm_edit)
        form.addRow("User PIN", self.user_pin_edit)
        form.addRow("Confirm User PIN", self.user_pin_confirm_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Initialize Token")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("PrimaryButton")
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        help_text = QLabel("Choose a token name and two PINs (4–64 characters). The administrator PIN manages the token; the user PIN grants access to its keys.")
        help_text.setWordWrap(True)
        help_text.setObjectName("Muted")
        layout.addWidget(help_text)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @staticmethod
    def _password_edit(placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        edit.setPlaceholderText(placeholder)
        return edit

    @property
    def value(self) -> TokenInitializationInput:
        return TokenInitializationInput(
            label=self.label_edit.text().strip(),
            so_pin=self.so_pin_edit.text(),
            user_pin=self.user_pin_edit.text(),
        )

    def clear_pins(self) -> None:
        for edit in (self.so_pin_edit, self.so_pin_confirm_edit,
                     self.user_pin_edit, self.user_pin_confirm_edit):
            edit.clear()

    def reject(self) -> None:
        self.clear_pins()
        super().reject()

    def _accept_if_valid(self) -> None:
        value = self.value
        if not value.label:
            QMessageBox.warning(self, "Validation", "Token label cannot be empty.")
            return
        if not 4 <= len(value.so_pin) <= 64 or not 4 <= len(value.user_pin) <= 64:
            QMessageBox.warning(self, "Validation", "PINs must contain 4–64 characters.")
            return
        if value.so_pin != self.so_pin_confirm_edit.text():
            QMessageBox.warning(self, "Validation", "Administrator PIN confirmation does not match.")
            return
        if value.user_pin != self.user_pin_confirm_edit.text():
            QMessageBox.warning(self, "Validation", "User PIN confirmation does not match.")
            return
        self.accept()
