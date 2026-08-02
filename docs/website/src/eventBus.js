export class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(eventName, listener) {
    const listeners = this.listeners.get(eventName) ?? new Set();
    listeners.add(listener);
    this.listeners.set(eventName, listeners);

    return () => {
      this.off(eventName, listener);
    };
  }

  off(eventName, listener) {
    const listeners = this.listeners.get(eventName);
    if (!listeners) {
      return;
    }

    listeners.delete(listener);
    if (listeners.size === 0) {
      this.listeners.delete(eventName);
    }
  }

  emit(eventName, payload = {}) {
    const listeners = this.listeners.get(eventName);
    if (!listeners) {
      return payload;
    }

    listeners.forEach((listener) => {
      listener(payload);
    });

    return payload;
  }
}