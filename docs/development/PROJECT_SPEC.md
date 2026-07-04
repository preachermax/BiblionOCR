📘 MyPixler / BiblionOCR Architecture Spec v2.0
“Event-Sourced RIS Project Creation System”
1. 🧭 System Overview

This system is a deterministic, event-sourced project creation engine with a Qt-based UI and persistent audit logging.

It is designed around one core principle:

Every project creation is a traceable sequence of immutable events (RIS-compliant provenance chain).

2. 🧱 High-Level Architecture
┌──────────────────────────────┐
│        UI Layer              │
│  (Qt MainWindow + Widgets)   │
└─────────────┬────────────────┘
              │ signals / calls
              ▼
┌──────────────────────────────┐
│     Controller Layer         │
│   (MyServer orchestrator)    │
│  - wiring only               │
│  - no business logic         │
└─────────────┬────────────────┘
              │
              ▼
┌──────────────────────────────┐
│       Core Engine Layer      │
│ ProjectCreationEngine        │
│ EventBus                     │
│ RIS Validator                │
│ State Machine               │
└─────────────┬────────────────┘
              │ events
              ▼
┌──────────────────────────────┐
│   Persistence Layer          │
│ SQLiteEventStore             │
│ (append-only event log)      │
└──────────────────────────────┘
3. 🧩 Core Principles
3.1 Separation of Responsibilities
Layer	Responsibility
UI	Rendering + user interaction
Controller (MyServer)	Wiring only
Core Engine	Business logic + state machine
EventBus	Event propagation
SQLite Store	Permanent audit log
3.2 Event-Sourced Truth Model

The system state is derived from events, not stored directly.

Every meaningful action becomes:

Event → persisted → replayable → reconstructs full system state
3.3 RIS Compliance Rule

Every project must produce a locked provenance record (RIS):

immutable after creation
hash-stamped
stored in filesystem + event log
4. ⚙️ Core Modules
4.1 ProjectCreationEngine
Responsibility

State machine controlling project lifecycle.

Location
Core/engine.py
Public API
create_project(payload: dict) -> dict
Lifecycle States
INIT →
VALIDATE →
PROVENANCE →
RIS →
WRITE →
COMPLETE / FAILED
4.2 EventBus
Responsibility

In-memory event dispatcher + bridge to persistence layer.

Rules
emits events only
does not mutate state
optionally persists via store
Interface
emit(event: dict)
subscribe(event_name: str, callback: fn)
4.3 SQLiteEventStore
Responsibility

Append-only immutable event log.

Rules
never updates events
only appends
supports replay
Schema
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_name TEXT,
    timestamp REAL,
    state TEXT,
    project_name TEXT,
    metadata TEXT
)
4.4 RIS Generator
Responsibility

Creates immutable provenance snapshot.

Output
{
  "project_name": str,
  "timestamp": float,
  "ris_version": "1.1",
  "hash": sha256,
  "locked": True
}
5. 🖥 UI Architecture (Qt Layer)
5.1 UI Structure
MainWindow (QMainWindow)
  └── self.ui (Ui_MainUI generated)
        └── widgets
5.2 Widget Access Rule

All widgets must be accessed via:

self.ui.ui.<widget_name>
5.3 UI Responsibilities
collect user input
emit button signals
display engine results
subscribe to events (optional)
6. 🎛 Controller Layer (MyServer)
6.1 Responsibility

MyServer is strictly:

A dependency injection + wiring layer

6.2 Allowed responsibilities
instantiate Core engine
instantiate UI
connect signals → engine
subscribe to events
no business logic
6.3 Forbidden responsibilities
no RIS validation
no filesystem logic
no event processing logic
6.4 Wiring pattern
UI button → MyServer handler → Engine → EventBus → Store/UI
7. 🔁 System Execution Flow
Full lifecycle:
1. User clicks "New Project"
        ↓
2. MyServer handler invoked
        ↓
3. Engine.create_project(payload)
        ↓
4. State machine executes steps
        ↓
5. Events emitted at each stage
        ↓
6. EventBus dispatches events
        ↓
7. SQLite stores event
        ↓
8. UI updates via subscriptions
8. 📡 Event Contract
Event Schema
{
    "event": str,
    "timestamp": float,
    "state": str,
    "project_name": str | None,
    "metadata": dict
}
Event Rules
events are immutable
events represent truth
all system changes must emit events
9. 📁 Package Structure (Canonical)
Core/
    engine.py
    event_bus.py
    event_store.py
    ris.py
    state.py
    __init__.py

ViewController/
    0-MainUI/
        MainWindow.py
        Ui_MainUI.py
        MyServer.py

user/
pyproject.toml
10. 🧠 Design Invariants

These MUST NEVER be violated:

Invariant 1

UI never directly calls filesystem logic

Invariant 2

Engine never imports UI

Invariant 3

EventBus never mutates state

Invariant 4

SQLite store is append-only

Invariant 5

MyServer contains no business logic

11. 🚀 Extension Points (Future Architecture)
Phase 3 additions
11.1 Replay Engine
rebuild full project from event log
11.2 Timeline Viewer
UI visualization of event chain
11.3 Plugin System
external project creation behaviors
11.4 Distributed Event Bus
multi-process / networked engine
12. 🧭 System Identity Statement

MyPixler is an event-sourced RIS-compliant project generation engine where all state transitions are immutable, traceable, and replayable.

