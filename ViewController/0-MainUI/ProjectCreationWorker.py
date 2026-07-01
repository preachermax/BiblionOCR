from PyQt5 import QtCore as qtc


class ProjectCreationWorker(qtc.QObject):
    progress = qtc.pyqtSignal(int)
    finished = qtc.pyqtSignal(object)
    error = qtc.pyqtSignal(str)

    SUBSCRIBED_EVENTS = (
        "existing_project_removed",
        "validation_passed",
        "provenance_captured",
        "ris_generated",
        "project_structure_progress",
        "project_structure_created",
        "filesystem_written",
        "project_registered",
        "project_created",
    )

    EVENT_PROGRESS = {
        "existing_project_removed": 10,
        "validation_passed": 20,
        "provenance_captured": 45,
        "ris_generated": 65,
        "project_structure_created": 89,
        "filesystem_written": 90,
        "project_registered": 95,
        "project_created": 100,
    }

    STRUCTURE_PROGRESS_START = 66
    STRUCTURE_PROGRESS_END = 88

    def __init__(self, engine, payload):
        super().__init__()
        self.engine = engine
        self.payload = payload
        self._event_bus = getattr(engine, "event_bus", None)
        self._subscribed_events = []

    def run(self):
        try:
            self._subscribe_progress_events()
            self.progress.emit(5)

            result = self.engine.create_project(self.payload)

            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self._unsubscribe_progress_events()

    def _subscribe_progress_events(self):
        if self._event_bus is None or not hasattr(self._event_bus, "subscribe"):
            return

        for event_name in self.SUBSCRIBED_EVENTS:
            self._event_bus.subscribe(event_name, self._handle_engine_event)
            self._subscribed_events.append(event_name)

    def _unsubscribe_progress_events(self):
        if self._event_bus is None or not hasattr(self._event_bus, "unsubscribe"):
            self._subscribed_events.clear()
            return

        for event_name in self._subscribed_events:
            self._event_bus.unsubscribe(event_name, self._handle_engine_event)
        self._subscribed_events.clear()

    def _handle_engine_event(self, event):
        event_name = event.get("event")
        if event_name == "project_structure_progress":
            progress_value = self._map_structure_progress(event.get("metadata") or {})
        else:
            progress_value = self.EVENT_PROGRESS.get(event_name)

        if progress_value is not None:
            self.progress.emit(progress_value)

    def _map_structure_progress(self, metadata):
        bytes_total = metadata.get("bytes_total") or 0
        bytes_completed = metadata.get("bytes_completed") or 0

        if bytes_total > 0:
            ratio = max(0.0, min(1.0, bytes_completed / bytes_total))
            span = self.STRUCTURE_PROGRESS_END - self.STRUCTURE_PROGRESS_START
            return self.STRUCTURE_PROGRESS_START + int(round(span * ratio))

        total = metadata.get("total") or 0
        completed = metadata.get("completed") or 0

        if total <= 0:
            return self.STRUCTURE_PROGRESS_START

        ratio = max(0.0, min(1.0, completed / total))
        span = self.STRUCTURE_PROGRESS_END - self.STRUCTURE_PROGRESS_START
        return self.STRUCTURE_PROGRESS_START + int(round(span * ratio))