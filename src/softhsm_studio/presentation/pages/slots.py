from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QGroupBox,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from softhsm_studio.domain.models import SlotInfo


class SlotsPage(QWidget):
    slot_selected = Signal(object)
    create_slot_requested = Signal()
    initialize_token_requested = Signal()
    clear_token_requested = Signal()
    delete_slot_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._slots: list[SlotInfo] = []
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel("Slots & Tokens")
        heading.setObjectName("PageTitle")
        header.addWidget(heading)
        header.addStretch(1)
        self.slot_count = QLabel("0 slots")
        self.slot_count.setObjectName("Muted")
        header.addWidget(self.slot_count)
        layout.addLayout(header)

        actions = QHBoxLayout()
        self.create_button = self._button(
            "Add Demo Slot", self.create_slot_requested, "PrimaryButton"
        )
        self.initialize_button = self._button("Initialize Token", self.initialize_token_requested)
        self.clear_button = self._button("Remove Demo Token", self.clear_token_requested)
        self.delete_button = self._button("Delete Demo Slot", self.delete_slot_requested, "DangerButton")
        actions.addWidget(self.initialize_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.demo_admin = QGroupBox("Demo only · Virtual slot administration")
        demo_layout = QHBoxLayout(self.demo_admin)
        for button in (self.create_button, self.clear_button, self.delete_button):
            demo_layout.addWidget(button)
        demo_layout.addStretch(1)
        self.advanced_button = QPushButton("Advanced demo controls")
        self.advanced_button.setCheckable(True)
        self.advanced_button.toggled.connect(self.demo_admin.setVisible)
        layout.addWidget(self.advanced_button)
        layout.addWidget(self.demo_admin)
        self.demo_admin.hide()

        self.guidance = QLabel("Select a slot to inspect its token. Create, clear and delete are Virtual HSM operations.")
        self.guidance.setObjectName("Muted")
        self.guidance.setWordWrap(True)
        layout.addWidget(self.guidance)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Slot ID", "Description", "Token", "State"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        splitter.addWidget(self.table)

        self.details_button = QPushButton("Show technical details")
        self.details_button.setCheckable(True)
        layout.addWidget(self.details_button)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(False)
        self.details.setMinimumWidth(280)
        splitter.addWidget(self.details)
        self.details.hide()
        self.details_button.toggled.connect(self.details.setVisible)
        splitter.setSizes([620, 400])
        layout.addWidget(splitter, 1)

    def set_provider_mode(self, virtual: bool, connected: bool, initialization: bool) -> None:
        self.advanced_button.setVisible(connected and virtual)
        self.demo_admin.setVisible(connected and virtual and self.advanced_button.isChecked())
        self.initialize_button.setVisible(connected and (virtual or initialization))
        self.initialize_button.setText("Prepare Demo Token" if virtual else "Initialize Token")
        self.guidance.setText(
            "Demo mode. Select a slot and prepare its token with a name and PINs."
            if connected and virtual else
            "Connected HSM. Select a slot to view its token. "
            + ("Token initialization is available." if initialization else
               "Token setup is not implemented here; use your vendor administration tool.")
            if connected else
            "Start a demo or connect an HSM from the Home screen."
        )

    @staticmethod
    def _button(text: str, signal, object_name: str = "") -> QPushButton:
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.clicked.connect(signal)
        return button

    @property
    def selected_slot(self) -> SlotInfo | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return self._slots[row] if 0 <= row < len(self._slots) else None

    def set_slots(self, slots: list[SlotInfo], selected_id: int | None = None) -> None:
        if selected_id is None and self.selected_slot is not None:
            selected_id = self.selected_slot.slot_id
        self._slots = list(slots)
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._slots))
        for row, slot in enumerate(self._slots):
            token_label = slot.token.label if slot.token else "—"
            values = (
                str(slot.slot_id),
                slot.description or "—",
                token_label or "—",
                slot.state.replace("_", " ").title(),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, slot.slot_id)
                if column in (0, 3):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.slot_count.setText(f"{len(slots)} slot{'s' if len(slots) != 1 else ''}")
        if self._slots:
            row = next(
                (index for index, slot in enumerate(self._slots) if slot.slot_id == selected_id),
                0,
            )
            self.table.selectRow(row)
        else:
            self._show_slot(None)
            self.slot_selected.emit(None)
        self._selection_changed()

    def set_busy(self, busy: bool) -> None:
        for button in (
            self.create_button,
            self.initialize_button,
            self.clear_button,
            self.delete_button,
        ):
            button.setEnabled(not busy and button.isEnabled())

    def set_action_availability(
        self,
        *,
        can_create: bool,
        can_initialize: bool,
        can_clear: bool,
        can_delete: bool,
    ) -> None:
        self.create_button.setEnabled(can_create)
        self.initialize_button.setEnabled(can_initialize)
        self.clear_button.setEnabled(can_clear)
        self.delete_button.setEnabled(can_delete)

    def _selection_changed(self) -> None:
        selected = self.selected_slot
        self._show_slot(selected)
        self.slot_selected.emit(selected)

    def _show_slot(self, slot: SlotInfo | None) -> None:
        if slot is None:
            self.details.setHtml(
                "<h2>No slot selected</h2><p>Connect a provider to inspect its slots.</p>"
            )
            return
        slot_flags = ", ".join(slot.flags) or "—"
        diagnostic = (
            f"<p><b>Diagnostic:</b> {escape(slot.diagnostic)}</p>" if slot.diagnostic else ""
        )
        token_html = "<p><i>No token present.</i></p>"
        if slot.token is not None:
            token = slot.token
            token_flags = ", ".join(token.flags) or "—"
            login_required = "Yes" if token.login_required else "No"
            user_pin_initialized = "Yes" if token.user_pin_initialized else "No"
            write_protected = "Yes" if token.write_protected else "No"
            token_html = f"""
            <h3>Token</h3>
            <table cellspacing='5'>
              <tr><td><b>Label</b></td><td>{escape(token.label)}</td></tr>
              <tr><td><b>Serial</b></td><td>{escape(token.serial)}</td></tr>
              <tr><td><b>Model</b></td><td>{escape(token.model)}</td></tr>
              <tr><td><b>Manufacturer</b></td><td>{escape(token.manufacturer)}</td></tr>
              <tr><td><b>Initialized</b></td><td>{"Yes" if token.initialized else "No"}</td></tr>
              <tr><td><b>Login required</b></td><td>{login_required}</td></tr>
              <tr><td><b>User PIN initialized</b></td><td>{user_pin_initialized}</td></tr>
              <tr><td><b>Write protected</b></td><td>{write_protected}</td></tr>
              <tr><td><b>Flags</b></td><td>{escape(token_flags)}</td></tr>
            </table>
            """
        self.details.setHtml(
            f"""
            <h2>{escape(slot.description or "Slot")} · {slot.slot_id}</h2>
            <table cellspacing='5'>
              <tr><td><b>Manufacturer</b></td><td>{escape(slot.manufacturer)}</td></tr>
              <tr><td><b>Hardware</b></td><td>{escape(slot.hardware_version or "—")}</td></tr>
              <tr><td><b>Firmware</b></td><td>{escape(slot.firmware_version or "—")}</td></tr>
              <tr><td><b>Flags</b></td><td>{escape(slot_flags)}</td></tr>
              <tr><td><b>State</b></td><td>{escape(slot.state)}</td></tr>
            </table>
            {diagnostic}
            <hr>
            {token_html}
            """
        )
