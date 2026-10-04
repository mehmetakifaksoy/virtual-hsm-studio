from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from softhsm_studio.domain.ports import HsmProvider


class ProviderConnectThread(QThread):
    succeeded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, provider: HsmProvider, parent=None) -> None:
        super().__init__(parent)
        self.provider = provider

    def run(self) -> None:
        try:
            self.provider.connect()
            slots = self.provider.list_slots()
        except Exception as exc:
            message = str(exc)
            try:
                self.provider.close()
            except Exception as close_error:
                message = f"{message}\nProvider cleanup failed: {close_error}"
            self.failed.emit(message)
            return
        self.succeeded.emit(self.provider, slots)


class ProviderRefreshThread(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, provider: HsmProvider, parent=None) -> None:
        super().__init__(parent)
        self.provider = provider

    def run(self) -> None:
        try:
            slots = self.provider.refresh()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(slots)
