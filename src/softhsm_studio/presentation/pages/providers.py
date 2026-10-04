from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from softhsm_studio.domain.models import ProviderInfo
from ..widgets.cards import ActionCard


class ProvidersPage(QWidget):
    load_module_requested = Signal()
    virtual_provider_requested = Signal()
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        heading = QLabel("Connections")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        description = QLabel("Connect to a PKCS#11 module or use the development-only Virtual HSM.")
        description.setObjectName("Muted")
        description.setWordWrap(True)
        layout.addWidget(description)

        cards = QHBoxLayout()
        virtual = ActionCard("LOCAL DEMO · NO HARDWARE", "Virtual HSM",
            "A persistent local simulator. Explore slots, tokens and sessions without hardware. Key generation creates metadata only.")
        self.virtual_button = QPushButton("Start Demo")
        self.virtual_button.setObjectName("PrimaryButton")
        self.virtual_button.clicked.connect(self.virtual_provider_requested)
        virtual.content.addWidget(self.virtual_button)
        module = ActionCard("REAL HSM / EXTERNAL PROVIDER", "Vendor PKCS#11 module",
            "Connect a vendor module matching the application's architecture. Available operations depend on the provider.")
        self.load_module_button = QPushButton("Connect HSM…")
        self.load_module_button.clicked.connect(self.load_module_requested)
        module.content.addWidget(self.load_module_button)
        cards.addWidget(virtual)
        cards.addWidget(module)
        layout.addLayout(cards)
        self.refresh_button = QPushButton("Refresh connected provider")
        self.refresh_button.clicked.connect(self.refresh_requested)
        layout.addWidget(self.refresh_button)

        form = QFormLayout()
        self.name = self._value_field()
        self.kind = self._value_field()
        self.manufacturer = self._value_field()
        self.version = self._value_field()
        self.module_path = self._value_field()
        self.module_path.setToolTip("Provider module or virtual-state path")
        form.addRow("Name", self.name)
        form.addRow("Type", self.kind)
        form.addRow("Manufacturer", self.manufacturer)
        form.addRow("Version", self.version)
        form.addRow("Module / state path", self.module_path)
        layout.addLayout(form)
        self.capabilities = QLabel()
        self.capabilities.setObjectName("Muted")
        self.capabilities.setWordWrap(True)
        layout.addWidget(self.capabilities)
        layout.addStretch(1)

    @staticmethod
    def _value_field() -> QLineEdit:
        field = QLineEdit()
        field.setReadOnly(True)
        field.setClearButtonEnabled(False)
        return field

    def set_provider(self, provider: ProviderInfo, connected: bool, busy: bool) -> None:
        self.name.setText(provider.name if connected else "Not connected")
        self.kind.setText(provider.kind.value if connected else "—")
        self.manufacturer.setText(provider.manufacturer if connected else "—")
        self.version.setText(provider.version if connected else "—")
        self.module_path.setText(provider.module_path if connected else "—")
        self.load_module_button.setEnabled(not busy)
        self.virtual_button.setEnabled(not busy)
        self.refresh_button.setEnabled(connected and not busy)

    def set_capabilities(self, service) -> None:
        capabilities = (
            ("Sessions", service.supports_sessions),
            ("Objects", service.supports_objects),
            ("Mechanisms", service.supports_mechanisms),
            ("Virtual administration", service.supports_virtual_admin),
        )
        self.capabilities.setText("Application features · " + " · ".join(
            f"{name}: {'available' if supported else 'not available in this application'}"
            for name, supported in capabilities
        ))
