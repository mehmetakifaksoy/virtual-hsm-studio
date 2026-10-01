from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from softhsm_studio.application import HsmService
from softhsm_studio.domain.models import ProviderKind, SlotInfo
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider

from .dialogs import CreateSlotDialog, InitializeTokenDialog
from .workers import ProviderConnectThread, ProviderRefreshThread


class MainWindow(QMainWindow):
    MODULE_SUFFIXES = {".dll", ".so", ".dylib"}

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SoftHSM Studio")
        self.resize(1320, 820)
        self.setMinimumSize(1080, 680)
        self.setAcceptDrops(True)

        self.service = HsmService(VirtualHsmProvider())
        self.slots: list[SlotInfo] = self.service.slots()
        self._threads: set[object] = set()
        self._busy = False

        self._build_ui()
        self._render_provider()
        self._render_slots(self.slots)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(270)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(10)

        title = QLabel("SoftHSM Studio")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Virtual HSM + PKCS#11 Explorer")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        self.provider_badge = QLabel()
        self.provider_badge.setObjectName("ProviderBadge")
        self.provider_badge.setWordWrap(True)

        side_layout.addWidget(title)
        side_layout.addWidget(subtitle)
        side_layout.addSpacing(6)
        side_layout.addWidget(self.provider_badge)
        side_layout.addSpacing(14)
        side_layout.addWidget(self._section_label("HSM SOURCE"))

        self.virtual_button = QPushButton("Use Virtual HSM")
        self.virtual_button.clicked.connect(self._switch_to_virtual)
        self.load_module_button = QPushButton("Load PKCS#11 Module…")
        self.load_module_button.setObjectName("PrimaryButton")
        self.load_module_button.clicked.connect(self._choose_module)
        self.refresh_button = QPushButton("Refresh Slots")
        self.refresh_button.clicked.connect(self._refresh_provider)

        side_layout.addWidget(self.virtual_button)
        side_layout.addWidget(self.load_module_button)
        side_layout.addWidget(self.refresh_button)
        side_layout.addSpacing(14)
        side_layout.addWidget(self._section_label("VIRTUAL HSM"))

        self.create_slot_button = QPushButton("Create Slot")
        self.create_slot_button.clicked.connect(self._create_slot)
        self.initialize_button = QPushButton("Initialize Token")
        self.initialize_button.clicked.connect(self._initialize_token)
        self.clear_button = QPushButton("Clear Token")
        self.clear_button.clicked.connect(self._clear_token)
        self.delete_button = QPushButton("Delete Slot")
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self._delete_slot)

        side_layout.addWidget(self.create_slot_button)
        side_layout.addWidget(self.initialize_button)
        side_layout.addWidget(self.clear_button)
        side_layout.addWidget(self.delete_button)
        side_layout.addStretch(1)

        warning = QLabel(
            "Virtual mode simulates HSM behavior for development. "
            "It is not a hardware security boundary."
        )
        warning.setObjectName("Muted")
        warning.setWordWrap(True)
        side_layout.addWidget(warning)

        content = QFrame()
        content.setObjectName("Panel")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        self.provider_title = QLabel()
        self.provider_title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        self.slot_count = QLabel()
        self.slot_count.setObjectName("Muted")
        header_layout.addWidget(self.provider_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.slot_count)
        content_layout.addLayout(header_layout)

        self.provider_detail = QLabel()
        self.provider_detail.setObjectName("Muted")
        self.provider_detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.provider_detail.setWordWrap(True)
        content_layout.addWidget(self.provider_detail)

        splitter = QSplitter(Qt.Vertical)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Slot ID", "Description", "Token", "Manufacturer", "Model", "Serial", "State"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._show_selected_slot)
        self.table.doubleClicked.connect(self._show_selected_slot)
        splitter.addWidget(self.table)

        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(False)
        splitter.addWidget(self.details)
        splitter.setSizes([470, 250])
        content_layout.addWidget(splitter, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready")

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def _choose_module(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PKCS#11 Module",
            "",
            "PKCS#11 Modules (*.dll *.so *.dylib);;All files (*)",
        )
        if path:
            self._load_module(Path(path))

    def _load_module(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._show_error(f"Module file does not exist: {path}")
            return
        provider = Pkcs11ModuleProvider(path)
        self._connect_provider_async(provider, f"Loading {path.name}…")

    def _switch_to_virtual(self) -> None:
        provider = VirtualHsmProvider()
        self._connect_provider_async(provider, "Opening Virtual HSM…")

    def _connect_provider_async(self, provider, status: str) -> None:
        self._set_busy(True, status)
        thread = ProviderConnectThread(provider, self)
        self._threads.add(thread)
        thread.succeeded.connect(self._provider_connected)
        thread.failed.connect(self._provider_connect_failed)
        thread.finished.connect(lambda: self._release_thread(thread))
        thread.start()

    def _provider_connected(self, provider, slots) -> None:
        self.service.activate_connected(provider)
        self.slots = list(slots)
        self._render_provider()
        self._render_slots(self.slots)
        self._set_busy(False, f"Loaded {len(self.slots)} slot(s)")

    def _provider_connect_failed(self, message: str) -> None:
        self._set_busy(False, "Provider load failed")
        self._show_error(message)

    def _refresh_provider(self) -> None:
        self._set_busy(True, "Refreshing slots…")
        thread = ProviderRefreshThread(self.service.provider, self)
        self._threads.add(thread)
        thread.succeeded.connect(self._refresh_finished)
        thread.failed.connect(self._refresh_failed)
        thread.finished.connect(lambda: self._release_thread(thread))
        thread.start()

    def _refresh_finished(self, slots) -> None:
        self.slots = list(slots)
        self._render_provider()
        self._render_slots(self.slots)
        self._set_busy(False, f"Refreshed {len(self.slots)} slot(s)")

    def _refresh_failed(self, message: str) -> None:
        self._set_busy(False, "Refresh failed")
        self._show_error(message)

    def _release_thread(self, thread) -> None:
        self._threads.discard(thread)
        thread.deleteLater()

    def _render_provider(self) -> None:
        info = self.service.provider_info
        kind = "Virtual" if info.kind is ProviderKind.VIRTUAL else "PKCS#11"
        self.provider_badge.setText(f"{kind} · Connected")
        self.provider_title.setText(info.name or kind)
        parts = [part for part in (info.manufacturer, info.version, info.module_path) if part]
        self.provider_detail.setText("  •  ".join(parts))
        self._update_virtual_buttons()

    def _render_slots(self, slots: list[SlotInfo]) -> None:
        self.table.setRowCount(len(slots))
        for row, slot in enumerate(slots):
            token = slot.token
            values = (
                str(slot.slot_id),
                slot.description or "—",
                token.label if token else "—",
                token.manufacturer if token and token.manufacturer else slot.manufacturer or "—",
                token.model if token else "—",
                token.serial if token else "—",
                slot.state,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, slot.slot_id)
                if column in (0, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, column, item)

        self.table.resizeColumnsToContents()
        self.slot_count.setText(f"{len(slots)} slot{'s' if len(slots) != 1 else ''}")
        if slots:
            self.table.selectRow(0)
        else:
            self.details.setHtml("<p>No slots were reported by this provider.</p>")
        self._update_virtual_buttons()

    def _show_selected_slot(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self.details.clear()
            return

        slot_flags = ", ".join(slot.flags) or "—"
        diagnostic = (
            f"<p><b>Diagnostic:</b> {escape(slot.diagnostic)}</p>" if slot.diagnostic else ""
        )
        token_html = "<p><i>No token present.</i></p>"
        if slot.token is not None:
            token = slot.token
            token_flags = ", ".join(token.flags) or "—"
            token_html = f"""
            <h3>Token</h3>
            <table cellspacing='5'>
              <tr><td><b>Label</b></td><td>{escape(token.label)}</td></tr>
              <tr><td><b>Serial</b></td><td>{escape(token.serial)}</td></tr>
              <tr><td><b>Model</b></td><td>{escape(token.model)}</td></tr>
              <tr><td><b>Manufacturer</b></td><td>{escape(token.manufacturer)}</td></tr>
              <tr><td><b>Initialized</b></td><td>{'Yes' if token.initialized else 'No'}</td></tr>
              <tr><td><b>Login required</b></td><td>{'Yes' if token.login_required else 'No'}</td></tr>
              <tr><td><b>User PIN initialized</b></td><td>{'Yes' if token.user_pin_initialized else 'No'}</td></tr>
              <tr><td><b>Write protected</b></td><td>{'Yes' if token.write_protected else 'No'}</td></tr>
              <tr><td><b>Flags</b></td><td>{escape(token_flags)}</td></tr>
            </table>
            """

        self.details.setHtml(
            f"""
            <h2>Slot {slot.slot_id}</h2>
            <table cellspacing='5'>
              <tr><td><b>Description</b></td><td>{escape(slot.description)}</td></tr>
              <tr><td><b>Manufacturer</b></td><td>{escape(slot.manufacturer)}</td></tr>
              <tr><td><b>Hardware</b></td><td>{escape(slot.hardware_version or '—')}</td></tr>
              <tr><td><b>Firmware</b></td><td>{escape(slot.firmware_version or '—')}</td></tr>
              <tr><td><b>Flags</b></td><td>{escape(slot_flags)}</td></tr>
              <tr><td><b>State</b></td><td>{escape(slot.state)}</td></tr>
            </table>
            {diagnostic}
            <hr>
            {token_html}
            """
        )
        self._update_virtual_buttons()

    def _selected_slot(self) -> SlotInfo | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        if 0 <= row < len(self.slots):
            return self.slots[row]
        return None

    def _create_slot(self) -> None:
        dialog = CreateSlotDialog(self)
        if dialog.exec() != dialog.Accepted:
            return
        try:
            self.service.create_virtual_slot(dialog.description)
            self._reload_virtual_slots("Slot created")
        except Exception as exc:
            self._show_error(str(exc))

    def _initialize_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        dialog = InitializeTokenDialog(self)
        if dialog.exec() != dialog.Accepted:
            return
        value = dialog.value
        try:
            self.service.initialize_virtual_token(
                slot.slot_id,
                value.label,
                value.so_pin,
                value.user_pin,
            )
            self._reload_virtual_slots(f"Token initialized in slot {slot.slot_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _clear_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        if slot.token is None:
            self._show_error("The selected slot is already empty.")
            return
        result = QMessageBox.question(
            self,
            "Clear Virtual Token",
            f"Clear the token from virtual slot {slot.slot_id}?\n\n"
            "All simulated token metadata and future objects in this token will be deleted.",
        )
        if result != QMessageBox.Yes:
            return
        try:
            self.service.clear_virtual_token(slot.slot_id)
            self._reload_virtual_slots(f"Token cleared from slot {slot.slot_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _delete_slot(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        result = QMessageBox.question(
            self,
            "Delete Virtual Slot",
            f"Delete virtual slot {slot.slot_id} ({slot.description})?",
        )
        if result != QMessageBox.Yes:
            return
        try:
            self.service.delete_virtual_slot(slot.slot_id)
            self._reload_virtual_slots(f"Slot {slot.slot_id} deleted")
        except Exception as exc:
            self._show_error(str(exc))

    def _reload_virtual_slots(self, status: str) -> None:
        self.slots = self.service.slots()
        self._render_slots(self.slots)
        self.statusBar().showMessage(status, 5000)

    def _update_virtual_buttons(self) -> None:
        enabled = self.service.supports_virtual_admin and not self._busy
        selected = self._selected_slot()
        self.create_slot_button.setEnabled(enabled)
        self.initialize_button.setEnabled(enabled and selected is not None)
        self.clear_button.setEnabled(enabled and selected is not None and selected.token is not None)
        self.delete_button.setEnabled(enabled and selected is not None)

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self.load_module_button.setEnabled(not busy)
        self.virtual_button.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy)
        self.statusBar().showMessage(message)
        if busy:
            self.setCursor(Qt.WaitCursor)
        else:
            self.unsetCursor()
        self._update_virtual_buttons()

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "SoftHSM Studio", message)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if any(self._is_supported_module(Path(url.toLocalFile())) for url in urls if url.isLocalFile()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if self._is_supported_module(path):
                self._load_module(path)
                event.acceptProposedAction()
                return

    def _is_supported_module(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in self.MODULE_SUFFIXES
