# event_bus.py

class EventBus:
    def __init__(self, store=None):
        self.listeners = {}
        self.store = store

    def subscribe(self, event_name, callback):
        self.listeners.setdefault(event_name, []).append(callback)

    def emit(self, event):
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