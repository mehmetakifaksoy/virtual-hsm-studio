from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from softhsm_studio.domain.models import ProviderInfo, SessionInfo, SlotInfo
from ..widgets.cards import ActionCard


class DashboardPage(QWidget):
    navigate_requested = Signal(int)
    virtual_provider_requested = Signal()
    load_module_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._next_page = 1
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        heading = QLabel("Your HSM workspace")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        self.summary = QLabel("Explore the full workflow with Virtual HSM. No hardware required.")
        self.summary.setObjectName("Muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.welcome = ActionCard("GET STARTED", "From first slot to first session",
            "Start a local simulation, initialize a token with your own PINs, then explore USER and SO sessions.")
        self.welcome.setObjectName("WelcomeCard")
        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start Virtual HSM")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.clicked.connect(self.virtual_provider_requested)
        self.connect_button = QPushButton("Connect PKCS#11 module…")
        self.connect_button.clicked.connect(self.load_module_requested)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.connect_button)
        buttons.addStretch(1)
        self.welcome.content.addLayout(buttons)
        layout.addWidget(self.welcome)

        cards = QGridLayout()
        cards.setSpacing(12)
        self.provider_value = self._card(cards, 0, "PROVIDER", "Not connected")
        self.slots_value = self._card(cards, 1, "SLOTS", "0")
        self.tokens_value = self._card(cards, 2, "READY TOKENS", "0")
        self.sessions_value = self._card(cards, 3, "SESSIONS", "0")
        layout.addLayout(cards)

        self.next_step = ActionCard("NEXT STEP", "Choose a provider", "Your workspace is ready when you are.")
        self.step_label = QLabel("01  Connect a provider    /    02  Initialize a token    /    03  Open a session")
        self.step_label.setObjectName("Muted")
        self.step_label.setWordWrap(True)
        self.next_step.content.addWidget(self.step_label)
        self.next_button = QPushButton("View providers")
        self.next_button.clicked.connect(lambda checked=False: self.navigate_requested.emit(self._next_page))
        self.next_step.content.addWidget(self.next_button)
        layout.addWidget(self.next_step)
        self.activity = QLabel("No activity yet.")
        self.activity.setObjectName("Muted")
        self.activity.setWordWrap(True)
        layout.addWidget(self.activity)
        layout.addStretch(1)

    @staticmethod
    def _card(grid, column, title, value):
        frame = QFrame()
        frame.setObjectName("MetricCard")
        content = QVBoxLayout(frame)
        content.setContentsMargins(16, 14, 16, 14)
        label = QLabel(title)
        label.setObjectName("Eyebrow")
        label.setWordWrap(True)
        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        value_label.setWordWrap(True)
        content.addWidget(label)
        content.addWidget(value_label)
        grid.addWidget(frame, 0, column)
        return value_label

    def set_state(self, provider: ProviderInfo, connected: bool, slots: list[SlotInfo],
                  sessions: list[SessionInfo], sessions_supported: bool, status: str):
        self._connected = connected
        ready = sum(slot.token is not None and slot.token.initialized for slot in slots)
        self.provider_value.setText(provider.name if connected else "—")
        self.slots_value.setText(str(len(slots)))
        self.tokens_value.setText(str(ready))
        self.sessions_value.setText(str(len(sessions)) if sessions_supported else "—")
        self.welcome.setVisible(not connected)
        self.summary.setText(
            f"Connected to {provider.name}. Your token and session overview is below."
            if connected else "Explore the full workflow with Virtual HSM. No hardware required."
        )
        if not connected:
            self._next_page, text = 1, "Choose your provider"
        elif not ready:
            self._next_page, text = 2, "Initialize your first token"
        elif sessions_supported:
            self._next_page, text = 3, "Manage sessions" if sessions else "Open your first session"
        else:
            self._next_page, text = 2, "Inspect tokens and manage keys"
        self.next_button.setText(text)
        self.next_step.heading.setText(text)
        self.next_step.description.setText("Continue the POC workflow. Your local Virtual HSM state is saved automatically." if provider.kind.value == "virtual" and connected else "Only operations supported by the selected provider are available.")
        self.step_label.setText(
            "01  Provider connected    /    02  Token ready    /    03  Explore sessions"
            if connected and ready else
            "01  Provider connected    /    02  Initialize a token    /    03  Open a session"
            if connected else
            "01  Connect a provider    /    02  Initialize a token    /    03  Open a session"
        )
        self.activity.setText(status)

    def set_busy(self, busy):
        self.start_button.setEnabled(not busy)
        self.connect_button.setEnabled(not busy)
        self.next_button.setEnabled(not busy)

    def set_status(self, status):
        self.activity.setText(status)
