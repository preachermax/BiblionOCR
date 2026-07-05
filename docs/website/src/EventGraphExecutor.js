import { eventGraph } from "./eventGraph.js";
import { emitEvent } from "./eventLogger.js";
import { setActiveNode, setIsRunning, setLastEvent } from "./stateManager.js";

function createActiveNode(eventName, depth, parentEvent) {
  return {
    id: eventName,
    label: eventName,
    category: "Event",
    summary: `Event graph execution step at depth ${depth}.`,
    parentEvent: parentEvent ?? null
  };
}

export class EventGraphExecutor {
  constructor({ eventBus, graph = eventGraph, maxDepth = 12 } = {}) {
    if (!eventBus) {
      throw new Error("EventGraphExecutor requires an EventBus instance.");
    }

    this.eventBus = eventBus;
    this.graph = graph;
    this.maxDepth = maxDepth;
  }

  execute(startEvent, context = {}) {
    if (!startEvent) {
      throw new Error("EventGraphExecutor requires a starting event.");
    }

    setIsRunning(true);

    const trail = [];

    try {
      this.#executeRecursive(startEvent, {
        depth: 0,
        path: [],
        trail,
        parentEvent: context.parentEvent ?? null,
        payload: context.payload ?? {},
        traceId: context.traceId ?? null
      });

      return trail;
    } finally {
      setIsRunning(false);
    }
  }

  #executeRecursive(eventName, executionState) {
    const { depth, path, trail, parentEvent, payload, traceId } = executionState;

    if (depth > this.maxDepth) {
      const depthEntry = emitEvent("event_graph_max_depth_reached", {
        eventName,
        depth,
        maxDepth: this.maxDepth,
        path
      }, { traceId });

      setLastEvent(depthEntry);
      this.eventBus.emit("event_graph_max_depth_reached", {
        eventName,
        depth,
        maxDepth: this.maxDepth,
        path,
        traceId,
        logEntry: depthEntry
      });
      trail.push(depthEntry);
      return;
    }

    const activeNode = createActiveNode(eventName, depth, parentEvent);
    setActiveNode(activeNode);

    const entry = emitEvent(eventName, {
      source: "event-graph-executor",
      depth,
      parentEvent,
      path,
      ...payload
    }, { traceId });

    setLastEvent(entry);
    this.eventBus.emit(eventName, {
      depth,
      parentEvent,
      path,
      traceId,
      activeNode,
      logEntry: entry,
      payload
    });
    trail.push(entry);

    const nextEvents = this.graph[eventName] ?? [];
    const nextPath = [...path, eventName];

    nextEvents.forEach((nextEvent) => {
      if (nextPath.includes(nextEvent)) {
        const cycleEntry = emitEvent("event_graph_cycle_detected", {
          eventName: nextEvent,
          parentEvent: eventName,
          depth: depth + 1,
          path: nextPath
        }, { traceId });

        setLastEvent(cycleEntry);
        this.eventBus.emit("event_graph_cycle_detected", {
          eventName: nextEvent,
          parentEvent: eventName,
          depth: depth + 1,
          path: nextPath,
          traceId,
          logEntry: cycleEntry
        });
        trail.push(cycleEntry);
        return;
      }

      this.#executeRecursive(nextEvent, {
        depth: depth + 1,
        path: nextPath,
        trail,
        parentEvent: eventName,
        payload,
        traceId
      });
    });
  }
}