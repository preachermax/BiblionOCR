# Biblion Documentation Library

## Purpose

This directory is the documentation root for the Biblion project.

It exists to preserve the project’s vision, architecture, research, engineering state, and publication direction in one version-controlled library.

Code explains implementation.

The documentation library explains intent, structure, history, and long-term direction.

---

## Start Here

If you are orienting yourself to the documentation set, start with these files in order:

1. [DOCUMENTATION_ARCHITECTURE.md](DOCUMENTATION_ARCHITECTURE.md)
2. [PROJECT MANIFESTO.md](PROJECT%20MANIFESTO.md)
3. [THE_BIBLION_PROJECT.md](vision/THE_BIBLION_PROJECT.md)
4. [PROJECT_ARCHITECTURE.md](architecture/PROJECT_ARCHITECTURE.md)
5. [DEV_NOTEBOOK.md](development/DEV_NOTEBOOK.md)

---

## Directory Map

### `vision/`

High-level purpose, philosophy, and long-term identity.

Key documents:
- [THE_BIBLION_PROJECT.md](vision/THE_BIBLION_PROJECT.md)

### `architecture/`

System structure, module boundaries, and major runtime contracts.

Key documents:
- [PROJECT_ARCHITECTURE.md](architecture/PROJECT_ARCHITECTURE.md)
- [PROJECT_CREATION_ARCHITECTURE.md](architecture/PROJECT_CREATION_ARCHITECTURE.md)

### `development/`

Active engineering notebook, developer references, runtime notes, and implementation-facing support documents.

Key documents:
- [DEV_NOTEBOOK.md](development/DEV_NOTEBOOK.md)
- [DESIGN_SPECIFICATION.md](development/DESIGN_SPECIFICATION.md)
- [README_HELP_SYSTEM.md](development/README_HELP_SYSTEM.md)
- [QUICK_REFERENCE.md](development/QUICK_REFERENCE.md)

### `research/`

Supporting scholarship, technical investigation, and background material.

### `publications/`

Publication-facing writing and editorial support material.

### `community/`

Contributor-facing and participation-oriented project material.

### `roadmap/`

Forward-looking planning, milestones, and future initiatives.

### `website/`

Website planning, structure, and public presentation material.

Key documents:
- [README.md](website/README.md)

Current prototype highlights:
- React + Cytoscape demo under `docs/website/`
- EventBus + EventRunner + EventGraphExecutor runtime path for demo traversal
- traceable event logging, state inspection, and visited-node highlighting in the graph view

### `patreon/`

Funding and supporter-oriented planning material.

### `archive/`

Historical documents that should be retained for context rather than deleted.

---

## Documentation Rules

- `docs/` is the authoritative knowledge library for Biblion.
- Architecture changes should be reflected in the relevant architecture and development documents.
- The active engineering notebook is [DEV_NOTEBOOK.md](development/DEV_NOTEBOOK.md).
- The current domain vocabulary is defined in [DESIGN_SPECIFICATION.md](development/DESIGN_SPECIFICATION.md).
- Documents should cross-reference one another rather than duplicating full content where practical.

### Migration Note

The documentation library is replacing older markdown locations that previously lived at the repository root and under `ViewController/0-MainUI/`.

When both an older path and a `docs/` path exist conceptually, prefer the `docs/` location as the current source of truth.

---

## Follow-Up Pointers

Use this README to decide where new documentation belongs:

- project meaning or mission → `vision/`
- software structure or contracts → `architecture/`
- active implementation state or debugging notes → `development/`
- supporting investigation → `research/`
- outward-facing publishing material → `publications/`

When a document feels misplaced, move or rewrite it so the directory purpose remains clear.

---

## Related Documents

- [DOCUMENTATION_ARCHITECTURE.md](DOCUMENTATION_ARCHITECTURE.md)
- [PROJECT MANIFESTO.md](PROJECT%20MANIFESTO.md)
- [PROJECT_ARCHITECTURE.md](architecture/PROJECT_ARCHITECTURE.md)
- [DEV_NOTEBOOK.md](development/DEV_NOTEBOOK.md)
- [DESIGN_SPECIFICATION.md](development/DESIGN_SPECIFICATION.md)
- [website/README.md](website/README.md)

---

*Documentation preserves understanding.*

*Biblion is intended to preserve both software and the reasons it exists.*
