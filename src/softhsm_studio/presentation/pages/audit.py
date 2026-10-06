from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class AuditPage(QWidget):
    def __init__(self, audit):
        super().__init__()
        self.audit = audit
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Audit / Diagnostics · In-memory POC events (latest 1000)"))
        refresh = QPushButton("Refresh audit")
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result)

    def refresh(self):
        self.result.setPlainText(
            "\n".join(
                f"{e.timestamp} | {e.operation} | {e.provider} | slot {e.slot} | "
                f"{e.key_reference} | {e.result}"
                for e in self.audit.events
            )
            or "No protection or BYOK events yet."
        )
