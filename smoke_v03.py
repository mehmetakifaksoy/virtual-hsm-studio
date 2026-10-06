from pathlib import Path
from tempfile import TemporaryDirectory

from softhsm_studio.application.service import HsmService
from softhsm_studio.infrastructure.virtual_hsm.provider import (
    VirtualHsmProvider,
)


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "virtual_hsm.json"

        provider = VirtualHsmProvider(state_path)
        service = HsmService(provider)

        print("Provider:")
        print(service.provider_info)
        print()

        print("Initial slots:")
        for slot in service.slots():
            print(slot)
        print()

        print("Initializing token in Slot 0...")

        service.initialize_virtual_token(
            slot_id=0,
            label="DEV_TOKEN",
            so_pin="112233",
            user_pin="445566",
        )

        print("Token initialized.")
        print()

        print("Opening RW session...")

        session = service.open_session(
            slot_id=0,
            read_write=True,
        )

        print("Session opened:")
        print(session)
        print()

        print("Logging in as USER...")

        session = service.login_user(
            session.session_id,
            "445566",
        )

        print("Authenticated session:")
        print(session)
        print()

        print("Active sessions:")

        for active_session in service.sessions():
            print(active_session)

        print()

        print("Visible objects:")
        objects = service.objects(
            session.session_id
        )

        print(objects)
        print()

        print("Mechanisms:")
        mechanisms = service.mechanisms(0)

        print(mechanisms)
        print()

        print("Logging out...")

        session = service.logout(
            session.session_id
        )

        print(session)
        print()

        print("Closing session...")

        service.close_session(
            session.session_id
        )

        print(
            "Remaining sessions:",
            service.sessions(),
        )

        service.close()

        print()
        print("v0.3 smoke test completed successfully.")


if __name__ == "__main__":
    main()