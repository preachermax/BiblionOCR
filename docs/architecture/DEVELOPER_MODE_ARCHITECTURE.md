# DEVELOPER_MODE_ARCHITECTURE.md

# BiblionOCR Developer Mode Architecture

Version: 1.0
Status: Design Specification
Author: BiblionOCR Architecture
Last Updated: July 2026

---

# 1. Purpose

Developer Mode provides runtime observability for the BiblionOCR platform.

Its purpose is to expose internal application behavior without modifying production workflows or affecting normal application performance.

Developer Mode exists for:

- Application debugging
- Runtime visualization
- Performance analysis
- Contributor onboarding
- Educational demonstrations
- Architecture validation

Developer Mode is intended to remain an integrated subsystem of BiblionOCR rather than a separate application.

---

# 2. Design Goals

Developer Mode shall:

✓ Observe application behavior

✓ Never become application logic

✓ Operate through the EventBus

✓ Remain modular

✓ Be platform independent

✓ Scale with future BiblionOCR modules

---

# 3. Architectural Philosophy

Developer Mode is a passive observer.

Production modules never update Developer Mode directly.

Instead:

Production Module
        │
        ▼
    EventBus
        │
        ▼
Developer Services
        │
        ▼
Developer Panels

This preserves separation of concerns while maintaining a single event-driven architecture.

---

# 4. Core Principles

## Principle 1

Developer Mode is read-only by default.

No developer panel should modify application state unless explicitly designed as a diagnostic tool.

---

## Principle 2

Production behavior must never depend upon Developer Mode.

Developer Mode may be disabled entirely without changing application execution.

---

## Principle 3

Developer Mode subscribes to events.

It does not receive direct function calls from production modules.

---

## Principle 4

Developer panels are independent.

Each panel should be capable of being enabled or disabled without affecting other panels.

Visible Developer panels should be hidden by default and activated only through an explicit Developer-facing control.

When a panel is closed or inactive, it should not require ongoing observation work beyond the minimum runtime wiring needed to preserve normal application behavior.

---

## Principle 5

Developer Mode must remain cross-platform.

Windows

Ubuntu

Jetson Nano

must expose a consistent runtime information schema.

Observed values may differ according to platform capabilities, active backends, and environment-specific runtime conditions.

---

# 5. High-Level Architecture

                BiblionOCR

      ┌──────────────────────────┐
      │     Production Modules    │
      └──────────────────────────┘
                   │
                   ▼
               EventBus
                   │
                   ▼
        Developer Services Layer
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
 Runtime      Metrics      Trace Recorder
 Inspector    Collector
     ▼
 Dependency Graph
     ▼
 Developer Panels

Developer Services acts as the instrumentation layer between production code and the developer interface.

---

# 6. Developer Services

Developer Services is the central runtime observer.

Responsibilities include:

• Event observation

• Runtime state collection

• Performance metric aggregation

• Trace recording

• Dependency graph updates

• Session diagnostics

Production modules remain unaware of Developer Services.

---

# 7. Runtime Components

## Runtime Inspector

Displays live information for each module.

The Runtime Inspector consumes runtime information exclusively through the public read-only Developer Services API.

It must not query production modules directly.

Example:

Module Name

Status

Current Operation

Execution Time

Subscriber Count

Recent Events

Canonical runtime status values for the initial Runtime Inspector are:

OPEN

CLOSED

OBSERVED

UNKNOWN

---

## Event Timeline

Chronological display of runtime events.

Example:

10:31:15

Image Loaded

↓

10:31:15

Session Updated

↓

10:31:15

OCR Requested

↓

10:31:16

OCR Complete

---

## Live Event Monitor

Displays current EventBus activity.

Source

Target

Event

Timestamp

Status

---

## Dependency Explorer

Visualizes relationships between runtime modules.

Example:

MyServer

├── SessionManager

├── OCR

├── EventBus

└── MyPixler

---

## Performance Monitor

Displays:

Execution Time

Average Runtime

Call Frequency

Queue Length

Memory Usage

---

## Trace Recorder

Records complete execution traces.

Supports:

Replay

Export

Filtering

Session comparison

