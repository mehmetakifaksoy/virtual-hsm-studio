"""Standalone key management application; no slot administration controls."""
import argparse
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog
from softhsm_studio.application import HsmService
from softhsm_studio.runtime import DisconnectedProvider, prepare_module
from softhsm_studio.infrastructure.pkcs11 import Pkcs11ModuleProvider
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.presentation.workers import ProviderConnectThread
from softhsm_studio.presentation.key_dialog import SlotKeysDialog
from softhsm_studio.presentation.theme import APP_STYLESHEET


class KeyManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('HSM Key Manager')
        self.resize(850, 520)
        self.service = HsmService(DisconnectedProvider())
        self.worker = None
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)
        title = QLabel('Key Manager')
        title.setObjectName('PageTitle')
        layout.addWidget(title)
        note = QLabel('Connect your HSM, select an initialized token, then view or generate keys.\nPrepare slots and tokens separately in HSM Studio.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.connect_button = QPushButton('Connect HSM…')
        self.connect_button.setObjectName('PrimaryButton')
        self.connect_button.clicked.connect(self.choose_module)
        layout.addWidget(self.connect_button)
        self.demo_button = QPushButton('Open existing local demo tokens')
        self.demo_button.clicked.connect(lambda: self.connect_provider(VirtualHsmProvider()))
        layout.addWidget(self.demo_button)
        self.tokens = QComboBox()
        self.tokens.setPlaceholderText('Connect a provider to select a token')
        layout.addWidget(self.tokens)
        self.open_button = QPushButton('Manage Selected Token Keys')
        self.open_button.clicked.connect(self.open_keys)
        self.open_button.setEnabled(False)
        layout.addWidget(self.open_button)
        self.status = QLabel('Not connected. Demo tokens simulate metadata only; they cannot sign data.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()
        self.setCentralWidget(root)

    def choose_module(self):
        name, _ = QFileDialog.getOpenFileName(self, 'Select vendor PKCS#11 module', '', 'PKCS#11 modules (*.dll *.so *.dylib)')
        if name:
            self.connect_provider(Pkcs11ModuleProvider(prepare_module(Path(name))))

    def connect_provider(self, provider):
        if self.worker:
            return
        self.connect_button.setEnabled(False)
        self.demo_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.status.setText('Connecting…')
        self.worker = ProviderConnectThread(provider, self)
        self.worker.succeeded.connect(self.connected)
        self.worker.failed.connect(self.status.setText)
        self.worker.finished.connect(self.finished)
        self.worker.start()

    def connected(self, provider, slots):
        self.service.activate_connected(provider)
        self.tokens.clear()
        for slot in slots:
            if slot.token and slot.token.initialized:
                self.tokens.addItem(f'{slot.token.label} — Slot {slot.slot_id}', slot)
        if self.tokens.count():
            self.tokens.setCurrentIndex(0)
        mode = 'Demo simulation (metadata only)' if self.service.supports_virtual_admin else self.service.provider_info.name
        self.status.setText(f'{mode}. Select a token to manage keys.' if self.tokens.count() else
                            f'{mode}. No initialized tokens. Prepare a token in HSM Studio or your vendor tool, then reconnect.')

    def finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.connect_button.setEnabled(True)
        self.demo_button.setEnabled(True)
        self.open_button.setEnabled(self.tokens.count() > 0)

    def open_keys(self):
        slot = self.tokens.currentData()
        if slot is not None and self.worker is None:
            SlotKeysDialog(self.service, slot, self).exec()

    def closeEvent(self, event):
        if self.worker:
            event.ignore()
            return
        self.service.close()
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    app.setApplicationName('HSM Key Manager')
    app.setOrganizationName('VirtualHsmStudio')
    app.setStyleSheet(APP_STYLESHEET)
    window = KeyManagerWindow()
    window.show()
    if args.smoke_test:
        QTimer.singleShot(300, window.close)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
