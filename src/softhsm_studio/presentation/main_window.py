from __future__ import annotations

from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from softhsm_studio.application import HsmService
from softhsm_studio.domain.models import ProviderKind, SessionInfo, SessionRole, SlotInfo
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.runtime import DisconnectedProvider, prepare_module, settings

from .dialogs import CreateSlotDialog, InitializeTokenDialog
from .key_dialog import KeyOperation, SlotKeysDialog
from .pages import DashboardPage, ProvidersPage, SessionsPage, SlotsPage
from .workers import ProviderConnectThread, ProviderRefreshThread


class MainWindow(QMainWindow):
    MODULE_SUFFIXES = {".dll", ".so", ".dylib"}
    PAGE_NAMES = ("Dashboard", "Providers", "Slots", "Sessions")

    def __init__(self, tool: str = "admin") -> None:
        super().__init__()
        self.tool = tool
        self.setWindowTitle("Virtual HSM Studio · HSM Management Console")
        self.resize(1320, 820)
        self.setMinimumSize(1080, 680)
        self.setAcceptDrops(True)

        self.service = HsmService(DisconnectedProvider())
        self.slots: list[SlotInfo] = self.service.slots()
        self.sessions: list[SessionInfo] = []
        self._threads: set[object] = set()
        self._busy = False
        self._last_status = "Connect an HSM provider to begin."

        self._build_ui()
        self._render_provider()
        self._render_slots(self.slots)
        self._set_status(self._last_status)

        bundled_module = (
            Path(__file__).resolve().parents[3]
            / "tools"
            / "softhsm2"
            / "SoftHSM2"
            / "lib"
            / "softhsm2-x64.dll"
        )
        last_module = settings().value("module", "") or str(bundled_module)
        if last_module and Path(last_module).is_file():
            QTimer.singleShot(0, lambda: self._load_module(Path(last_module)))

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(10)

        title = QLabel("Virtual HSM Studio")
        title.setObjectName("AppTitle")
        subtitle = QLabel("HSM management console")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        side_layout.addWidget(title)
        side_layout.addWidget(subtitle)
        side_layout.addSpacing(12)

        self.navigation: list[QPushButton] = []
        for index, page_name in enumerate(self.PAGE_NAMES):
            button = QPushButton(page_name)
            button.setObjectName("NavigationButton")
            button.setCheckable(True)
            button.clicked.connect(partial(self._navigate, index))
            self.navigation.append(button)
            side_layout.addWidget(button)

        side_layout.addStretch(1)
        warning = QLabel(
            "Virtual mode is for development and testing. It is not a hardware security boundary."
        )
        warning.setObjectName("Muted")
        warning.setWordWrap(True)
        side_layout.addWidget(warning)

        content = QFrame()
        content.setObjectName("Panel")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(12)

        header = QHBoxLayout()
        self.provider_badge = QLabel("Not connected")
        self.provider_badge.setObjectName("ProviderBadge")
        self.provider_title = QLabel("HSM Management Console")
        self.provider_title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        self.slot_count = QLabel("0 slots")
        self.slot_count.setObjectName("Muted")
        header.addWidget(self.provider_badge)
        header.addWidget(self.provider_title)
        header.addStretch(1)
        header.addWidget(self.slot_count)
        content_layout.addLayout(header)

        self.provider_detail = QLabel()
        self.provider_detail.setObjectName("Muted")
        self.provider_detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.provider_detail.setWordWrap(True)
        content_layout.addWidget(self.provider_detail)

        self.feedback = QLabel()
        self.feedback.setObjectName("Feedback")
        self.feedback.setWordWrap(True)
        content_layout.addWidget(self.feedback)

        self.dashboard_page = DashboardPage()
        self.providers_page = ProvidersPage()
        self.slots_page = SlotsPage()
        self.sessions_page = SessionsPage()
        self.page_stack = QStackedWidget()
        for page in (
            self.dashboard_page,
            self.providers_page,
            self.slots_page,
            self.sessions_page,
        ):
            self.page_stack.addWidget(page)
        content_layout.addWidget(self.page_stack, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage(self._last_status)

        self.providers_page.load_module_requested.connect(self._choose_module)
        self.providers_page.virtual_provider_requested.connect(self._switch_to_virtual)
        self.providers_page.refresh_requested.connect(self._refresh_provider)
        self.slots_page.slot_selected.connect(self._slot_selection_changed)
        self.slots_page.create_slot_requested.connect(self._create_slot)
        self.slots_page.initialize_token_requested.connect(self._initialize_token)
        self.slots_page.clear_token_requested.connect(self._clear_token)
        self.slots_page.delete_slot_requested.connect(self._delete_slot)
        self.slots_page.manage_keys_requested.connect(self._open_slot_keys)
        self.sessions_page.refresh_requested.connect(self._refresh_sessions)
        self.sessions_page.open_session_requested.connect(self._open_session)
        self.sessions_page.close_session_requested.connect(self._close_session)
        self.sessions_page.login_requested.connect(self._login_session)
        self.sessions_page.logout_requested.connect(self._logout_session)
        self._navigate(0)

    def _navigate(self, page_index: int, checked: bool = True) -> None:
        self.page_stack.setCurrentIndex(page_index)
        for index, button in enumerate(self.navigation):
            button.setChecked(index == page_index)
        if not checked:
            self.navigation[page_index].setChecked(True)

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
        try:
            module_path = prepare_module(path)
            provider = Pkcs11ModuleProvider(module_path)
        except Exception as exc:
            self._show_error(str(exc))
            return
        self._connect_provider_async(provider, f"Loading {path.name}…")

    def _switch_to_virtual(self) -> None:
        self._connect_provider_async(VirtualHsmProvider(), "Opening Virtual HSM…")

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
            settings().setValue("module", str(provider.module_path))
        self._render_provider()
        self._render_slots(list(slots))
        self._set_status(f"Connected · {len(self.slots)} slot(s) available")
        self._set_busy(False, self._last_status)

    def _provider_connect_failed(self, message: str) -> None:
        self._set_busy(False, "Provider connection failed")
        self._show_error(message)

    def _refresh_provider(self) -> None:
        if isinstance(self.service.provider, DisconnectedProvider):
            self._show_error("Connect a provider before refreshing.")
            return
        self._set_busy(True, "Refreshing provider slots…")
        thread = ProviderRefreshThread(self.service.provider, self)
        self._threads.add(thread)
        thread.succeeded.connect(self._refresh_finished)
        thread.failed.connect(self._refresh_failed)
        thread.finished.connect(lambda: self._release_thread(thread))
        thread.start()

    def _refresh_finished(self, slots) -> None:
        self._render_provider()
        self._render_slots(list(slots))
        self._set_status(f"Refreshed {len(self.slots)} slot(s)")
        self._set_busy(False, self._last_status)

    def _refresh_failed(self, message: str) -> None:
        self._set_busy(False, "Provider refresh failed")
        self._show_error(message)

    def _release_thread(self, thread) -> None:
        self._threads.discard(thread)
        thread.deleteLater()

    def _render_provider(self) -> None:
        info = self.service.provider_info
        connected = not isinstance(self.service.provider, DisconnectedProvider)
        kind = "Virtual" if info.kind is ProviderKind.VIRTUAL else "PKCS#11"
        self.provider_badge.setText(f"{kind} · Connected" if connected else "Not connected")
        self.provider_title.setText(info.name if connected else "HSM Management Console")
        parts = [part for part in (info.manufacturer, info.version, info.module_path) if part]
        self.provider_detail.setText(" · ".join(parts) if connected else info.description)
        self.providers_page.set_provider(info, connected, self._busy)

    def _render_slots(self, slots: list[SlotInfo], selected_id: int | None = None) -> None:
        self.slots = list(slots)
        self.slots_page.set_slots(self.slots, selected_id)
        self.slot_count.setText(f"{len(self.slots)} slot{'s' if len(self.slots) != 1 else ''}")
        self._render_sessions()
        self._update_virtual_buttons()
        self._update_dashboard()

    def _render_sessions(self) -> None:
        supported = self.service.supports_sessions
        try:
            self.sessions = self.service.sessions() if supported else []
        except Exception as exc:
            self.sessions = []
            self.sessions_page.set_data(
                self.slots,
                self.sessions,
                supported,
                self._busy,
            )
            self.sessions_page.message.setText(f"Could not load sessions: {exc}")
            self._show_error(f"Could not load active HSM sessions: {exc}")
            return
        self.sessions_page.set_data(
            self.slots,
            self.sessions,
            supported,
            self._busy,
        )

    def _update_dashboard(self) -> None:
        info = self.service.provider_info
        connected = not isinstance(self.service.provider, DisconnectedProvider)
        self.dashboard_page.set_state(
            info,
            connected,
            self.slots,
            self.sessions,
            self.service.supports_sessions,
            self._last_status,
        )

    def _slot_selection_changed(self, slot: SlotInfo | None) -> None:
        if slot != self._selected_slot():
            return
        self._update_virtual_buttons()

    def _selected_slot(self) -> SlotInfo | None:
        return self.slots_page.selected_slot

    def _open_slot_keys(self) -> None:
        slot = self._selected_slot()
        if self._busy or slot is None:
            return
        if slot.token is None or not slot.token.initialized:
            self._show_error("Initialize a token in this slot before managing keys.")
            return
        SlotKeysDialog(self.service, slot, self).exec()

    def _create_slot(self) -> None:
        dialog = CreateSlotDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            created = self.service.create_virtual_slot(dialog.description)
            self._reload_virtual_slots(
                f"Slot {created.slot_id} created. Initialize its token to continue.",
                created.slot_id,
            )
        except Exception as exc:
            self._show_error(str(exc))

    def _initialize_token(self) -> None:
        slot = self._selected_slot()
        if slot is None:
            self._show_error("Select a slot first.")
            return
        dialog = InitializeTokenDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        value = dialog.value
        if isinstance(self.service.provider, Pkcs11ModuleProvider):
            self._set_busy(True, "Initializing the selected token…")
            worker = KeyOperation(
                self.service,
                slot.slot_id,
                "initialize",
                self,
                label=value.label,
                so_pin=value.so_pin,
                user_pin=value.user_pin,
            )
            self._threads.add(worker)
            worker.succeeded.connect(self._token_initialized)
            worker.failed.connect(self._token_initialize_failed)
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
            self._render_slots(self.service.refresh())
        except Exception as exc:
            self._set_busy(
                False,
                "Initialization completed, but slot refresh failed. Refresh before retrying.",
            )
            self._show_error(str(exc))
            return
        self._set_busy(False, result["message"])

    def _token_initialize_failed(self, message: str) -> None:
        self._set_busy(False, "Token initialization failed. Refresh slots before retrying.")
        self._show_error(message)

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
            "The token and all its stored objects will be permanently removed. "
            "The slot will remain available.",
        )
        if result != QMessageBox.StandardButton.Yes:
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
            f"Delete virtual slot {slot.slot_id} ({slot.description})?\n\n"
            "The slot, its token and any stored objects will be permanently removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_virtual_slot(slot.slot_id)
            self._reload_virtual_slots(f"Slot {slot.slot_id} deleted")
        except Exception as exc:
            self._show_error(str(exc))

    def _reload_virtual_slots(
        self,
        status: str,
        selected_id: int | None = None,
    ) -> None:
        self._render_slots(self.service.slots(), selected_id)
        self._set_status(status)

    def _update_virtual_buttons(self) -> None:
        selected = self._selected_slot()
        info = self.service.provider_info
        is_virtual_admin = self.service.supports_virtual_admin
        provider_details = f"{info.name} {info.description} {info.manufacturer}".lower()
        can_initialize = (
            selected is not None
            and (selected.token is None or not selected.token.initialized)
            and (is_virtual_admin or "softhsm" in provider_details)
        )
        initialized = (
            selected is not None and selected.token is not None and selected.token.initialized
        )
        self.slots_page.set_action_availability(
            can_create=is_virtual_admin and not self._busy,
            can_initialize=can_initialize and not self._busy,
            can_clear=(
                is_virtual_admin
                and selected is not None
                and selected.token is not None
                and not self._busy
            ),
            can_delete=is_virtual_admin and selected is not None and not self._busy,
            can_manage_keys=initialized and not self._busy,
        )

    def _refresh_sessions(self) -> None:
        if not self.service.supports_sessions:
            self._show_error("The active provider does not support session management.")
            return
        try:
            self.sessions = self.service.sessions()
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.sessions_page.set_data(
            self.slots,
            self.sessions,
            True,
            self._busy,
        )
        self._update_dashboard()

    def _open_session(self, slot_id: int, read_write: bool) -> None:
        try:
            self.service.open_session(slot_id, read_write=read_write)
            self._refresh_sessions()
            self._set_status(f"Opened a session on slot {slot_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _close_session(self, session_id: int) -> None:
        try:
            self.service.close_session(session_id)
            self._refresh_sessions()
            self._set_status(f"Closed session {session_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _login_session(self, session_id: int, role: str, pin: str) -> None:
        try:
            if role == SessionRole.SO.value.upper():
                self.service.login_so(session_id, pin)
            else:
                self.service.login_user(session_id, pin)
        except Exception as exc:
            self._show_error(str(exc))
        finally:
            pin = ""
        self._refresh_sessions()

    def _logout_session(self, session_id: int) -> None:
        try:
            self.service.logout(session_id)
            self._refresh_sessions()
            self._set_status(f"Logged out session {session_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self.providers_page.set_provider(
            self.service.provider_info,
            not isinstance(self.service.provider, DisconnectedProvider),
            busy,
        )
        self.sessions_page.set_busy(busy, self.service.supports_sessions)
        self._set_status(message)
        self._update_virtual_buttons()
        if busy:
            self.setCursor(Qt.CursorShape.WaitCursor)
        else:
            self.unsetCursor()

    def _set_status(self, message: str) -> None:
        self._last_status = message
        self.feedback.setText(message)
        self.statusBar().showMessage(message, 5000)
        self.dashboard_page.set_status(message)

    def _show_error(self, message: str) -> None:
        self._set_status(message)
        QMessageBox.critical(self, "Virtual HSM Studio", message)

    def closeEvent(self, event) -> None:
        if self._threads:
            self.feedback.setText("Wait for the current HSM operation to finish before closing.")
            event.ignore()
            return
        self.service.close()
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if any(
            self._is_supported_module(Path(url.toLocalFile())) for url in urls if url.isLocalFile()
        ):
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
