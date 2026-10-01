from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from softhsm_studio.presentation.main_window import MainWindow
from softhsm_studio.presentation.theme import APP_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SoftHSM Studio")
    app.setOrganizationName("SoftHSM Studio")
    app.setApplicationVersion("0.2.0")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec()
