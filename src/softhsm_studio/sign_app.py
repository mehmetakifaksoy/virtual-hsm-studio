"""Standalone file signing client; verification requires no HSM connection."""
import argparse
import base64
import sys
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog
from softhsm_studio.key_manager import KeyManagerWindow
from softhsm_studio.application.signing import signing_operation, verify_files
from softhsm_studio.presentation.theme import APP_STYLESHEET


class SignTask(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, request, parent):
        super().__init__(parent)
        self.request = request

    def run(self):
        try:
            self.succeeded.emit(signing_operation(self.request))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.request.clear()


class SignDialog(QDialog):
    def __init__(self, service, slot, parent):
        super().__init__(parent)
        self.service, self.slot = service, slot
        self.worker = None
        self.result_data = None
        self.setWindowTitle('Sign a file · RSA / SHA-256')
        self.resize(650, 480)
        layout = QVBoxLayout(self)
        note = QLabel('1. Enter USER PIN and load signing keys.\n2. Select a key and file, re-enter your PIN, then sign.\n3. Save the signature and public key for independent verification.\nPOC limit: 16 MiB. This creates a detached signature, not a PDF signature.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.pin = QLineEdit()
        self.pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin.setPlaceholderText('USER PIN — cleared after each operation')
        layout.addWidget(self.pin)
        self.load = QPushButton('Load RSA Signing Keys')
        self.load.clicked.connect(lambda: self.start('list'))
        layout.addWidget(self.load)
        self.keys = QComboBox()
        layout.addWidget(self.keys)
        self.file = QLineEdit()
        self.file.setReadOnly(True)
        self.file.setPlaceholderText('No document selected')
        layout.addWidget(self.file)
        self.choose = QPushButton('Choose File…')
        self.choose.clicked.connect(self.choose_file)
        layout.addWidget(self.choose)
        self.sign = QPushButton('Sign File')
        self.sign.setObjectName('PrimaryButton')
        self.sign.clicked.connect(lambda: self.start('sign'))
        layout.addWidget(self.sign)
        self.export = QPushButton('Export Public Key…')
        self.export.clicked.connect(lambda: self.start('export'))
        layout.addWidget(self.export)
        self.save = QPushButton('Save Signature…')
        self.save.setEnabled(False)
        self.save.clicked.connect(self.save_signature)
        layout.addWidget(self.save)
        self.status = QLabel('Private key material stays inside the HSM.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def choose_file(self):
        name, _ = QFileDialog.getOpenFileName(self, 'Select document')
        if name:
            self.file.setText(name)
            self.result_data = None
            self.save.setEnabled(False)

    def start(self, action):
        if self.worker:
            return
        if not self.pin.text():
            self.status.setText('Enter USER PIN. No automatic login retry is performed.')
            return
        if action != 'list' and self.keys.currentData() is None:
            self.status.setText('Load and select an RSA signing key first.')
            return
        if action == 'sign' and not self.file.text():
            self.status.setText('Choose a file first.')
            return
        request = dict(module=str(self.service.provider.module_path), slot_id=self.slot.slot_id,
                       pin=self.pin.text(), action=action, key_id=self.keys.currentData(), file=self.file.text())
        self.pin.clear()
        self.result_data = None
        self.save.setEnabled(False)
        self.status.setText('Working…')
        for widget in (self.load, self.sign, self.export, self.choose, self.keys, self.pin):
            widget.setEnabled(False)
        self.worker = SignTask(request, self)
        self.worker.succeeded.connect(self.completed)
        self.worker.failed.connect(self.status.setText)
        self.worker.finished.connect(self._operation_finished)
        self.worker.start()

    def completed(self, result):
        if 'keys' in result:
            self.keys.clear()
            for row in result['keys']:
                self.keys.addItem(f"{row['label']} · {row['id']}", row['id'])
            self.status.setText(f'{self.keys.count()} RSA signing keys found. Enter PIN again to sign or export the public key.')
        else:
            self.result_data = result
            self.save.setEnabled('signature' in result)
            if 'signature' in result:
                self.status.setText('Signature created and verified. Save Signature, then save the matching public key.\nSHA-256: '+result['sha256'])
                self.save_public_key()
            else:
                self.save_public_key()

    def write_output(self, title, data, extension):
        name, _ = QFileDialog.getSaveFileName(self, title, '', extension)
        if not name:
            return
        try:
            if self.file.text() and Path(name).resolve() == Path(self.file.text()).resolve():
                raise ValueError('Choose a destination different from the original document.')
            Path(name).write_bytes(data)
            self.status.setText(f'Saved: {name}')
        except (OSError, ValueError):
            self.status.setText('Could not save. Choose a writable destination different from the original document.')

    def save_signature(self):
        if self.result_data and 'signature' in self.result_data:
            self.write_output('Save detached signature', base64.b64decode(self.result_data['signature']), 'Signature (*.sig)')

    def save_public_key(self):
        self.write_output('Save public key (PEM)', self.result_data['public_key'].encode('ascii'), 'Public key (*.pem)')

    def _operation_finished(self):
        self.worker.deleteLater()
        self.worker = None
        for widget in (self.load, self.sign, self.export, self.choose, self.keys, self.pin):
            widget.setEnabled(True)

    def reject(self):
        if self.worker:
            self.status.setText('Wait for the HSM operation to finish before closing.')
            return
        self.pin.clear()
        super().reject()

    def closeEvent(self, event):
        if self.worker:
            event.ignore()
        else:
            self.pin.clear()
            super().closeEvent(event)


class SignWindow(KeyManagerWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('HSM Sign & Verify')
        layout = self.centralWidget().layout()
        layout.itemAt(0).widget().setText('Sign & Verify')
        layout.itemAt(1).widget().setText('Sign a file using an existing HSM RSA key. Verify a signature independently with an exported public key.\nRSA PKCS#1 v1.5 / SHA-256 · Detached signatures · 16 MiB POC limit')
        self.demo_button.hide()
        self.open_button.setText('Sign with Selected Token…')
        verify = QPushButton('Verify File Signature… (No HSM Required)')
        verify.clicked.connect(self.verify)
        layout.insertWidget(layout.count()-1, verify)
        self.status.setText('Connect SoftHSM2 or a vendor PKCS#11 module to sign. The local metadata simulator cannot sign.')

    def open_keys(self):
        slot = self.tokens.currentData()
        if slot is not None and self.worker is None:
            SignDialog(self.service, slot, self).exec()

    def verify(self):
        files = []
        for title, pattern in [('Original document', 'All files (*)'), ('Detached signature', 'Signature (*.sig);;All files (*)'), ('RSA public key', 'Public key (*.pem)')]:
            name, _ = QFileDialog.getOpenFileName(self, title, '', pattern)
            if not name:
                return
            files.append(name)
        try:
            valid = verify_files(*files)
            self.status.setText('VALID — The signature matches this file and public key.' if valid else
                                'INVALID — The file, signature or public key does not match.')
        except Exception:
            self.status.setText('Verification could not run. Check the file size (16 MiB maximum), signature and RSA public key PEM.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    app.setApplicationName('HSM Sign & Verify')
    app.setStyleSheet(APP_STYLESHEET)
    window = SignWindow()
    window.show()
    if args.smoke_test:
        QTimer.singleShot(300, window.close)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
