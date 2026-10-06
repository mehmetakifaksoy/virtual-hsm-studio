"""Reusable cards for the POC console."""
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class ActionCard(QFrame):
    def __init__(self, eyebrow: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionCard")
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(24, 22, 24, 22)
        self.content.setSpacing(14)
        kicker = QLabel(eyebrow)
        kicker.setObjectName("Eyebrow")
        heading = self.heading = QLabel(title)
        heading.setObjectName("CardTitle")
        heading.setWordWrap(True)
        body = self.description = QLabel(description)
        body.setObjectName("Muted")
        body.setWordWrap(True)
        self.content.addWidget(kicker)
        self.content.addWidget(heading)
        self.content.addWidget(body)
