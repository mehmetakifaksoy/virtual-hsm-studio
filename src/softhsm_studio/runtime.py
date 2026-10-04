"""Shared configuration for the two DLL-backed desktop tools."""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QSettings
from softhsm_studio.domain.models import ProviderInfo, ProviderKind
from softhsm_studio.domain.ports import HsmProvider


class DisconnectedProvider(HsmProvider):
    @property
    def info(self):
        return ProviderInfo(name='No HSM connected', kind=ProviderKind.PKCS11,
                            description='Start a Virtual HSM workspace or connect your PKCS#11 module.')

    def connect(self):
        pass

    def list_slots(self):
        return []


def prepare_module(path):
    """Both tools use the same persistent SoftHSM token directory."""
    path = Path(path).resolve()
    if 'softhsm' in path.name.lower() and not os.environ.get('SOFTHSM2_CONF'):
        source_root = Path(__file__).resolve().parents[2] / '.hsm-data'
        root = source_root if not getattr(sys, 'frozen', False) and source_root.exists() else user_data_dir() / 'softhsm'
        tokens = root / 'tokens'
        tokens.mkdir(parents=True, exist_ok=True)
        config = root / 'softhsm2.conf'
        if not config.exists():
            config.write_text(f'directories.tokendir = {tokens.as_posix()}\nobjectstore.backend = file\nlog.level = ERROR\nslots.removable = false\n', encoding='utf-8')
        os.environ['SOFTHSM2_CONF'] = str(config)
    return path


def settings():
    return QSettings('VirtualHsmStudio', 'DllTools')


def user_data_dir() -> Path:
    """Writable per-user data, never the installed application directory."""
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "VirtualHsmStudio"
    return Path.home() / ".local/share/virtual-hsm-studio"
