APP_STYLESHEET = r"""
QWidget {
    background-color: #f3f6fa;
    color: #172a42;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QMainWindow { background-color: #edf2f8; }
QFrame#Sidebar { background-color: #e5edf7; border: 1px solid #d0dbea; border-radius: 12px; }
QFrame#Panel { background-color: white; border: 1px solid #d9e2ed; border-radius: 12px; }
QFrame#MetricCard {
    background-color: white;
    border: 1px solid #d9e2ed;
    border-radius: 10px;
}
QLabel { background: transparent; }
QLabel#AppTitle { font-size: 18pt; font-weight: 700; color: #142e53; }
QLabel#PageTitle {
    font-size: 17pt;
    font-weight: 700;
    color: #142e53;
}
QLabel#MetricValue {
    font-size: 20pt;
    font-weight: 700;
    color: #2463c6;
}
QLabel#Muted { color: #53677f; }
QLabel#SectionTitle { font-size: 11pt; font-weight: 700; color: #24456a; }
QLabel#ProviderBadge { background-color: #e1f4e9; color: #17663d; border: 1px solid #abd4bb; border-radius: 8px; padding: 8px; }
QLabel#Feedback { background-color: #eaf2ff; color: #214d86; border: 1px solid #c6d9f4; border-radius: 8px; padding: 12px; }
QPushButton { background-color: white; border: 1px solid #bacadd; border-radius: 7px; padding: 10px 14px; color: #234466; }
QPushButton:hover { background-color: #eaf2ff; border-color: #7298c7; }
QPushButton:pressed { background-color: #d8e7fa; }
QPushButton:focus { border: 2px solid #2869cf; }
QPushButton#NavigationButton {
    text-align: left;
}
QPushButton#NavigationButton:checked {
    background-color: #2463c6;
    color: white;
    border-color: #2463c6;
    font-weight: 700;
}
QPushButton:disabled { color: #8492a5; background-color: #edf1f5; border-color: #dbe2ea; }
QPushButton#PrimaryButton { background-color: #2463c6; color: white; border-color: #2463c6; font-weight: 700; }
QPushButton#PrimaryButton:hover { background-color: #194f9f; }
QPushButton#PrimaryButton:disabled { background-color: #dce5f2; color: #879bb7; border-color: #dce5f2; }
QPushButton#DangerButton { color: #af303d; background-color: #fff5f5; border-color: #e4b9bf; }
QTableWidget { background-color: white; alternate-background-color: #f4f7fc; border: 1px solid #d5dfec; border-radius: 8px; gridline-color: #e4ebf4; selection-background-color: #dceaff; selection-color: #123e79; }
QHeaderView::section { background-color: #eaf0f8; color: #355477; border: none; border-bottom: 1px solid #d0dbea; padding: 10px; font-weight: 700; }
QLineEdit, QComboBox { background-color: white; border: 1px solid #b9cadd; border-radius: 6px; padding: 9px; selection-background-color: #2463c6; selection-color: white; }
QLineEdit:focus { border: 2px solid #2463c6; }
QTextBrowser { background-color: white; border: 1px solid #d5dfec; border-radius: 8px; padding: 12px; }
QTabWidget::pane { background-color: white; border: 1px solid #d2deed; border-radius: 8px; }
QTabBar::tab { padding: 12px 18px; background-color: #e8eef7; color: #415d7f; border: 1px solid #d2deed; }
QTabBar::tab:selected { background-color: #2463c6; color: white; }
QStatusBar { color: #53677f; }
QToolTip { background-color: #173456; color: white; border: 1px solid #345a85; padding: 6px; }
QSplitter::handle { background-color: #e3eaf3; }
"""
