const state = {
  activeNode: null,
  lastEvent: null,
  isRunning: false
};
const subscribers = new Set();

function cloneValue(value) {
  if (value && typeof value === "object") {
    return { ...value };
  }

  return value;
}

function snapshotState() {
  return {
    activeNode: cloneValue(state.activeNode),
    lastEvent: cloneValue(state.lastEvent),
    isRunning: state.isRunning
  };
}

function notifySubscribers() {
  const snapshot = snapshotState();
  subscribers.forEach((subscriber) => {
    subscriber(snapshot);
  });
}

export function getActiveNode() {
  return state.activeNode;
}

export function setActiveNode(activeNode) {
  state.activeNode = activeNode;
  notifySubscribers();
  return cloneValue(state.activeNode);
}

export function getLastEvent() {
  return state.lastEvent;
}

export function setLastEvent(lastEvent) {
  state.lastEvent = lastEvent;
  notifySubscribers();
  return cloneValue(state.lastEvent);
}

export function getIsRunning() {
  return state.isRunning;
}

export function setIsRunning(isRunning) {
  state.isRunning = isRunning;
  notifySubscribers();
  return state.isRunning;
}

export function getState() {
  return snapshotState();
}

export function subscribeToState(subscriber) {
  subscribers.add(subscriber);
  subscriber(getState());

  return () => {
    subscribers.delete(subscriber);
  };
}