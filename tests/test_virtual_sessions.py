from pathlib import Path

import pytest

from softhsm_studio.domain.errors import (
    AuthenticationError,
    SessionError,
    ValidationError,
)
from softhsm_studio.domain.models import (
    SessionRole,
    SessionState,
)
from softhsm_studio.infrastructure.virtual_hsm import (
    VirtualHsmProvider,
)


def ready_provider(
    tmp_path: Path,
) -> VirtualHsmProvider:
    provider = VirtualHsmProvider(
        tmp_path / "state.json"
    )

    provider.connect()

    provider.initialize_token(
        0,
        "DEV_TOKEN",
        "112233",
        "445566",
    )

    return provider


def test_open_rw_session_starts_public(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    session = provider.open_session(
        0,
        read_write=True,
    )

    assert (
        session.role
        is SessionRole.PUBLIC
    )

    assert (
        session.state
        is SessionState.RW_PUBLIC_SESSION
    )

    assert (
        session.authenticated
        is False
    )


def test_user_login_updates_all_sessions_for_slot(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    provider.open_session(
        0
    )

    rw = provider.open_session(
        0,
        read_write=True,
    )

    logged_in = provider.login(
        rw.session_id,
        SessionRole.USER,
        "445566",
    )

    assert (
        logged_in.state
        is SessionState.RW_USER_FUNCTIONS
    )

    sessions = provider.list_sessions(
        0
    )

    assert (
        sessions[0].state
        is SessionState.RO_USER_FUNCTIONS
    )

    assert (
        sessions[1].state
        is SessionState.RW_USER_FUNCTIONS
    )

    assert all(
        item.role
        is SessionRole.USER
        for item in sessions
    )


def test_wrong_pin_is_rejected(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    session = provider.open_session(
        0,
        read_write=True,
    )

    with pytest.raises(
        AuthenticationError
    ):
        provider.login(
            session.session_id,
            SessionRole.USER,
            "wrong-pin",
        )


def test_so_requires_rw_and_no_ro_sessions(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    ro = provider.open_session(
        0
    )

    with pytest.raises(
        SessionError
    ):
        provider.login(
            ro.session_id,
            SessionRole.SO,
            "112233",
        )

    rw = provider.open_session(
        0,
        read_write=True,
    )

    with pytest.raises(
        SessionError
    ):
        provider.login(
            rw.session_id,
            SessionRole.SO,
            "112233",
        )


def test_so_login_and_logout(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    session = provider.open_session(
        0,
        read_write=True,
    )

    authenticated = provider.login(
        session.session_id,
        SessionRole.SO,
        "112233",
    )

    assert (
        authenticated.role
        is SessionRole.SO
    )

    assert (
        authenticated.state
        is SessionState.RW_SO_FUNCTIONS
    )

    public = provider.logout(
        session.session_id
    )

    assert (
        public.role
        is SessionRole.PUBLIC
    )

    assert (
        public.state
        is SessionState.RW_PUBLIC_SESSION
    )


def test_close_last_session_clears_login_state(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    session = provider.open_session(
        0,
        read_write=True,
    )

    provider.login(
        session.session_id,
        SessionRole.USER,
        "445566",
    )

    provider.close_session(
        session.session_id
    )

    new_session = provider.open_session(
        0,
        read_write=True,
    )

    assert (
        new_session.role
        is SessionRole.PUBLIC
    )


def test_token_changes_require_closed_sessions(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    provider.open_session(
        0
    )

    with pytest.raises(
        SessionError
    ):
        provider.clear_token(
            0
        )


def test_open_session_requires_initialized_token(
    tmp_path: Path,
) -> None:
    provider = VirtualHsmProvider(
        tmp_path / "state.json"
    )

    provider.connect()

    with pytest.raises(
        ValidationError
    ):
        provider.open_session(
            0
        )


def test_mechanisms_do_not_advertise_unimplemented_crypto(
    tmp_path: Path,
) -> None:
    provider = ready_provider(
        tmp_path
    )

    assert (
        provider.list_mechanisms(0)
        == []
    )