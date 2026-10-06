from __future__ import annotations
import argparse
import sys
from softhsm_studio import __version__
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from softhsm_studio.presentation.main_window import MainWindow
from softhsm_studio.presentation.theme import APP_STYLESHEET


def main() -> int:
    parser = argparse.ArgumentParser(description='Virtual HSM Studio management console')
    parser.add_argument('--tool', choices=('admin', 'key-manager'), default='admin')
    parser.add_argument('--smoke-test', action='store_true', help=argparse.SUPPRESS)
    args, qt_args = parser.parse_known_args()
    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName('HSM Admin Tool' if args.tool == 'admin' else 'HSM Key Manager')
    app.setOrganizationName('VirtualHsmStudio')
    app.setApplicationVersion(__version__)
    app.setStyleSheet(APP_STYLESHEET)
    if args.tool == 'key-manager':
        from softhsm_studio.key_manager import KeyManagerWindow
        window = KeyManagerWindow()
    else:
        window = MainWindow(tool=args.tool)
    window.show()
    if args.smoke_test:
        if args.tool == 'key-manager':
            QTimer.singleShot(300, window.close)
        else:
            from softhsm_studio.smoke import run_smoke
            QTimer.singleShot(100, lambda: run_smoke(window, app))
    return app.exec()
