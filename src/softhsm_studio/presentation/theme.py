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


APP_STYLESHEET += r"""
QWidget { font-size: 10pt; background-color: #f4f6fa; color: #18263a; }
QFrame#Sidebar { background-color: #13233d; border: none; border-radius: 14px; }
QLabel#BrandMark { color: #8caef7; font-size: 10pt; font-weight: 700; padding-bottom: 10px; }
QLabel#AppTitle { color: #ffffff; font-size: 22pt; font-weight: 700; }
QLabel#SidebarMuted { color: #a8b8cf; font-size: 9pt; }
QPushButton#NavigationButton { background-color: transparent; color: #b7c7df; border: none; padding: 13px 16px; border-radius: 8px; }
QPushButton#NavigationButton:hover { background-color: #223a5c; color: white; }
QPushButton#NavigationButton:checked { background-color: #315fce; color: white; font-weight: 700; }
QFrame#Panel { background-color: #f4f6fa; border: none; }
QLabel#PageTitle { font-size: 21pt; font-weight: 700; color: #172942; }
QFrame#ActionCard, QFrame#MetricCard { background-color: white; border: 1px solid #dee5ee; border-radius: 12px; }
QFrame#WelcomeCard { background-color: #eaf0ff; border: 1px solid #d1ddfa; border-radius: 12px; }
QLabel#Eyebrow { font-size: 9pt; font-weight: 700; color: #567197; }
QLabel#CardTitle { font-size: 15pt; font-weight: 700; color: #182e50; }
QLabel#MetricValue { font-size: 22pt; font-weight: 700; color: #254b91; }
QLabel#Feedback { background-color: white; border: 1px solid #dfe6ef; border-radius: 8px; padding: 9px; color: #53677f; }
QLabel#ProviderBadge { padding: 6px 10px; font-size: 9pt; }
QPushButton { padding: 10px 15px; border-radius: 7px; }
QCheckBox { background: transparent; spacing: 8px; }
"""

APP_STYLESHEET += r"""
QLabel { background: transparent; }
QLineEdit, QComboBox { background: white; }
QScrollArea { background: transparent; border: none; }
QLabel#ProviderBadge[connected="false"] { color: #53677f; background: #e7edf5; border-color: #d4deea; }
"""


# Shared visual polish for the light console and dark navigation.
APP_STYLESHEET += r"""
QFrame#Sidebar { background: #14243b; border-radius: 16px; }
QLabel#AppTitle { font-size: 19pt; }
QLabel#PageTitle { font-size: 23pt; }
QLabel#CardTitle { font-size: 16pt; }
QFrame#ActionCard, QFrame#MetricCard { border-color: #e0e6ee; border-radius: 14px; }
QFrame#WelcomeCard { background: #ffffff; border: 1px solid #d5e0f0; border-radius: 14px; }
QPushButton { min-height: 22px; padding: 10px 18px; border-radius: 8px; }
QPushButton#NavigationButton { padding: 14px 18px; }
QPushButton#NavigationButton:checked { background: #285bcc; }
QPushButton#PrimaryButton { background: #285bcc; border-color: #285bcc; }
QPushButton#PrimaryButton:hover { background: #204cad; border-color: #204cad; }
QPushButton:checked { background: #eaf0fb; border-color: #9bb4e4; }
QGroupBox { background: #ffffff; border: 1px solid #dfe6ef; border-radius: 10px; margin-top: 16px; padding: 18px 12px 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #50657f; }
QHeaderView::section { background: #f0f4f9; padding: 13px; color: #526781; }
QTableWidget { alternate-background-color: #f8fafc; selection-background-color: #e5edfc; }
QScrollBar:vertical { background: #edf1f6; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #b8c5d6; border-radius: 5px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLineEdit:read-only { background: #f8fafc; border-color: #e2e8f0; }
"""
