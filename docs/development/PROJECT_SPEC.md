# MyPixler / BiblionOCR Architecture Spec v2.0

Event-Sourced RIS Project Creation System

## 1. System Overview

This system is a deterministic, event-sourced project creation engine with a Qt-based UI and persistent audit logging.

Core principle:

Every project creation is a traceable sequence of immutable events (RIS-compliant provenance chain).

## 2. High-Level Architecture

```text
+------------------------------+
| UI Layer                     |
| (Qt MainWindow + Widgets)    |
+-------------+----------------+
              | signals / calls
              v
+------------------------------+
| Controller Layer             |
| (MyServer orchestrator)      |
| - dependency wiring          |
| - runtime orchestration      |
+-------------+----------------+
              |
              v
+------------------------------+
| Core Engine Layer            |
| ProjectCreationEngine        |
| EventBus                     |
| RIS Validator                |
| State Machine                |
+-------------+----------------+
              | events
              v
+------------------------------+
| Persistence Layer            |
| SQLiteEventStore             |
| (append-only event log)      |
+------------------------------+
```

## 3. Core Principles

### 3.1 Separation of Responsibilities

| Layer | Responsibility |
| --- | --- |
| UI | Rendering and user interaction |
| Controller (MyServer) | Dependency wiring and runtime orchestration |
| Core Engine | Business logic and state machine |
| EventBus | Event propagation |
| SQLite Store | Permanent audit log |

### 3.2 Event-Sourced Truth Model

The system state is derived from events, not stored directly.

Every meaningful action becomes:

Event -> persisted -> replayable -> reconstructs full system state.

### 3.3 RIS Compliance Rule

Every project must produce a locked provenance record (RIS):

- Immutable after creation.
- Hash-stamped.
- Stored in filesystem and event log.

## 4. Core Modules

### 4.1 ProjectCreationEngine

Responsibility:

State machine controlling project lifecycle.

Location:

Core/engine.py

Public API:

create_project(payload: dict) -> dict

Lifecycle states:

INIT -> VALIDATE -> PROVENANCE -> RIS -> WRITE -> COMPLETE / FAILED

### 4.2 EventBus

Responsibility:

In-memory event dispatcher and bridge to persistence layer.

Rules:

- Emits events only.
- Does not mutate state.
- Optionally persists via store.

Interface:

- emit(event: dict)
- subscribe(event_name: str, callback: fn)
- unsubscribe(event_name: str, callback: fn)

### 4.3 SQLiteEventStore

Responsibility:

Append-only immutable event log.

Rules:

- Never updates events.
- Only appends.
- Supports replay and filtered reads.

Schema:

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_name TEXT,
    timestamp REAL,
    state TEXT,
    project_name TEXT,
    metadata TEXT
)
```

### 4.4 RIS Generator

Responsibility:

Creates immutable provenance snapshot.

Output:

```json
{
  "project_name": "str",
  "timestamp": 0.0,
  "ris_version": "1.1",
  "hash": "sha256",
  "locked": true
}
```

## 5. UI Architecture (Qt Layer)

### 5.1 UI Structure

MyServer (QMainWindow)

- Owns self.ui as Ui_MainUI generated class instance.
- Ui_MainUI class is loaded from MyServerUI.py.
- Widgets are members of self.ui.

### 5.2 Widget Access Rule

Widget access pattern:

self.ui.<widget_name>

### 5.3 UI Responsibilities

- Collect user input.
- Emit button signals.
- Display engine results.
- Subscribe to events (optional).

## 6. Controller Layer (MyServer)

### 6.1 Responsibility

MyServer is primarily:

A dependency injection and orchestration layer.

### 6.2 Allowed responsibilities

- Instantiate Core engine dependencies.
- Instantiate UI and module surfaces.
- Connect signals to engine and module handlers.
- Subscribe to events and route UI updates.

### 6.3 Forbidden responsibilities

- No RIS validation logic in controller methods.
- No direct filesystem business rules in controller methods.
- No domain event schema ownership outside Core.

### 6.4 Wiring Pattern

UI button -> MyServer handler -> Engine -> EventBus -> Store/UI

## 7. System Execution Flow

Full lifecycle:

1. User clicks New Project.
2. MyServer handler is invoked.
3. Engine.create_project(payload) runs.
4. State machine executes steps.
5. Events are emitted at each stage.
6. EventBus dispatches events.
7. SQLite stores event.
8. UI updates via subscriptions.

## 8. Event Contract

Event schema:

```json
{
  "event": "str",
  "timestamp": 0.0,
  "state": "str",
  "project_name": null,
  "metadata": {}
}
```

Event rules:

- Events are immutable.
- Events represent truth.
- All system changes must emit events.

## 9. Package Structure (Canonical)

```text
Core/
    engine.py
    event_bus.py
    event_store.py
    ris.py
    state.py
    __init__.py

ViewController/
    0-MainUI/
        MyServer.py
        MyServerUI.py

user/
pyproject.toml
```

## 10. Design Invariants

These must never be violated:

1. UI never directly calls filesystem business logic.
2. Engine never imports UI.
3. EventBus never mutates state.
4. SQLite store is append-only.
5. MyServer should not own core domain business logic.

## 11. Extension Points (Future Architecture)

Phase 3 additions:

### 11.1 Replay Engine

Rebuild full project from event log.

### 11.2 Timeline Viewer

UI visualization of event chain.

### 11.3 Plugin System

External project creation behaviors.

### 11.4 Distributed Event Bus

Multi-process or networked engine.

## 12. System Identity Statement

MyPixler is an event-sourced RIS-compliant project generation engine where all state transitions are immutable, traceable, and replayable.
