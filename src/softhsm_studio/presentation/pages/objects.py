from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from softhsm_studio.domain.models import ObjectClass, ObjectInfo, SessionInfo


class ObjectsPage(QWidget):
    refresh_requested = Signal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._objects: list[ObjectInfo] = []
        self._supported = False
        self._busy = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("Object Explorer")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)

        self.message = QLabel("Select an active session to inspect its visible object metadata.")
        self.message.setObjectName("Muted")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)

        controls = QHBoxLayout()
        self.session_selector = QComboBox()
        self.session_selector.setMinimumWidth(240)
        self.class_selector = QComboBox()
        self.class_selector.setMinimumWidth(180)
        self.class_selector.addItem("All object classes", None)
        for object_class in ObjectClass:
            self.class_selector.addItem(
                object_class.value.replace("_", " ").title(),
                object_class,
            )
        self.refresh_button = QPushButton("Load Objects")
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self._request_refresh)
        controls.addWidget(QLabel("Session"))
        controls.addWidget(self.session_selector)
        controls.addWidget(QLabel("Class"))
        controls.addWidget(self.class_selector)
        controls.addWidget(self.refresh_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Label", "Class", "Key Type", "CKA_ID", "Private", "Sensitive", "Extractable"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.details = QLabel("Object values and key material are never displayed by this screen.")
        self.details.setObjectName("Feedback")
        self.details.setWordWrap(True)
        layout.addWidget(self.details)

    @property
    def selected_session_id(self) -> int | None:
        value = self.session_selector.currentData()
        return int(value) if value is not None else None

    def set_sessions(
        self,
        sessions: list[SessionInfo],
        supported: bool,
        busy: bool = False,
    ) -> None:
        previous_session = self.selected_session_id
        self.session_selector.blockSignals(True)
        self.session_selector.clear()
        for session in sessions:
            self.session_selector.addItem(
                f"Session {session.session_id} · Slot {session.slot_id} · "
                f"{session.role.value.upper()}",
                session.session_id,
            )
        selected_index = self.session_selector.findData(previous_session)
        if selected_index >= 0:
            self.session_selector.setCurrentIndex(selected_index)
        self.session_selector.blockSignals(False)

        self._supported = supported
        self._busy = busy
        self.refresh_button.setEnabled(supported and not busy and self.session_selector.count() > 0)
        self.session_selector.setEnabled(supported and not busy)
        self.class_selector.setEnabled(supported and not busy)
        if not supported:
            self.set_objects([], "The active provider does not support object discovery.")
        elif not sessions:
            self.set_objects([], "Open a session in Sessions to browse its objects.")
        else:
            self.set_objects([], "Select a session and load its object metadata.")

    def set_objects(self, objects: list[ObjectInfo], message: str | None = None) -> None:
        self._objects = list(objects)
        self.table.setRowCount(len(self._objects))
        for row, item in enumerate(self._objects):
            values = (
                item.label or "—",
                item.object_class.value.replace("_", " ").title(),
                item.key_type or "—",
                item.cka_id or "—",
                "Yes" if item.private else "No",
                "Yes" if item.sensitive else "No",
                "Yes" if item.extractable else "No",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column > 2:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, cell)
        self.table.resizeColumnsToContents()
        if message is None:
            message = (
                f"{len(objects)} object(s) visible. Private object visibility depends "
                "on the session's login state."
                if objects
                else "No objects are visible in this session."
            )
        self.message.setText(message)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.refresh_button.setEnabled(
            self._supported and not busy and self.session_selector.count() > 0
        )
        self.session_selector.setEnabled(self._supported and not busy)
        self.class_selector.setEnabled(self._supported and not busy)

    def _request_refresh(self) -> None:
        session_id = self.selected_session_id
        if session_id is None:
            self.set_objects([], "Open a session in Sessions to browse its objects.")
            return
        self.refresh_requested.emit(session_id, self.class_selector.currentData())
