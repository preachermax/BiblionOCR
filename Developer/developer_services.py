"""Developer Services runtime instrumentation interface.

This module defines the central runtime instrumentation service for
Developer Mode as described in ``docs/architecture/DEVELOPER_MODE_ARCHITECTURE.md``.

The class in this module is intentionally limited to an architectural
interface skeleton. It establishes constructor shape, documentation, and
placeholder methods without implementing runtime behavior.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ObservedModule:
    """Developer-facing snapshot for a single observed runtime module."""

    name: str
    current_state: object = None
    last_observed_event: str = "UNKNOWN"
    last_update_timestamp: str = ""
    status: str = "unknown"


@dataclass
class RuntimeMetrics:
    """Lightweight metrics snapshot for future runtime expansion."""

    total_observed_events: int = 0
    events_per_module: dict = None

    def __post_init__(self):
        if self.events_per_module is None:
            self.events_per_module = {}


@dataclass
class TraceEntry:
    """Developer-facing execution trace record."""

    trace_identifier: str
    event_name: str
    source_module: str
    destination_module: str
    timestamp: str


@dataclass
class RecentEvent:
    """Developer-facing snapshot of a recently observed EventBus event."""

    source_module: str
    destination_module: str
    event_name: str
    timestamp: str
    status: str


class TraceRecorder:
    """Lightweight in-memory trace recorder for Developer Mode.

    This implementation stores execution traces only. Replay, filtering,
    export, and session comparison behaviors remain intentionally deferred.
    """

    def __init__(self):
        self.traces = []

    def record(self, trace_identifier, event_name, source_module, destination_module):
        """Store a single execution trace entry."""
        trace_entry = TraceEntry(
            trace_identifier=trace_identifier,
            event_name=event_name,
            source_module=source_module,
            destination_module=destination_module,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.traces.append(trace_entry)
        return trace_entry

    def snapshot(self):
        """Return a serializable snapshot of recorded execution traces."""
        return [
            {
                "trace_identifier": trace.trace_identifier,
                "event_name": trace.event_name,
                "source_module": trace.source_module,
                "destination_module": trace.destination_module,
                "timestamp": trace.timestamp,
            }
            for trace in self.traces
        ]


class RecentEventStore:
    """Bounded in-memory store for recent observed EventBus activity."""

    def __init__(self, max_events=100):
        self.max_events = max_events
        self.events = []

    def record(
        self, source_module, destination_module, event_name, status, timestamp=None
    ):
        """Store a recent event entry for panel inspection."""
        recent_event = RecentEvent(
            source_module=source_module,
            destination_module=destination_module,
            event_name=event_name,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            status=status,
        )
        self.events.append(recent_event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]
        return recent_event

    def snapshot(self):
        """Return a serializable snapshot of recent observed events."""
        return [
            {
                "source_module": event.source_module,
                "destination_module": event.destination_module,
                "event_name": event.event_name,
                "timestamp": event.timestamp,
                "status": event.status,
            }
            for event in self.events
        ]


class RuntimeModel:
    """Internal runtime model maintained by DeveloperServices.

    This implementation manages the modules collection and a lightweight
    metrics section, leaving broader performance instrumentation for later
    milestones.
    """

    def __init__(self):
        self.modules = {}
        self.metrics = RuntimeMetrics()

    def update_module(self, module_name, current_state, last_event, status):
        """Create or update a module entry from normalized event data."""
        module = self.modules.get(module_name)
        if module is None:
            module = ObservedModule(name=module_name)
            self.modules[module_name] = module

        module.current_state = current_state
        module.last_observed_event = last_event
        module.last_update_timestamp = datetime.now(timezone.utc).isoformat()
        module.status = status

        return module

    def snapshot(self):
        """Return a serializable snapshot of the runtime model."""
        return {
            "modules": {
                name: {
                    "name": module.name,
                    "current_state": module.current_state,
                    "last_observed_event": module.last_observed_event,
                    "last_update_timestamp": module.last_update_timestamp,
                    "status": module.status,
                }
                for name, module in self.modules.items()
            },
            "metrics": self.metrics_snapshot(),
        }

    def modules_snapshot(self):
        """Return a serializable snapshot of observed modules only."""
        return deepcopy(self.snapshot()["modules"])

    def registered_modules_snapshot(self):
        """Return a read-only list of registered module names."""
        return list(self.modules.keys())

    def module_snapshot(self, module_name):
        """Return a serializable snapshot for one observed module."""
        module = self.modules.get(module_name)
        if module is None:
            return None

        return deepcopy(
            {
                "name": module.name,
                "current_state": module.current_state,
                "last_observed_event": module.last_observed_event,
                "last_update_timestamp": module.last_update_timestamp,
                "status": module.status,
            }
        )

    def record_observed_event(self, module_name):
        """Update lightweight event counters for the observed module."""
        self.metrics.total_observed_events += 1
        self.metrics.events_per_module[module_name] = (
            self.metrics.events_per_module.get(module_name, 0) + 1
        )

    def metrics_snapshot(self):
        """Return a serializable snapshot of the lightweight metrics state."""
        return {
            "total_observed_events": self.metrics.total_observed_events,
            "events_per_module": dict(self.metrics.events_per_module),
        }


class DeveloperServices:
    """Central runtime instrumentation service for Developer Mode.

    DeveloperServices is the sole instrumentation layer between production
    modules and Developer Mode panels. Production modules continue to publish
    normal application events through the existing EventBus. DeveloperServices
    observes those events, normalizes them into a runtime model, collects
    metrics and traces, and publishes aggregated diagnostic information for
    developer-facing panels.

    This skeleton intentionally avoids implementing operational runtime
    behavior. Its purpose is to establish the architectural interface for the
    future Developer Mode subsystem.
    """

    def __init__(self, event_bus, enabled=True, workspace_root=None):
        """Initialize the DeveloperServices interface.

        Args:
            event_bus: The production EventBus instance observed by
                DeveloperServices.
            enabled: Whether DeveloperServices should consider itself active.
                This flag is stored only as configuration state in this
                skeleton.
            workspace_root: Optional workspace-scoped root for future
                developer-facing diagnostic artifacts such as traces, session
                recordings, and comparison snapshots.
        """
        self.event_bus = event_bus
        self.enabled = enabled
        self.workspace_root = workspace_root
        self.runtime_model = RuntimeModel()
        self.trace_recorder = TraceRecorder()
        self.recent_events = RecentEventStore()

    def start(self):
        """Start DeveloperServices subscriptions and collection pipelines.

        Placeholder only. Future implementations should subscribe to the
        EventBus and activate runtime observation when Developer Mode is
        enabled.
        """

    def stop(self):
        """Stop DeveloperServices subscriptions and collection pipelines.

        Placeholder only. Future implementations should detach subscriptions,
        flush or finalize pending diagnostics as needed, and leave production
        runtime behavior unchanged.
        """

    def observe_event(self, event):
        """Observe a production event from the EventBus.

        This initial implementation is limited to module collection updates in
        the internal runtime model.
        """
        normalized_event = self.normalize_event(event)
        self.update_runtime_model(normalized_event)
        self.collect_metrics(normalized_event)
        self.record_trace(normalized_event)
        self.record_recent_event(normalized_event)

    def normalize_event(self, event):
        """Normalize a production event into the Developer Mode event model.

        This initial implementation extracts only the fields needed to update
        the modules collection.
        """
        module_name = event.get("module") or event.get("source") or "unknown"
        return {
            "module_name": module_name,
            "current_state": event.get("state"),
            "last_event": event.get("event", "UNKNOWN"),
            "status": event.get("status", "observed"),
            "trace_identifier": event.get("trace_id", "untraced"),
            "event_name": event.get("event", "UNKNOWN"),
            "source_module": event.get("source") or module_name,
            "destination_module": event.get("target")
            or event.get("destination")
            or "unknown",
            "timestamp": event.get("timestamp")
            or datetime.now(timezone.utc).isoformat(),
        }

    def update_runtime_model(self, normalized_event):
        """Update the internal runtime state model.

        This initial implementation updates only the modules collection defined
        by the runtime state model.
        """
        self.runtime_model.update_module(
            module_name=normalized_event["module_name"],
            current_state=normalized_event.get("current_state"),
            last_event=normalized_event.get("last_event", "UNKNOWN"),
            status=normalized_event.get("status", "observed"),
        )

    def collect_metrics(self, normalized_event):
        """Collect performance and diagnostic metrics.

        This initial implementation collects only total observed event count
        and event count per module. Broader performance metrics remain
        intentionally unimplemented.
        """
        self.runtime_model.record_observed_event(normalized_event["module_name"])

    def record_trace(self, normalized_event):
        """Record trace information for runtime execution paths.

        This initial implementation stores execution trace entries only.
        Replay, export, filtering, and session comparison remain deferred.
        """
        self.trace_recorder.record(
            trace_identifier=normalized_event.get("trace_identifier", "untraced"),
            event_name=normalized_event.get("event_name", "UNKNOWN"),
            source_module=normalized_event.get("source_module", "unknown"),
            destination_module=normalized_event.get(
                "destination_module", "unknown"
            ),
        )

    def record_recent_event(self, normalized_event):
        """Store a recent event snapshot for future Developer Mode panels.

        This accessor-facing store supports live event inspection without
        exposing mutable internal state or modifying production behavior.
        """
        self.recent_events.record(
            source_module=normalized_event.get("source_module", "unknown"),
            destination_module=normalized_event.get(
                "destination_module", "unknown"
            ),
            event_name=normalized_event.get("event_name", "UNKNOWN"),
            status=normalized_event.get("status", "observed"),
            timestamp=normalized_event.get("timestamp"),
        )

    def update_dependency_graph(self, normalized_event):
        """Update dependency and relationship information.

        Placeholder only. Future implementations should derive module and
        service relationships from observed runtime behavior.
        """

    def publish_diagnostics(self):
        """Publish aggregated diagnostic data to Developer Mode consumers.

        Placeholder only. Future implementations should expose runtime model,
        metrics, traces, and related developer-facing information to panels or
        other developer-mode surfaces.
        """

    def get_runtime_model(self):
        """Return the current runtime model snapshot.

        The returned dictionary is detached from internal state so Developer
        Mode panels can inspect it without mutating runtime instrumentation.
        """
        return deepcopy(self.runtime_model.snapshot())

    def get_modules(self):
        """Return a read-only snapshot of the observed modules collection.

        This accessor is intended for future Developer Mode panels and returns
        a defensive copy of the internal module state.
        """
        return self.runtime_model.modules_snapshot()

    def get_registered_modules(self):
        """Return a read-only list of registered module names.

        This stable accessor exposes module registration state without
        returning mutable references to the internal module collection.
        """
        return list(self.runtime_model.registered_modules_snapshot())

    def get_module_state(self, module_name):
        """Return a read-only snapshot for a single observed module.

        The returned value is detached from the internal runtime model so
        callers cannot mutate DeveloperServices state.
        """
        return self.runtime_model.module_snapshot(module_name)

    def get_metrics(self):
        """Return a read-only snapshot of DeveloperServices metrics.

        The returned dictionary is a defensive copy suitable for future
        Developer Mode panel consumption.
        """
        return self.get_metrics_snapshot()

    def get_metrics_snapshot(self):
        """Return the current metrics snapshot.

        This initial implementation returns only lightweight event counters.
        """
        return deepcopy(self.runtime_model.metrics_snapshot())

    def get_traces(self):
        """Return a read-only snapshot of recorded execution traces.

        Trace data is returned as detached serializable records so callers
        cannot mutate internal trace storage.
        """
        return self.get_trace_snapshot()

    def get_recent_events(self):
        """Return a read-only snapshot of recent observed EventBus activity.

        This accessor supports future live event panels and returns defensive
        copies of source, destination, event, timestamp, and status fields.
        """
        return deepcopy(self.recent_events.snapshot())

    def get_trace_snapshot(self):
        """Return the current trace snapshot.

        This initial implementation returns stored execution trace entries
        without replay, filtering, or export behavior.
        """
        return deepcopy(self.trace_recorder.snapshot())

    def export_traces(self, destination=None):
        """Export developer-facing trace artifacts.

        Placeholder only. Future implementations should export traces to
        workspace-scoped developer storage by default unless a future workflow
        explicitly defines a project-safe diagnostic artifact path.
        """

    def compare_sessions(self, left_session, right_session):
        """Compare two developer-mode diagnostic sessions.

        Placeholder only. Future implementations should compare recorded
        sessions or trace snapshots for architectural diagnostics.
        """