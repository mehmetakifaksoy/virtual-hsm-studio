"""Session action handlers; only HsmService handles provider access."""
from softhsm_studio.domain.models import SessionRole


class SessionActions:
    def _refresh_sessions(self) -> None:
        if not self.service.supports_sessions:
            self._show_error("The active provider does not support session management.")
            return
        try:
            self.sessions = self.service.sessions()
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.sessions_page.set_data(
            self.slots,
            self.sessions,
            True,
            self._busy,
        )
        self._update_dashboard()

    def _open_session(self, slot_id: int, read_write: bool) -> None:
        try:
            self.service.open_session(slot_id, read_write=read_write)
            self._refresh_sessions()
            self._set_status(f"Opened a session on slot {slot_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _close_session(self, session_id: int) -> None:
        try:
            self.service.close_session(session_id)
            self._refresh_sessions()
            self._set_status(f"Closed session {session_id}")
        except Exception as exc:
            self._show_error(str(exc))

    def _login_session(self, session_id: int, role: str, pin: str) -> None:
        try:
            if role == SessionRole.SO.value.upper():
                self.service.login_so(session_id, pin)
            else:
                self.service.login_user(session_id, pin)
        except Exception:
            self._show_error("Login failed. Check the role, session access and PIN. Avoid repeated PIN attempts.")
        finally:
            pin = ""
        self._refresh_sessions()

    def _logout_session(self, session_id: int) -> None:
        try:
            self.service.logout(session_id)
            self._refresh_sessions()
            self._set_status(f"Logged out session {session_id}")
        except Exception as exc:
            self._show_error(str(exc))
