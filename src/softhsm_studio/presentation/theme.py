APP_STYLESHEET = r"""
QWidget {
    background-color: #0f141b;
    color: #e7edf5;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}
QMainWindow { background-color: #0b1016; }
QFrame#Sidebar, QFrame#Panel {
    background-color: #141b24;
    border: 1px solid #24303d;
    border-radius: 12px;
}
QLabel#AppTitle {
    font-size: 22pt;
    font-weight: 700;
    color: #f5f8fc;
}
QLabel#Muted { color: #8fa0b3; }
QLabel#SectionTitle {
    font-size: 10.5pt;
    font-weight: 700;
    color: #c9d7e8;
}
QLabel#ProviderBadge {
    background-color: #123326;
    color: #8ff0bd;
    border: 1px solid #1f6b4c;
    border-radius: 8px;
    padding: 6px 10px;
}
QPushButton {
    background-color: #1d2835;
    border: 1px solid #324154;
    border-radius: 8px;
    padding: 9px 12px;
    text-align: left;
}
QPushButton:hover { background-color: #263547; border-color: #47617d; }
QPushButton:pressed { background-color: #17212b; }
QPushButton:disabled { color: #667384; background-color: #151b22; border-color: #202832; }
QPushButton#PrimaryButton {
    background-color: #2457d6;
    border-color: #3d70ea;
    color: white;
    font-weight: 700;
}
QPushButton#DangerButton { color: #ffb4b4; }
QTableWidget {
    background-color: #111821;
    alternate-background-color: #151e29;
    border: 1px solid #263342;
    border-radius: 10px;
    gridline-color: #22303e;
    selection-background-color: #1f4f9b;
    selection-color: white;
}
QHeaderView::section {
    background-color: #18222e;
    color: #aebed0;
    border: none;
    border-right: 1px solid #263342;
    border-bottom: 1px solid #263342;
    padding: 8px;
    font-weight: 700;
}
QLineEdit {
    background-color: #0f151d;
    border: 1px solid #334355;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #2d64eb;
}
QLineEdit:focus { border-color: #4d7bf0; }
QTextBrowser {
    background-color: #0f151d;
    border: 1px solid #263342;
    border-radius: 10px;
    padding: 8px;
}
QStatusBar { color: #8fa0b3; }
QToolTip { background-color: #1c2733; color: #eef3f8; border: 1px solid #3b4d61; }
"""
