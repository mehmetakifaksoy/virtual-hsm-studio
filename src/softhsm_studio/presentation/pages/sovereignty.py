from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class KeySovereigntyPage(QWidget):
    encrypt_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel("Key Sovereignty · Protect Before Cloud")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        self.notice = QLabel(
            "Plaintext never uploaded. Encryption runs locally.\n"
            "POC: virtual wrapping uses a process-memory KEK, not a hardware HSM key. "
            "Packages are recoverable only during this application session. "
            "Do not use for important data. Maximum file size: 16 MiB."
        )
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        form = QFormLayout()
        self.source = QLineEdit()
        self.source.setReadOnly(True)
        self.choose_button = QPushButton("Select source file")
        self.choose_button.clicked.connect(self.choose_file)
        self.provider = QComboBox()
        self.slot = QComboBox()
        self.master = QComboBox()
        self.master.addItem("Virtual session KEK · mock", "poc-session-kek")
        form.addRow("Source file", self.source)
        form.addRow("", self.choose_button)
        form.addRow("Provider", self.provider)
        form.addRow("Slot / Token", self.slot)
        form.addRow("Master key reference", self.master)
        layout.addLayout(form)
        self.encrypt_button = QPushButton("Encrypt Locally")
        self.encrypt_button.setObjectName("PrimaryButton")
        self.encrypt_button.clicked.connect(self.encrypt_requested)
        layout.addWidget(self.encrypt_button)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result, 1)

    def choose_file(self):
        value, _ = QFileDialog.getOpenFileName(self, "Select local source file")
        if value:
            self.source.setText(str(Path(value)))

    def set_context(self, provider_info, slots, supported, busy=False):
        self.provider.clear()
        self.provider.addItem(provider_info.name, provider_info.kind.value)
        previous = self.slot.currentData()
        self.slot.clear()
        for slot in slots:
            if slot.token and slot.token.initialized:
                self.slot.addItem(
                    f"Slot {slot.slot_id} · {slot.token.label}",
                    (slot.slot_id, slot.token.serial),
                )
        index = self.slot.findData(previous)
        if index >= 0:
            self.slot.setCurrentIndex(index)
        self.encrypt_button.setEnabled(supported and self.slot.count() > 0 and not busy)
        self.master.setEnabled(supported)
        if not supported:
            self.result.setPlainText(
                "No wrapping capability available. Connect Virtual HSM for mock POC."
            )
        elif self.result.toPlainText().startswith("No wrapping capability"):
            self.result.setPlainText(
                "Ready for local protection with an initialized virtual token."
            )
