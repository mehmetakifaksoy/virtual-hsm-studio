"""Shared configuration for the two DLL-backed desktop tools."""
import os
from pathlib import Path
from PySide6.QtCore import QSettings
from softhsm_studio.domain.models import ProviderInfo, ProviderKind
from softhsm_studio.domain.ports import HsmProvider


class DisconnectedProvider(HsmProvider):
    @property
    def info(self):
        return ProviderInfo(name='No HSM connected', kind=ProviderKind.PKCS11,
                            description='Load a PKCS#11 DLL to begin.')

    def connect(self):
        pass

    def list_slots(self):
        return []


def prepare_module(path):
    """Both tools use the same persistent SoftHSM token directory."""
    path = Path(path).resolve()
    if 'softhsm' in path.name.lower() and not os.environ.get('SOFTHSM2_CONF'):
        root = Path(__file__).resolve().parents[2] / '.hsm-data'
        tokens = root / 'tokens'
        tokens.mkdir(parents=True, exist_ok=True)
        config = root / 'softhsm2.conf'
        if not config.exists():
            config.write_text(f'directories.tokendir = {tokens.as_posix()}\nobjectstore.backend = file\nlog.level = ERROR\nslots.removable = false\n', encoding='utf-8')
        os.environ['SOFTHSM2_CONF'] = str(config)
    return path


def settings():
    return QSettings('VirtualHsmStudio', 'DllTools')
