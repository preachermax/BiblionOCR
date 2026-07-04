# BiblionOCR Design Specification

## Status

Active design reference for domain boundaries and terminology.

## Purpose

This document distinguishes the major classes of concern in BiblionOCR so architecture, UI behavior, project generation, and future module work use the same vocabulary.

It is intentionally broader than project creation alone.

## 1. Top-Level Classes

### System

The full BiblionOCR platform.

Includes:
- repository source code
- Core runtime logic
- ViewController UI applications
- shared reference data
- generated user projects under the external Projects root
- documentation, manifests, and release support assets

Rules:
- the System owns code and reusable reference material
- the System may generate Projects but is not itself a Project
- the System should preserve stable boundaries between UI wiring, business logic, and persisted user artifacts

### Workspace

A checked-out development tree of the System.

Examples:
- the current repository clone
- local generated UI files
- tracked docs and design notes
- temporary developer-only files not intended for generated projects

Rules:
- a Workspace is for development and maintenance
- a Workspace can contain historical or experimental material that should not automatically flow into generated Projects
- cleanup decisions must distinguish workspace-only payloads from required Project artifacts

### Project

A user-created, externally stored work unit rooted under the user Projects folder.

Examples:
- `C:/Users/Max/Projects/Erasmus1516`
- future OCR/training/reference projects created from MyServer

A Project includes:
- provenance (`project.ris.json`)
- a deterministic folder structure derived from the project manifest
- project-local image, text, training, and output folders
- project-local runtime data such as JSON state and future MyWriter `esword` output

Rules:
- a Project is a generated artifact of the System
- a Project must be traceable, reproducible, and locally version-controlled
- a Project should include only project-safe runtime assets, not broad workspace history or development payloads by default

## 2. Operational Classes

### Workflow

An ordered business-level path through the system that advances a Project toward an outcome.

Examples:
- project creation workflow
- OCR workflow from source PDF to corrected text
- image preparation workflow in MyPixler
- training workflow leading toward MyTrainer
- verse correction workflow in MyVersifier

Characteristics:
- spans multiple steps and sometimes multiple modules
- is described in user-facing or architecture-facing terms
- can be resumed or inspected through persisted settings and project structure

Rules:
- Workflows describe intent and sequence
- Workflows may call multiple Processes
- Workflows should be visible in documentation, manifests, dialogs, and status reporting

### Process

A concrete executable transformation or operation inside a Workflow.

Examples:
- extract PDF pages
- convert TIFF to mono
- deskew image
- crop lines
- generate RIS payload
- initialize git repository
- update session JSON

Characteristics:
- narrower than a Workflow
- often implemented as a function, dialog action, worker task, or engine state step
- has inputs, outputs, and local validation

Rules:
- a Process should have one clear responsibility
- a Process may be synchronous or threaded
- a Process should not redefine broader workflow policy

### Stage

A named checkpoint or boundary inside a Workflow or Process chain.

Examples:
- `INIT`, `VALIDATE`, `PROVENANCE`, `RIS`, `WRITE`, `COMPLETE`
- image states such as source, mono, deskewed, cropped, line-boxed, ground-truth-ready
- folders under `Model/Project/Images/Workflow/*`

Rules:
- a Stage is a state boundary, not a UI module
- Stages should be stable enough to support replay, diagnostics, and user recovery
- Stage names should be meaningful in logs, manifests, and documentation

## 3. Structural Classes

### Module

A concrete application or code unit that exposes capabilities.

Examples:
- MyServer
- MyPixler
- MyBoxer
- MyWriter
- MyTrainer
- Core `ProjectCreationEngine`

Rules:
- Modules implement Processes and support Workflows
- Modules should not be treated as Workflows themselves, even when a module is the main entry point for a workflow
- module boundaries should remain explicit so future refactors do not collapse UI, orchestration, and processing into one layer

### UI Surface

A user-facing interaction layer such as a main window, dialog, wizard, or generated Designer UI.

Examples:
- MyServer main window
- Morphology dialog
- project creation wizard
- generated `.ui` and `*_UI.py` surfaces

