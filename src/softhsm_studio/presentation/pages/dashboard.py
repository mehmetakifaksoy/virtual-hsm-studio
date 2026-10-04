from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from softhsm_studio.domain.models import ProviderInfo, SessionInfo, SlotInfo


class DashboardPage(QWidget):
    navigate_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        heading = QLabel("Dashboard")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)

        self.summary = QLabel("Connect an HSM provider to see its status.")
        self.summary.setObjectName("Muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        cards = QGridLayout()
        cards.setSpacing(12)
        self.provider_value = self._card(cards, 0, "PROVIDER", "Not connected")
        self.slots_value = self._card(cards, 1, "SLOTS", "0")
        self.tokens_value = self._card(cards, 2, "INITIALIZED TOKENS", "0")
        self.sessions_value = self._card(cards, 3, "ACTIVE SESSIONS", "0")
        layout.addLayout(cards)

        self.activity = QLabel("No recent activity.")
        self.activity.setObjectName("Feedback")
        self.activity.setWordWrap(True)
        layout.addWidget(self.activity)
        for page_index, text in ((1, "Connect or change provider"),
                                 (2, "Inspect slots and tokens"),
                                 (3, "Manage sessions")):
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, index=page_index: self.navigate_requested.emit(index))
            layout.addWidget(button)
        layout.addStretch(1)

    @staticmethod
    def _card(grid: QGridLayout, column: int, title: str, value: str) -> QLabel:
        frame = QFrame()
        frame.setObjectName("MetricCard")
        card_layout = QVBoxLayout(frame)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        label.setWordWrap(True)
        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        value_label.setWordWrap(True)
        card_layout.addWidget(label)
        card_layout.addWidget(value_label)
        grid.addWidget(frame, 0, column)
        return value_label

    def set_state(
        self,
        provider: ProviderInfo,
        connected: bool,
        slots: list[SlotInfo],
        sessions: list[SessionInfo],
        sessions_supported: bool,
        status: str,
    ) -> None:
        self.provider_value.setText(provider.name if connected else "Not connected")
        self.slots_value.setText(str(len(slots)))
        self.tokens_value.setText(
            str(sum(slot.token is not None and slot.token.initialized for slot in slots))
        )
        self.sessions_value.setText(str(len(sessions)) if sessions_supported else "Not supported")
        self.summary.setText(
            f"{provider.name} · {provider.manufacturer or provider.kind.value} · "
            f"{provider.version or 'Version unavailable'}"
            if connected
            else "Connect a PKCS#11 module or the development Virtual HSM to begin."
        )
        if status:
            self.activity.setText(status)

    def set_status(self, status: str) -> None:
        self.activity.setText(status)
