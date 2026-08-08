# event_bus.py

import time


EVENT_SCHEMA_KEYS = ("event", "timestamp", "state", "project_name", "metadata")


def normalize_event(event):
    """Normalize an event to the canonical schema or raise ValueError."""
    if not isinstance(event, dict):
        raise ValueError("Event must be a dict")

    name = event.get("event")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Event requires a non-empty string 'event' field")

    state = event.get("state")
    if state is None:
        raise ValueError("Event requires 'state'")
    if not isinstance(state, str):
        state = str(state)

    timestamp = event.get("timestamp")
    if timestamp is None:
        raise ValueError("Event requires 'timestamp'")
    try:
        timestamp = float(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError("Event 'timestamp' must be numeric") from exc

    project_name = event.get("project_name")
    if project_name is not None and not isinstance(project_name, str):
        project_name = str(project_name)

    metadata = event.get("metadata")
    if metadata is None:
        metadata = {}
    elif not isinstance(metadata, dict):
        metadata = {"value": metadata}

    normalized = {
        "event": name.strip(),
        "timestamp": timestamp,
        "state": state,
        "project_name": project_name,
        "metadata": metadata,
    }

    # Ensure only canonical top-level keys are emitted downstream.
    return {key: normalized[key] for key in EVENT_SCHEMA_KEYS}

class EventBus:
    def __init__(self, store=None):
        self.listeners = {}
        self.store = store

    def subscribe(self, event_name, callback):
        self.listeners.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name, callback):
        callbacks = self.listeners.get(event_name)
        if not callbacks:
            return

        self.listeners[event_name] = [cb for cb in callbacks if cb != callback]
        if not self.listeners[event_name]:
            del self.listeners[event_name]

    def emit(self, event):
        event = normalize_event(event)

        if self.store:
            try:
                self.store.append(event)
            except Exception as exc:
                print(f"[EventBus] store append failed: {exc}")

        for cb in self.listeners.get(event["event"], []):
            try:
                cb(event)
            except Exception as exc:
                callback_name = getattr(cb, "__qualname__", repr(cb))
                print(
                    f"[EventBus] listener failed for {event['event']} "
                    f"({callback_name}): {exc}"
                )