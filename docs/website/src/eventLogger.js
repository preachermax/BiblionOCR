const eventLogs = [];
const subscribers = new Set();

export function createTraceId(prefix = "trace") {
  const randomPart = Math.random().toString(36).slice(2, 10);
  return `${prefix}-${Date.now()}-${randomPart}`;
}

function cloneEntry(entry) {
  return {
    ...entry,
    payload: { ...entry.payload }
  };
}

function notifySubscribers() {
  const snapshot = eventLogs.map(cloneEntry);
  subscribers.forEach((subscriber) => {
    subscriber(snapshot);
  });
}

export function emitEvent(eventName, payload = {}, options = {}) {
  const entry = {
    event: eventName,
    payload,
    timestamp: new Date().toISOString(),
    traceId: options.traceId ?? null
  };

  eventLogs.push(entry);
  notifySubscribers();
  return cloneEntry(entry);
}

export function getEventLogs() {
  return eventLogs.map(cloneEntry);
}

export function subscribeToEventLogs(subscriber) {
  subscribers.add(subscriber);
  subscriber(getEventLogs());

  return () => {
    subscribers.delete(subscriber);
  };
}

export function clearEventLogs() {
  eventLogs.length = 0;
  notifySubscribers();
}