from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QTabWidget, QWidget, QHeaderView,
)
from softhsm_studio.application.keys import slot_keys


class KeyOperation(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, service, slot_id, action, parent, **values):
        super().__init__(parent)
        self.service, self.slot_id, self.action, self.values = service, slot_id, action, values

    def run(self):
        try:
            self.succeeded.emit(slot_keys(self.service, self.slot_id, self.action, **self.values))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.values.clear()


class SlotKeysDialog(QDialog):
    def __init__(self, service, slot, parent=None):
        super().__init__(parent)
        self.service, self.slot = service, slot
        self.worker = None
        self.setWindowTitle(f"Keys · {slot.description} · Slot {slot.slot_id}")
        self.resize(820, 620)
        layout = QVBoxLayout(self)
        title = QLabel(f"Keys in {slot.description or 'slot'}")
        title.setObjectName('AppTitle')
        layout.addWidget(title)
        help_text = QLabel(
            'SIMULATION: this provider creates metadata only, not usable cryptographic keys.'
            if service.supports_virtual_admin else
            'Keys are generated and stored on your HSM. Private and secret keys are non-extractable.'
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        auth = QHBoxLayout()
        auth.addWidget(QLabel('USER PIN'))
        self.pin = QLineEdit()
        self.pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin.setPlaceholderText('Enter PIN to view private keys')
        auth.addWidget(self.pin, 1)
        self.login = QPushButton('Login / Show Keys')
        self.login.clicked.connect(lambda: self.start('list'))
        auth.addWidget(self.login)
        layout.addLayout(auth)
        self.tabs = QTabWidget()
        keys_page = QWidget()
        keys_layout = QVBoxLayout(keys_page)
        generate_page = QWidget()
        generate_layout = QVBoxLayout(generate_page)
        self.tabs.addTab(keys_page, 'Keys')
        self.tabs.addTab(generate_page, 'Generate Key')
        layout.addWidget(self.tabs, 1)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search keys by name, type or ID…')
        self.search.textChanged.connect(self.filter_keys)
        keys_layout.addWidget(self.search)
        form = QFormLayout()
        self.label = QLineEdit()
        self.label.setPlaceholderText('e.g. application-signing')
        self.algorithm = QComboBox()

        form.addRow('Key name', self.label)
        form.addRow('Key type', self.algorithm)
        generate_layout.addWidget(QLabel('Choose a name and algorithm for the new key.'))
        generate_layout.addLayout(form)
        actions = QHBoxLayout()
        self.refresh = QPushButton('Refresh Keys')
        self.generate = QPushButton('Generate Key')
        self.generate.setObjectName('PrimaryButton')
        self.refresh.clicked.connect(lambda: self.start('list'))
        self.generate.clicked.connect(lambda: self.start('generate'))
        actions.addWidget(self.refresh)
        actions.addWidget(self.generate)
        actions.addStretch()
        generate_layout.addLayout(actions)
        self.status = QLabel('Checking supported key types…')
        self.status.setWordWrap(True)
        self.status.setObjectName('Feedback')
        layout.addWidget(self.status)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Key name', 'Object type', 'Algorithm', 'ID'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        keys_layout.addWidget(self.table, 1)
        keys_refresh = QPushButton('Refresh Keys')
        keys_refresh.clicked.connect(lambda: self.start('list'))
        keys_layout.addWidget(keys_refresh)
        self.keys_refresh = keys_refresh
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._load_public_keys = True
        close = QPushButton('Close')
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        self.start('capabilities')

    def start(self, action):
        if self.worker is not None:
            return
        if action == 'generate' and not self.pin.text():
            self.status.setText('Enter the token USER PIN, then choose Refresh Keys or Generate Key.')
            self.pin.setFocus()
            return
        if action == 'generate' and not self.label.text().strip():
            self.status.setText('Enter a name for the new key.')
            self.label.setFocus()
            return
        values = dict(pin=self.pin.text(), label=self.label.text(), algorithm=self.algorithm.currentText())
        self.pin.clear()
        self.login.setEnabled(False)
        self.keys_refresh.setEnabled(False)
        self.refresh.setEnabled(False)
        self.generate.setEnabled(False)
        self.status.setText('Working… Please wait. Do not repeat the operation.')
        self.worker = KeyOperation(self.service, self.slot.slot_id, action, self, **values)
        self.worker.succeeded.connect(self.completed)
        self.worker.failed.connect(self.status.setText)
        self.worker.finished.connect(self.finished_operation)
        self.worker.start()

    def completed(self, result):
        if 'choices' in result:
            self.algorithm.addItems(result['choices'])
            self.status.setText('Enter your USER PIN and refresh to view keys.' if result['choices'] else 'No supported AES/RSA generation mechanism found. You can still refresh keys.')
        elif 'keys' in result:
            self.tabs.setCurrentIndex(0)
            rows = result['keys']
            self.table.setRowCount(len(rows))
            for row, key in enumerate(rows):
                for col, field in enumerate(('label', 'kind', 'algorithm', 'id')):
                    self.table.setItem(row, col, QTableWidgetItem(str(key[field])))
            self.table.resizeColumnsToContents()
            self.filter_keys()
            self.status.setText(result.get('message') or (f'{len(rows)} key objects visible. Enter USER PIN to include private keys.' if rows else 'No keys visible. Enter USER PIN and click Login / Show Keys, or open Generate Key to create one.'))
        else:
            self.status.setText(result['message'])

    def finished_operation(self):
        self.worker.deleteLater()
        self.worker = None
        self.login.setEnabled(True)
        self.keys_refresh.setEnabled(True)
        self.refresh.setEnabled(True)
        self.generate.setEnabled(self.algorithm.count() > 0)

        if self._load_public_keys:
            self._load_public_keys = False
            QTimer.singleShot(0, lambda: self.start('list') if self.isVisible() else None)

    def filter_keys(self):
        query = self.search.text().casefold().strip()
        for row in range(self.table.rowCount()):
            text = ' '.join(self.table.item(row, col).text() for col in range(4) if self.table.item(row, col))
            self.table.setRowHidden(row, query not in text.casefold())

    def reject(self):
        if self.worker is not None:
            self.status.setText('Please wait for the HSM operation to finish before closing.')
            return
        self.pin.clear()
        super().reject()

    def closeEvent(self, event):
        if self.worker is not None:
            event.ignore()
        else:
            self.pin.clear()
            super().closeEvent(event)
