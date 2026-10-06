from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class CloudIntegrationPage(QWidget):
    create_requested = Signal()
    parameters_requested = Signal()
    status_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel("Cloud Integration · Huawei External BYOK")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        notice = QLabel(
            "OFFLINE MOCK · No credentials or network requests. No file upload.\n"
            "External BYOK imports customer key material into cloud KMS. "
            "It is a separate mode from local key sovereignty; "
            "it does not keep the key outside KMS.\n"
            "Wrapped-material import is available through the tested adapter contract. "
            "Live KMS and GUI import are not implemented."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        self.key_id = None
        self.create_button = QPushButton("Create mock external key metadata")
        self.parameters_button = QPushButton("Get mock import parameters")
        self.status_button = QPushButton("Check mock status")
        for button, signal in (
            (self.create_button, self.create_requested),
            (self.parameters_button, self.parameters_requested),
            (self.status_button, self.status_requested),
        ):
            button.clicked.connect(signal)
            layout.addWidget(button)
        self.parameters_button.setEnabled(False)
        self.status_button.setEnabled(False)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result, 1)
