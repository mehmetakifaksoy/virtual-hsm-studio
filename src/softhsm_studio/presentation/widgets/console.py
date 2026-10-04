"""Console shell layout; HSM operations remain outside widgets."""
from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                              QStackedWidget, QVBoxLayout, QWidget, QScrollArea)
from ..pages import DashboardPage, ProvidersPage, SessionsPage, SlotsPage
from softhsm_studio import __version__

def build_console(self) -> None:
    root = QWidget()
    root_layout = QHBoxLayout(root)
    root_layout.setContentsMargins(16, 16, 16, 16)
    root_layout.setSpacing(14)

    sidebar = QFrame()
    sidebar.setObjectName("Sidebar")
    sidebar.setFixedWidth(224)
    side_layout = QVBoxLayout(sidebar)
    side_layout.setContentsMargins(22, 24, 22, 24)
    side_layout.setSpacing(10)

    brand = QLabel("HSM / STUDIO")
    brand.setObjectName("BrandMark")
    side_layout.addWidget(brand)
    title = QLabel("Virtual HSM\nStudio")
    title.setObjectName("AppTitle")
    title.setWordWrap(True)
    subtitle = QLabel("MANAGEMENT CONSOLE")
    subtitle.setObjectName("SidebarMuted")
    subtitle.setWordWrap(True)
    side_layout.addWidget(title)
    side_layout.addWidget(subtitle)
    side_layout.addSpacing(12)

    self.navigation: list[QPushButton] = []
    for index, page_name in enumerate(self.PAGE_NAMES):
        button = QPushButton(page_name)
        button.setObjectName("NavigationButton")
        button.setCheckable(True)
        button.clicked.connect(partial(self._navigate, index))
        self.navigation.append(button)
        side_layout.addWidget(button)

    side_layout.addStretch(1)
    warning = QLabel(
        "Virtual mode is for development and testing. It is not a hardware security boundary."
    )
    warning.setObjectName("SidebarMuted")
    warning.setWordWrap(True)
    side_layout.addWidget(warning)
    version = QLabel(f"POC PREVIEW  ·  {__version__}")
    version.setObjectName("SidebarMuted")
    side_layout.addWidget(version)

    content = QFrame()
    content.setObjectName("Panel")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(22, 24, 22, 24)
    content_layout.setSpacing(12)

    header = QHBoxLayout()
    self.provider_badge = QLabel("Not connected")
    self.provider_badge.setObjectName("ProviderBadge")
    self.provider_title = QLabel("HSM Management Console")
    self.provider_title.setStyleSheet("font-size: 16pt; font-weight: 700;")
    self.slot_count = QLabel("0 slots")
    self.slot_count.setObjectName("Muted")
    header.addWidget(self.provider_badge)
    header.addWidget(self.provider_title)
    header.addStretch(1)
    header.addWidget(self.slot_count)
    content_layout.addLayout(header)

    self.provider_detail = QLabel()
    self.provider_detail.setObjectName("Muted")
    self.provider_detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.provider_detail.setWordWrap(True)
    content_layout.addWidget(self.provider_detail)
    self.provider_detail.hide()

    self.feedback = QLabel()
    self.feedback.setObjectName("Feedback")
    self.feedback.setWordWrap(True)
    content_layout.addWidget(self.feedback)
    self.feedback.hide()

    self.dashboard_page = DashboardPage()
    self.providers_page = ProvidersPage()
    self.slots_page = SlotsPage()
    self.sessions_page = SessionsPage()
    self.page_stack = QStackedWidget()
    for page in (
        self.dashboard_page,
        self.providers_page,
        self.slots_page,
        self.sessions_page,
    ):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        self.page_stack.addWidget(scroll)
    content_layout.addWidget(self.page_stack, 1)

    root_layout.addWidget(sidebar)
    root_layout.addWidget(content, 1)
    self.setCentralWidget(root)
    self.statusBar().showMessage(self._last_status)

    self.dashboard_page.navigate_requested.connect(self._navigate)
    self.dashboard_page.virtual_provider_requested.connect(self._switch_to_virtual)
    self.dashboard_page.load_module_requested.connect(self._choose_module)
    self.providers_page.load_module_requested.connect(self._choose_module)
    self.providers_page.virtual_provider_requested.connect(self._switch_to_virtual)
    self.providers_page.refresh_requested.connect(self._refresh_provider)
    self.slots_page.slot_selected.connect(self._slot_selection_changed)
    self.slots_page.create_slot_requested.connect(self._create_slot)
    self.slots_page.initialize_token_requested.connect(self._initialize_token)
    self.slots_page.clear_token_requested.connect(self._clear_token)
    self.slots_page.delete_slot_requested.connect(self._delete_slot)
    self.sessions_page.refresh_requested.connect(self._refresh_sessions)
    self.sessions_page.open_session_requested.connect(self._open_session)
    self.sessions_page.close_session_requested.connect(self._close_session)
    self.sessions_page.login_requested.connect(self._login_session)
    self.sessions_page.logout_requested.connect(self._logout_session)
    self._navigate(0)
