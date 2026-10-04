from pathlib import Path
import sys
import pytest
from softhsm_studio.process_runtime import worker_command


def test_source_worker_uses_python_module(monkeypatch):
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert worker_command('snapshot')[1:] == ['-m', 'softhsm_studio.infrastructure.pkcs11.worker']
    assert worker_command('keys')[1:] == ['-m', 'softhsm_studio.infrastructure.pkcs11.key_worker']


def test_frozen_worker_uses_sibling_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path/'VirtualHsmStudio.exe'))
    (tmp_path/'HsmWorker.exe').write_bytes(b'test fixture')
    assert worker_command('keys') == [str(tmp_path/'HsmWorker.exe'), 'keys']


def test_missing_frozen_worker_reports_repair(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path/'VirtualHsmStudio.exe'))
    with pytest.raises(RuntimeError, match='Repair or reinstall'):
        worker_command('snapshot')


def test_unknown_worker_is_rejected():
    with pytest.raises(ValueError):
        worker_command('arbitrary-module')
