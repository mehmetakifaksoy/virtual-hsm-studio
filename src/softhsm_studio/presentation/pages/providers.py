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


class ProvidersPage(QWidget):
    load_module_requested = Signal()
    virtual_provider_requested = Signal()
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        heading = QLabel("Providers")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        description = QLabel("Connect to a PKCS#11 module or use the development-only Virtual HSM.")
        description.setObjectName("Muted")
        description.setWordWrap(True)
        layout.addWidget(description)

        actions = QHBoxLayout()
        self.load_module_button = QPushButton("Load PKCS#11 Module…")
        self.load_module_button.setObjectName("PrimaryButton")
        self.load_module_button.clicked.connect(self.load_module_requested)
        self.virtual_button = QPushButton("Use Virtual HSM")
        self.virtual_button.clicked.connect(self.virtual_provider_requested)
        self.refresh_button = QPushButton("Refresh Provider")
        self.refresh_button.clicked.connect(self.refresh_requested)
        actions.addWidget(self.load_module_button)
        actions.addWidget(self.virtual_button)
        actions.addWidget(self.refresh_button)
        actions.addStretch(1)
        layout.addLayout(actions)

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
        self.capabilities.setText("Capabilities · " + " · ".join(
            f"{name}: {'available' if supported else 'not supported'}"
            for name, supported in capabilities
        ))
