from __future__ import annotations
import argparse
import sys
from PySide6.QtWidgets import QApplication
from softhsm_studio.presentation.main_window import MainWindow
from softhsm_studio.presentation.theme import APP_STYLESHEET


def main() -> int:
    parser = argparse.ArgumentParser(description='DLL-backed HSM desktop tools')
    parser.add_argument('--tool', choices=('admin', 'key-manager'), default='admin')
    args, qt_args = parser.parse_known_args()
    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName('HSM Admin Tool' if args.tool == 'admin' else 'HSM Key Manager')
    app.setOrganizationName('VirtualHsmStudio')
    app.setApplicationVersion('0.3.0')
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow(tool=args.tool)
    window.show()
    return app.exec()
