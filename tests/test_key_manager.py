import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from softhsm_studio.key_manager import KeyManagerWindow
from softhsm_studio.infrastructure.virtual_hsm import VirtualHsmProvider
from softhsm_studio.application.keys import slot_keys


def test_key_manager_uses_prepared_tokens_and_clears_demo_pin(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = KeyManagerWindow()
    provider = VirtualHsmProvider(tmp_path / 'state.json')
    provider.connect()
    window.service.activate_connected(provider)
    window.service.initialize_virtual_token(0, 'Test token', '112233', '445566')
    window.connected(provider, provider.list_slots())
    assert window.tokens.count() == 1
    slot = window.tokens.currentData()
    result = slot_keys(window.service, slot.slot_id, 'generate', pin='445566', algorithm='RSA-2048', label='demo-signing')
    assert result['keys']
    from softhsm_studio.presentation.key_dialog import SlotKeysDialog
    dialog = SlotKeysDialog(window.service, slot, window)
    dialog.show()
    for _ in range(300):
        QTest.qWait(10)
        if dialog.worker is None:
            break
    assert dialog.worker is None
    dialog.pin.setText('445566')
    dialog.start('list')
    assert dialog.pin.text() == ''
    for _ in range(300):
        QTest.qWait(10)
        if dialog.worker is None:
            break
    assert dialog.worker is None
    assert dialog.table.rowCount() > 0
    dialog.reject()
    window.close()