Rules:
- a UI Surface gathers input, presents state, and triggers Processes
- UI Surfaces should not become the source of truth for business policy
- when the repo requires Designer-first ownership, the `.ui` file is the editable source of truth for layout

### Artifact

A durable file or folder produced, consumed, or transformed by the System.

Examples:
- `project.ris.json`
- `ProjectFolderList.txt`
- `Workflow.json`
- images in `Model/Project/Images/Workflow`
- corrected text files
- line boxes, glyph boxes, training assets

Rules:
- Artifacts belong either to the Workspace or to a Project; do not blur the two
- Artifact location should communicate lifecycle role where possible
- generated Projects should receive only artifacts required for runtime, provenance, or user work

### Reference Data

Shared reusable data that informs runtime behavior but is not the user’s direct work product.

Examples:
- shared JSON configuration
- shared language/reference mappings
- future MyWriter-managed `Model/Project/Data/esword`
- fonts and support assets needed by release/runtime workflows

Rules:
- Reference Data may be seeded into Projects when the runtime depends on it
- Reference Data should be curated carefully because it is the easiest class to over-copy into generated Projects
- `esword` remains intentionally preserved because it is expected to be generated and refreshed by MyWriter later

## 4. State Classes

### Session

User- or module-scoped persisted runtime state that helps restore context.

Examples:
- `Session.json`
- `PixlerSession.json`
- `ScannerSession.json`
- `VersifierSession.json`

Rules:
- Session state restores operator context; it is not a substitute for workflow provenance
- Session state may point to current project files or folders
- Session state should remain project-safe and path-aware across platforms where possible

### Event

An immutable record of a meaningful system transition.

Examples:
- project creation lifecycle events
- future replayable event-store entries

Rules:
- Events describe what happened
- Events should not be mutable state containers
- Event contracts should stay narrow, stable, and audit-friendly

## 5. Relationship Model

```text
System
  contains Workspace
  generates Projects

Project
  contains Artifacts, Session state, Workflow stages, and user outputs

Workflow
  coordinates Processes across Modules

Process
  transforms Artifacts and advances Stages

Module
  exposes UI Surfaces and implements Processes

Reference Data
  may be copied into Projects only when required by runtime behavior
```

## 6. Key Distinctions

### Project vs Workspace

- Project: user work product under the external Projects root
- Workspace: development tree of the application itself

### Workflow vs Process

- Workflow: ordered path toward a larger outcome
- Process: single executable transformation within that path

### Stage vs Process

- Stage: named state boundary
- Process: action that may move work from one Stage to another

### Module vs Workflow

- Module: concrete tool or code unit
- Workflow: business-level sequence that may use several Modules

### Reference Data vs User Output

- Reference Data: seeded, curated, reusable support content
- User Output: project-specific results created during OCR, correction, or training work

## 7. Design Invariants

- The System must distinguish generated Projects from the development Workspace.
- Project generation must remain curated; broad workspace payloads should not be copied by default.
- Workflows may cross module boundaries, but Processes should remain locally understandable and testable.
- UI Surfaces collect input and present state; they should not become the authoritative source of business policy.
- Reference Data must be explicitly curated, especially when deciding what belongs in generated Projects.
- MyTrainer remains an active future-facing module area, so training-related cleanup should distinguish between stale helper payloads and still-planned training workflows.

## 8. Current Application to This Repo

Current practical interpretation:
- `Core/engine.py` owns project-creation lifecycle Processes.
- `MyServer.py` owns UI orchestration and project/workflow entry points.
- `MyPixler.py` owns image-processing Processes and preview/apply behavior.
- `ProjectFolderList.py` curates which Workspace artifacts become Project artifacts.
- `PROJECT_CREATION_ARCHITECTURE.md` defines the project-creation contract.
- `PROJECT_ARCHITECTURE.md` describes the larger module landscape.
- this document defines the vocabulary that separates Project, Workflow, Process, Module, Stage, Artifact, Session, and Reference Data.

## 9. Recommended Use

Use this document when:
- deciding whether a file belongs in the repo Workspace or in generated Projects
- clarifying whether a request is about workflow design, process implementation, or UI behavior
- evaluating cleanup candidates
- discussing MyTrainer and future training architecture
- aligning documentation across architecture, project creation, and module-specific notes
