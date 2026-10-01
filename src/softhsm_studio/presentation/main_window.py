from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import PySide6.QtWidgets

from softhsm_studio.application import HsmService
from softhsm_studio.domain.models import ProviderKind, SlotInfo
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider

from .dialogs import CreateSlotDialog, InitializeTokenDialog
from .key_dialog import SlotKeysDialog, KeyOperation
from softhsm_studio.runtime import DisconnectedProvider, prepare_module, settings
from .workers import ProviderConnectThread, ProviderRefreshThread


class MainWindow(PySide6.QtWidgets.QMainWindow):
    MODULE_SUFFIXES = {".dll", ".so", ".dylib"}

    def __init__(self, tool: str = 'admin') -> None:
        super().__init__()
        self.tool = tool
        self.setWindowTitle("HSM Admin Tool · DLL Workspace" if tool == 'admin' else "HSM Key Manager · DLL Workspace")
        self.resize(1320, 820)
        self.setMinimumSize(1080, 680)
        self.setAcceptDrops(True)

        self.service = HsmService(DisconnectedProvider())
        self.slots: list[SlotInfo] = self.service.slots()
        self._threads: set[object] = set()
        self._busy = False

        self._build_ui()
        self._render_provider()
        self._render_slots(self.slots)

        self.virtual_button.hide()
        self.create_slot_button.hide()
        self.clear_button.hide()
        self.delete_button.hide()
        self.feedback.setText('Load your virtual HSM PKCS#11 DLL to begin. Both tools use the same token store.')
        if self.tool == 'admin':
            self.workspace_tabs.setTabVisible(0, False)
            self.workspace_tabs.setCurrentIndex(1)
            self.initialize_button.setText('Create / Initialize Token')
        else:
            self.workspace_tabs.setTabVisible(1, False)
            self.workspace_tabs.setCurrentIndex(0)
        bundled_module = Path(__file__).resolve().parents[3] / 'tools' / 'softhsm2' / 'SoftHSM2' / 'lib' / 'softhsm2-x64.dll'
        last_module = settings().value('module', '') or str(bundled_module)
        if last_module and Path(last_module).is_file():
            QTimer.singleShot(0, lambda: self._load_module(Path(last_module)))

    def _build_ui(self) -> None:
        root = PySide6.QtWidgets.QWidget()
        root_layout = PySide6.QtWidgets.QHBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(14)

        sidebar = PySide6.QtWidgets.QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)
        side_layout = PySide6.QtWidgets.QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(10)

        title = PySide6.QtWidgets.QLabel("Admin Tool" if self.tool == 'admin' else "Key Manager")
        title.setObjectName("AppTitle")
        subtitle = PySide6.QtWidgets.QLabel("Load DLL → Initialize token" if self.tool == 'admin' else "Load DLL → Slot → Keys")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        self.provider_badge = PySide6.QtWidgets.QLabel()
        self.provider_badge.setObjectName("ProviderBadge")
        self.provider_badge.setWordWrap(True)

        side_layout.addWidget(title)
        side_layout.addWidget(subtitle)
        side_layout.addSpacing(6)
        side_layout.addWidget(self.provider_badge)
        side_layout.addSpacing(14)
        side_layout.addWidget(self._section_label("1. CONNECTION"))

        self.virtual_button = PySide6.QtWidgets.QPushButton("Use Virtual HSM")
        self.virtual_button.clicked.connect(self._switch_to_virtual)
        self.load_module_button = PySide6.QtWidgets.QPushButton("Load HSM DLL…")
        self.load_module_button.setToolTip("Choose the PKCS#11 module supplied with your HSM.")
        self.load_module_button.clicked.connect(self._choose_module)
        self.refresh_button = PySide6.QtWidgets.QPushButton("Refresh Slots")
        self.refresh_button.clicked.connect(self._refresh_provider)

        side_layout.addWidget(self.virtual_button)
        side_layout.addWidget(self.load_module_button)
        side_layout.addWidget(self.refresh_button)
        side_layout.addSpacing(14)


        self.create_slot_button = PySide6.QtWidgets.QPushButton("Create Slot")
        self.create_slot_button.setObjectName("PrimaryButton")
        self.create_slot_button.clicked.connect(self._create_slot)
        self.initialize_button = PySide6.QtWidgets.QPushButton("Initialize Token")
        self.initialize_button.clicked.connect(self._initialize_token)
        self.clear_button = PySide6.QtWidgets.QPushButton("Clear Token")
        self.clear_button.clicked.connect(self._clear_token)
        self.delete_button = PySide6.QtWidgets.QPushButton("Delete Slot")
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self._delete_slot)





        side_layout.addStretch(1)

        warning = PySide6.QtWidgets.QLabel(
            "Virtual mode simulates HSM behavior for development. "
            "It is not a hardware security boundary."
        )
        warning.setObjectName("Muted")
        warning.setWordWrap(True)
        side_layout.addWidget(warning)

        content = PySide6.QtWidgets.QFrame()
        content.setObjectName("Panel")
        content_layout = PySide6.QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(12)

        header_layout = PySide6.QtWidgets.QHBoxLayout()
        self.provider_title = PySide6.QtWidgets.QLabel()
        self.provider_title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        self.slot_count = PySide6.QtWidgets.QLabel()
        self.slot_count.setObjectName("Muted")
        header_layout.addWidget(self.provider_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.slot_count)
        content_layout.addLayout(header_layout)

        self.provider_detail = PySide6.QtWidgets.QLabel()
        self.provider_detail.setObjectName("Muted")
        self.provider_detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.provider_detail.setWordWrap(True)
        content_layout.addWidget(self.provider_detail)
        self.feedback = PySide6.QtWidgets.QLabel("Choose a slot below, or create one to get started.")
        self.feedback.setObjectName("Feedback")
        self.feedback.setWordWrap(True)
        content_layout.addWidget(self.feedback)
        create_row = PySide6.QtWidgets.QHBoxLayout()
        create_row.addWidget(self._section_label("2. SELECT A SLOT"))
        create_row.addStretch(1)
        create_row.addWidget(self.create_slot_button)
        content_layout.addLayout(create_row)

        splitter = PySide6.QtWidgets.QSplitter(Qt.Horizontal)
        self.table = PySide6.QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Slot ID", "Description", "Token", "Manufacturer", "Model", "Serial", "State"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(PySide6.QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(PySide6.QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(PySide6.QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        for column in (3, 4, 5):
            self.table.setColumnHidden(column, True)
        self.table.horizontalHeader().setSectionResizeMode(1, PySide6.QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._show_selected_slot)
        self.table.doubleClicked.connect(self._open_slot_keys)
        splitter.addWidget(self.table)

        selected_panel = PySide6.QtWidgets.QWidget()
        selected_layout = PySide6.QtWidgets.QVBoxLayout(selected_panel)
        selected_layout.setContentsMargins(0, 8, 0, 0)
        self.selected_title = self._section_label("SELECTED SLOT")
        selected_layout.addWidget(self.selected_title)
        self.next_step = PySide6.QtWidgets.QLabel()
        self.next_step.setWordWrap(True)
        selected_layout.addWidget(self.next_step)

        self.keys_button = PySide6.QtWidgets.QPushButton("Open Key Manager →")
        self.keys_button.setObjectName("PrimaryButton")
        self.keys_button.clicked.connect(self._open_slot_keys)
        self.workspace_tabs = PySide6.QtWidgets.QTabWidget()
        key_page = PySide6.QtWidgets.QWidget()
        key_layout = PySide6.QtWidgets.QVBoxLayout(key_page)
        key_layout.setSpacing(16)
        key_heading = self._section_label("3. MANAGE TOKEN KEYS")
        key_layout.addWidget(key_heading)
        key_help = PySide6.QtWidgets.QLabel(
            "Open the key manager to view keys, enter your USER PIN, or generate a new AES / RSA key."
        )
        key_help.setWordWrap(True)
        key_layout.addWidget(key_help)
        key_layout.addWidget(self.keys_button)
        key_layout.addStretch(1)
        self.workspace_tabs.addTab(key_page, "Key Manager")
        admin_page = PySide6.QtWidgets.QWidget()
        admin_layout = PySide6.QtWidgets.QVBoxLayout(admin_page)
        admin_layout.setSpacing(16)
        admin_help = PySide6.QtWidgets.QLabel(
            "Select the free SoftHSM slot, then create a token with its name, administrator PIN and USER PIN. "
            "The separate Key Manager uses the same DLL to generate and view keys."
        )
        admin_help.setWordWrap(True)
        admin_layout.addWidget(admin_help)
        admin_layout.addWidget(self.initialize_button)
        admin_layout.addWidget(self.clear_button)
        admin_layout.addWidget(self.delete_button)
        admin_layout.addStretch(1)
        self.workspace_tabs.addTab(admin_page, "Administration")
        selected_layout.addWidget(self.workspace_tabs)
        self.details = PySide6.QtWidgets.QTextBrowser()
        self.details.setOpenExternalLinks(False)
        selected_layout.addWidget(self.details, 1)
        splitter.addWidget(selected_panel)
        splitter.setSizes([570, 420])
        content_layout.addWidget(splitter, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("DLL workspace · Admin Tool and Key Manager are separate applications")

    @staticmethod
    def _section_label(text: str) -> PySide6.QtWidgets.QLabel:
        label = PySide6.QtWidgets.QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def _choose_module(self) -> None:
        path, _ = PySide6.QtWidgets.QFileDialog.getOpenFileName(
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
        path = prepare_module(path)
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
        if isinstance(provider, Pkcs11ModuleProvider):
            settings().setValue('module', str(provider.module_path))
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
        self.provider_badge.setText(f"{kind} · Connected" if info.module_path else "No DLL loaded")
        self.provider_title.setText(info.name or kind)
        parts = [part for part in (info.manufacturer, info.version, info.module_path) if part]
        self.provider_detail.setToolTip("  •  ".join(parts))
        self.provider_detail.setText("Load a PKCS#11 DLL to begin." if not info.module_path else "Select a free slot to initialize a token." if self.tool == 'admin' else "Select an initialized slot to view and generate keys.")
        self._update_virtual_buttons()

    def _render_slots(self, slots: list[SlotInfo], selected_id: int | None = None) -> None:
        if selected_id is None:
            row = self.table.currentRow()
            if row >= 0 and self.table.item(row, 0) is not None:
                selected_id = self.table.item(row, 0).data(Qt.UserRole)
        self.table.blockSignals(True)
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
                slot.state.replace("_", " ").title(),
            )
            for column, value in enumerate(values):
                item = PySide6.QtWidgets.QTableWidgetItem(value)
                item.setData(Qt.UserRole, slot.slot_id)
                if column in (0, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, column, item)

        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.slot_count.setText(f"{len(slots)} slot{'s' if len(slots) != 1 else ''}")
        if slots:
            row = next((i for i, slot in enumerate(slots) if slot.slot_id == selected_id), 0)
            self.table.selectRow(row)
            self._show_selected_slot()
        else:
            self._show_selected_slot()
        self._update_virtual_buttons()

    def _show_selected_slot(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self.selected_title.setText("NO SLOT SELECTED")
            self.next_step.setText("Load your virtual HSM DLL. Admin Tool prepares tokens; Key Manager manages their keys.")
            self.details.setHtml("<p>A slot holds a token and its keys.</p>")
            self._update_virtual_buttons()
            return

        self.workspace_tabs.setCurrentIndex(1 if self.tool == 'admin' else 0)
        self.selected_title.setText(f"{slot.description or 'Slot'} · Slot {slot.slot_id}")
        self.next_step.setText("This slot is empty. Initialize a token to prepare it for use." if slot.token is None and self.service.supports_virtual_admin else "Token details are shown below.")
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

    def _open_slot_keys(self) -> None:
        if self.tool != 'key-manager':
            self.feedback.setText('Open the separate Key Manager tool to view or generate keys.')
            return
        slot = self._selected_slot()
        if self._busy or slot is None:
            return
        if slot.token is None or not slot.token.initialized:
            self._show_error("Initialize a token in this slot before managing keys.")
            return
        SlotKeysDialog(self.service, slot, self).exec()

    def _create_slot(self) -> None:
        dialog = CreateSlotDialog(self)
        if dialog.exec() != PySide6.QtWidgets.QDialog.DialogCode.Accepted:
            return
        try:
            created = self.service.create_virtual_slot(dialog.description)
            self._reload_virtual_slots(f"Slot {created.slot_id} created. Initialize its token to continue.", created.slot_id)
        except Exception as exc:
            self._show_error(str(exc))

    def _initialize_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        dialog = InitializeTokenDialog(self)
        if dialog.exec() != PySide6.QtWidgets.QDialog.DialogCode.Accepted:
            return
        value = dialog.value
        if isinstance(self.service.provider, Pkcs11ModuleProvider):
            self._set_busy(True, 'Initializing the selected virtual token…')
            worker = KeyOperation(self.service, slot.slot_id, 'initialize', self,
                                  label=value.label, so_pin=value.so_pin, user_pin=value.user_pin)
            self._threads.add(worker)
            worker.succeeded.connect(lambda result: self._token_initialized(result))
            worker.failed.connect(lambda message: self._token_initialize_failed(message))
            worker.finished.connect(lambda: self._release_thread(worker))
            worker.start()
            return
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

    def _token_initialized(self, result) -> None:
        try:
            self.slots = self.service.refresh()
            self._render_slots(self.slots)
            self._set_busy(False, result['message'])
        except Exception as exc:
            self._set_busy(False, 'Initialization completed, but slot refresh failed. Refresh before retrying.')
            self._show_error(str(exc))

    def _token_initialize_failed(self, message) -> None:
        self._set_busy(False, 'Token initialization failed. Refresh slots before retrying.')
        self._show_error(message)

    def _clear_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        if slot.token is None:
            self._show_error("The selected slot is already empty.")
            return
        result = PySide6.QtWidgets.QMessageBox.question(
            self,
            "Clear Virtual Token",
            f"Clear the token from virtual slot {slot.slot_id}?\n\n"
            "The token and all its stored objects will be permanently removed. The slot will remain available.",
        )
        if result != PySide6.QtWidgets.QMessageBox.Yes:
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
        result = PySide6.QtWidgets.QMessageBox.question(
            self,
            "Delete Virtual Slot",
            f"Delete virtual slot {slot.slot_id} ({slot.description})?\n\n"
            "The slot, its token and any stored objects will be permanently removed.",
            PySide6.QtWidgets.QMessageBox.StandardButton.Yes | PySide6.QtWidgets.QMessageBox.StandardButton.No,
            PySide6.QtWidgets.QMessageBox.StandardButton.No,
        )
        if result != PySide6.QtWidgets.QMessageBox.Yes:
            return
        try:
            self.service.delete_virtual_slot(slot.slot_id)
            self._reload_virtual_slots(f"Slot {slot.slot_id} deleted")
        except Exception as exc:
            self._show_error(str(exc))

    def _reload_virtual_slots(self, status: str, selected_id: int | None = None) -> None:
        self.slots = self.service.slots()
        self._render_slots(self.slots, selected_id)
        self.feedback.setText(status)
        self.statusBar().showMessage(status, 5000)

    def _update_virtual_buttons(self) -> None:
        enabled = self.service.supports_virtual_admin and not self._busy
        selected = self._selected_slot()
        self.create_slot_button.setEnabled(enabled)
        self.keys_button.setEnabled(not self._busy and selected is not None and selected.token is not None and selected.token.initialized)
        info = self.service.provider_info
        soft_hsm = 'softhsm' in (info.name + ' ' + info.description + ' ' + info.manufacturer).lower()
        uninitialized = selected is not None and (selected.token is None or not selected.token.initialized)
        self.initialize_button.setEnabled(self.tool == 'admin' and not self._busy and soft_hsm and uninitialized)
        self.initialize_button.setToolTip("Select an uninitialized SoftHSM slot. Vendor hardware administration uses its own client.")
        self.clear_button.setEnabled(enabled and selected is not None and selected.token is not None)
        self.delete_button.setEnabled(enabled and selected is not None)

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self.feedback.setText(message)
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
        PySide6.QtWidgets.QMessageBox.critical(self, "SoftHSM Studio", message)

    def closeEvent(self, event) -> None:
        if self._threads:
            self.feedback.setText('Wait for the current HSM operation to finish before closing.')
            event.ignore()
            return
        self.service.close()
        event.accept()

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
