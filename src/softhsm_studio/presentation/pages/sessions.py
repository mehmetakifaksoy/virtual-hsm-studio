from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from softhsm_studio.domain.models import SessionInfo, SlotInfo


class SessionsPage(QWidget):
    refresh_requested = Signal()
    open_session_requested = Signal(int, bool)
    close_session_requested = Signal(int)
    login_requested = Signal(int, str, str)
    logout_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sessions: list[SessionInfo] = []
        self._supported = False
        self._busy = False
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("Sessions")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        self.message = QLabel("Connect a provider that supports PKCS#11 sessions.")
        self.message.setObjectName("Muted")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)

        controls = QHBoxLayout()
        self.slot_selector = QComboBox()
        self.slot_selector.setMinimumWidth(220)
        self.read_write = QCheckBox("Read / write")
        self.read_write.setChecked(True)
        self.open_button = QPushButton("Open Session")
        self.open_button.setObjectName("PrimaryButton")
        self.open_button.clicked.connect(self._open_selected_slot)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.close_button = QPushButton("Close Session")
        self.close_button.clicked.connect(self._close_selected_session)
        self.login_button = QPushButton("Login…")
        self.login_button.clicked.connect(self._login_selected_session)
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self._logout_selected_session)
        for widget in (
            self.slot_selector,
            self.read_write,
            self.open_button,
            self.refresh_button,
            self.login_button,
            self.logout_button,
            self.close_button,
        ):
            controls.addWidget(widget)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Session ID", "Slot ID", "Access", "Role", "State", "Opened"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._update_actions)
        layout.addWidget(self.table, 1)

    @property
    def selected_session(self) -> SessionInfo | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return self._sessions[row] if 0 <= row < len(self._sessions) else None

    def set_data(
        self,
        slots: list[SlotInfo],
        sessions: list[SessionInfo],
        supported: bool,
        busy: bool = False,
    ) -> None:
        previous_slot = self.slot_selector.currentData()
        selected_session = self.selected_session
        selected_session_id = selected_session.session_id if selected_session is not None else None
        self.slot_selector.blockSignals(True)
        self.slot_selector.clear()
        available_slots = [
            slot for slot in slots if slot.token is not None and slot.token.initialized
        ]
        for slot in available_slots:
            self.slot_selector.addItem(
                f"{slot.description or 'Slot'} · {slot.slot_id}",
                slot.slot_id,
            )
        selected_index = self.slot_selector.findData(previous_slot)
        if selected_index >= 0:
            self.slot_selector.setCurrentIndex(selected_index)
        self.slot_selector.blockSignals(False)

        self._sessions = list(sessions)
        self.table.setRowCount(len(self._sessions))
        for row, session in enumerate(self._sessions):
            values = (
                str(session.session_id),
                str(session.slot_id),
                "Read / write" if session.read_write else "Read only",
                session.role.value.upper(),
                session.state.value.replace("_", " ").title(),
                session.opened_at,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, session.session_id)
                if column < 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        selected_row = next(
            (
                index
                for index, session in enumerate(self._sessions)
                if session.session_id == selected_session_id
            ),
            -1,
        )
        if selected_row >= 0:
            self.table.selectRow(selected_row)
        self.table.resizeColumnsToContents()
        self.message.setText(
            f"{len(sessions)} active session{'s' if len(sessions) != 1 else ''}."
            if supported
            else "The active provider does not support session management."
        )
        self.set_busy(busy, supported)
        self._update_actions()

    def set_busy(self, busy: bool, supported: bool) -> None:
        self._busy = busy
        self._supported = supported
        self.open_button.setEnabled(supported and not busy and self.slot_selector.count() > 0)
        self.refresh_button.setEnabled(supported and not busy)
        self.slot_selector.setEnabled(supported and not busy)
        self.read_write.setEnabled(supported and not busy)
        self._update_actions()

    def _open_selected_slot(self) -> None:
        slot_id = self.slot_selector.currentData()
        if slot_id is not None:
            self.open_session_requested.emit(int(slot_id), self.read_write.isChecked())

    def _close_selected_session(self) -> None:
        session = self.selected_session
        if session is not None:
            self.close_session_requested.emit(session.session_id)

    def _login_selected_session(self) -> None:
        session = self.selected_session
        if session is None:
            return
        role, accepted = QInputDialog.getItem(
            self, "Session Login", "Role", ["USER", "SO"], 0, False
        )
        if not accepted:
            return
        pin, accepted = QInputDialog.getText(
            self,
            "Session Login",
            f"{role} PIN",
            QLineEdit.EchoMode.Password,
        )
        if accepted:
            self.login_requested.emit(session.session_id, role, pin)

    def _logout_selected_session(self) -> None:
        session = self.selected_session
        if session is not None:
            self.logout_requested.emit(session.session_id)

    def _update_actions(self) -> None:
        session = self.selected_session
        available = self._supported and not self._busy
        self.close_button.setEnabled(available and session is not None)
        self.login_button.setEnabled(
            available and session is not None and not session.authenticated
        )
        self.logout_button.setEnabled(available and session is not None and session.authenticated)
