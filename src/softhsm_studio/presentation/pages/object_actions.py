"""Object discovery actions routed through the application service."""

from softhsm_studio.domain.models import ObjectClass


class ObjectActions:
    def _load_objects(
        self,
        session_id: int,
        object_class: ObjectClass | None,
    ) -> None:
        if not self.service.supports_objects:
            self.objects_page.set_objects(
                [],
                "The active provider does not support object discovery.",
            )
            return
        try:
            objects = self.service.objects(session_id, object_class)
        except Exception as exc:
            self.objects_page.set_objects([], f"Could not load object metadata: {exc}")
            self._show_error(f"Could not load objects for session {session_id}: {exc}")
            return
        self.objects_page.set_objects(objects)
