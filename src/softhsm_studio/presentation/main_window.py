from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

from softhsm_studio.application import HsmService
from softhsm_studio.domain.models import ProviderKind, SessionInfo, SlotInfo
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.runtime import DisconnectedProvider, prepare_module, settings

from .pages.slot_actions import SlotActions
from .pages.session_actions import SessionActions
from .widgets.console import build_console
from .workers import ProviderConnectThread, ProviderRefreshThread


class MainWindow(SlotActions, SessionActions, QMainWindow):
    MODULE_SUFFIXES = {".dll", ".so", ".dylib"}
    PAGE_NAMES = ("Home", "Connections", "Slots", "Sessions")

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

        # Starting a POC must never load a previously used vendor DLL implicitly.
        # The user explicitly chooses Virtual HSM or a module on each launch.

    def _build_ui(self) -> None:
        build_console(self)

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
        if self._busy:
            return
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
        if self._busy:
            return
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
        self.provider_badge.setProperty("connected", connected)
        self.provider_badge.style().unpolish(self.provider_badge)
        self.provider_badge.style().polish(self.provider_badge)
        self.provider_badge.setText(f"{kind} · Connected" if connected else "Not connected")
        self.provider_title.setText(info.name if connected else "HSM Management Console")
        parts = [part for part in (info.manufacturer, info.version, info.module_path) if part]
        self.provider_detail.setText(" · ".join(parts) if connected else info.description)
        self.providers_page.set_provider(info, connected, self._busy)
        self.providers_page.set_capabilities(self.service)

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

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self.providers_page.set_provider(
            self.service.provider_info,
            not isinstance(self.service.provider, DisconnectedProvider),
            busy,
        )
        self.sessions_page.set_busy(busy, self.service.supports_sessions)
        self.dashboard_page.set_busy(busy)
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
        try:
            self.service.close()
        except Exception:
            self._set_status("Provider cleanup failed. Close its sessions and retry.")
            event.ignore()
            return
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