Trace Recorder artifacts are developer-facing diagnostics.

By default, exported traces, session recordings, and comparison snapshots belong to Workspace-scoped developer storage rather than generated user Project data.

They should only be written into a Project when a future workflow explicitly defines them as project-safe diagnostic artifacts.

---

# 8. Runtime State Model

Each observed module may expose:

Module Name

Current State

Previous State

Active Task

Last Event

Execution Count

Average Runtime

Error State

Last Exception

Developer Mode reads these values only.

---

# 9. Event Model

Developer Mode observes EventBus traffic.

Typical events include:

PROJECT_CREATED

IMAGE_LOADED

OCR_STARTED

OCR_COMPLETED

PREVIEW_UPDATED

SESSION_SAVED

TEXT_EXPORTED

MODULE_OPENED

MODULE_CLOSED

Additional events may be introduced without modifying Developer Mode architecture.

---

# 10. Performance Considerations

Developer Mode shall:

avoid polling whenever possible

use event subscriptions

minimize allocations

allow selective panel activation

support future asynchronous collection

When disabled, runtime overhead should be negligible.

Developer-facing diagnostic artifacts should remain opt-in and should not expand normal Project output by default.

---

# 11. Future Expansion

Planned milestones include:

Milestone A

Runtime Observation

• Runtime Inspector

• Event Timeline

• Active Task Display

---

Milestone B

Visualization

• Dependency Graph

• Live Module Graph

• Event Path Animation

---

Milestone C

Diagnostics

• Trace Replay

• Event Filtering

• Session Recording

• Error Correlation

---

Milestone D

Performance

• CPU Metrics

• Memory Metrics

• Queue Metrics

• Event Throughput

---

Milestone E

Educational Mode

Provide an animated visualization of BiblionOCR execution suitable for:

Training

Documentation

Presentations

Community demonstrations

---

# 12. Integration Strategy

Developer Mode will evolve incrementally.

The first visible panel integration should prove the architecture with the smallest viable host surface.

For the initial Runtime Inspector milestone, the panel should be:

hidden by default

opened through a Developer-facing interface

driven by event subscriptions rather than polling

activated lazily so normal application behavior remains unaffected when Developer Mode is not in use

Implementation order:

1. Developer Services

2. Runtime Inspector

3. Event Timeline

4. Event Monitor

5. Performance Metrics

6. Dependency Graph

7. Trace Recorder

8. Educational Mode

Each milestone should remain independently functional.


## Definition

Developer Services is a runtime instrumentation subsystem.

Its responsibility is to observe, normalize, and publish runtime information for Developer Mode.

Developer Services is the only subsystem responsible for collecting developer-facing runtime data.

Production modules remain independent of Developer Services and continue to communicate through the EventBus.

Developer Services observes those communications and maintains an internal representation of application state for diagnostic purposes.

---

# 13. Relationship to Existing Architecture

Developer Mode extends the existing BiblionOCR architecture.

It does not replace:

MyServer

MyPixler

Project Creation Engine

EventBus

Session Manager

OCR Pipeline

Instead, it provides runtime observability for these systems.

# Runtime Instrumentation Contract

Production modules should publish meaningful application events through the EventBus.

Events should describe application activity rather than developer diagnostics.

Developer Services derives diagnostic information from these events.

Production modules should not emit events solely for Developer Mode.

Developer Services is responsible for:

• Event normalization

• Runtime state aggregation

• Trace recording

• Metrics collection

• Diagnostic publication
---

# 14. Long-Term Vision

Developer Mode should eventually become one of the defining capabilities of BiblionOCR.

Beyond debugging, it should:

teach new contributors

document system behavior

validate architectural decisions

support performance optimization

provide reproducible execution traces

serve as a living architectural reference for the project.

Developer Mode should demonstrate not only what BiblionOCR does, but how it does it.

# 15. Architectural Covenant

The architecture documents within the BiblionOCR repository are the authoritative source of design intent.

Implementation should follow documented architecture.

When implementation diverges from architecture:

1. Determine whether the implementation or architecture is correct.

2. Update one to match the other.

Architecture documents should never become historical artifacts.

They are living specifications that evolve with the software.