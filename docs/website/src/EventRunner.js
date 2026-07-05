import { createTraceId, emitEvent } from "./eventLogger.js";
import { getIsRunning, setIsRunning, setLastEvent } from "./stateManager.js";

export class EventRunner {
  constructor({ eventBus, executor, delayMs = 1200 }) {
    this.eventBus = eventBus;
    this.executor = executor;
    this.delayMs = delayMs;
    this.runId = 0;
    this.activeTraceId = null;
  }

  async run(startEvent, context = {}) {
    if (!this.eventBus) {
      throw new Error("EventRunner requires an EventBus instance.");
    }

    if (typeof this.executor !== "function") {
      throw new Error("EventRunner requires an executor function.");
    }

    if (!startEvent) {
      return false;
    }

    const runId = ++this.runId;
    const traceId = context.traceId ?? createTraceId("execution");
    this.activeTraceId = traceId;

    setIsRunning(true);

    const startedEntry = emitEvent("sequence_started", {
      startEvent,
      delayMs: this.delayMs,
      context
    }, { traceId });

    setLastEvent(startedEntry);
    this.eventBus.emit("sequence_started", {
      startEvent,
      delayMs: this.delayMs,
      context,
      traceId,
      logEntry: startedEntry
    });

    try {
      const result = await Promise.resolve(
        this.executor(startEvent, {
          ...context,
          traceId,
          delayMs: this.delayMs
        })
      );

      if (runId !== this.runId) {
        return false;
      }

      setIsRunning(false);

      const completedEntry = emitEvent("sequence_completed", {
        startEvent,
        delayMs: this.delayMs,
        context
      }, { traceId });

      setLastEvent(completedEntry);
      this.eventBus.emit("sequence_completed", {
        startEvent,
        delayMs: this.delayMs,
        context,
        traceId,
        logEntry: completedEntry
      });

      this.activeTraceId = null;

      return result;
    } catch (error) {
      if (runId === this.runId) {
        setIsRunning(false);
        this.activeTraceId = null;
      }
      throw error;
    }
  }

  async runSequence(startEvent, context = {}) {
    return this.run(startEvent, context);
  }

  stop({ reason = "stopped" } = {}) {
    const wasRunning = getIsRunning();
    this.runId += 1;
    setIsRunning(false);

    if (!wasRunning) {
      return false;
    }

    const traceId = this.activeTraceId;
    const stoppedEntry = emitEvent("sequence_stopped", { reason }, { traceId });
    setLastEvent(stoppedEntry);
    this.eventBus.emit("sequence_stopped", {
      reason,
      traceId,
      logEntry: stoppedEntry
    });

    this.activeTraceId = null;

    return true;
  }
}