# BiblionOCR-C++ Qt6 Migration Plan

Date: 2026-08-06
Scope: commercial Windows/Linux binary track for BiblionOCR-C++
Status: planning baseline

## Decision Summary

1. Preferred implementation path: Qt6 C++.
2. Migration objective: port PyQt5 runtime and UI behavior to a Qt6 C++ codebase with release-grade binary packaging.
3. Existing Designer-driven UI workflow should be preserved and modernized under Qt6.
4. Required intermediary bridge: migrate the OSS codebase from Qt5 Python to Qt6 Python before the Qt6 C++ product port.
5. Intermediary commercial repository name: BiblionOCR-PyQt6 (private).
6. Policy clarification: pre-release of Qt6 Python/PyQt6 is useful but not required before pre-releasing commercial Qt6 C++ binaries.

## Conversion Capability Statement

1. Full automatic conversion from PyQt5 Python to production-grade Qt6 C++ is not realistic as a one-shot transpile.
2. Assisted conversion is practical through architecture mapping, module-by-module porting, API surface adaptation, and test plus packaging automation.
3. Existing Python runtime can remain active while modules are incrementally replaced.

## Commercial Architecture Target

1. Runtime: Qt6 C++ desktop application suite.
2. UI: Qt Designer `.ui` source files with generated C++ UI bindings kept in lockstep.
3. Data: SQLite retained as primary local persistence layer.
4. Packaging targets include Windows self-contained installer package and Linux package profiles (AppImage/deb/rpm as selected per distribution strategy).
5. Compliance: third-party license inventory and bundled notices required per release.

## Migration Principles

1. Keep behavior parity before optimization.
2. Port shared core logic first, then module UIs in release order.
3. Preserve stable file and data contracts where possible.
4. Enforce test-before-commit and test-before-release gates.
5. Keep provenance ledger entries for every reused component.

## Intermediary Bridge: Qt5 Python OSS To Qt6 Python OSS

Objective:

1. Reduce migration risk by validating behavior and UI parity on Qt6 while still in Python.
2. Establish repeatable Python runtime installation standards for contributors and CI.
3. Produce reusable migration intelligence for BiblionOCR-PyQt6 without blocking commercial Qt6 C++ pre-releases.

Bridge scope:

1. Convert PyQt5 imports and API usage to Qt6-compatible Python bindings.
2. Keep Qt Designer `.ui` sources authoritative and regenerate runtime UI bindings.
3. Resolve Qt5 to Qt6 API changes in signals, enums, dialogs, and event handling.
4. Run module smoke tests and policy audits after each conversion slice.

Associated Python installation standards:

1. Windows OSS runtime profile: CPython 3.12 x64, dedicated `.venv` per repo clone, and pinned Qt6 Python binding package set in requirements lock file.
2. Linux OSS runtime profile: CPython 3.12 x64, dedicated `.venv` per repo clone, and the same pinned Qt6 Python binding package set as Windows.
3. CI profile: matrix validation on Windows and Linux using the same pinned dependency set.

Bridge exit criteria:

1. All targeted OSS modules run on Qt6 Python on Windows and Linux.
2. UI lockstep checks pass for `.ui` sources and generated runtime bindings.
3. Regression baseline is stable enough to begin Qt6 C++ porting by release order.
4. This bridge remains a quality accelerator, not a hard release gate for C++ binary pre-release.

## Phase Plan

### Phase 0: Baseline And Inventory

1. Freeze a baseline Python tag for reference.
2. Record module responsibilities, startup paths, and data contracts.
3. Build dependency and license inventory with binary distribution notes.
4. Define the Qt6 UI lockstep policy and generation workflow.

Exit criteria:

1. Approved architecture decision record.
2. Approved dependency/compliance inventory.
3. Approved parity checklist per module.

### Phase 0.5: OSS Qt6 Python Bridge

1. Migrate OSS runtime from Qt5 Python to Qt6 Python in controlled slices.
2. Standardize Windows/Linux Python installation profiles and dependency lock files.
3. Execute cross-platform smoke and behavioral parity checks after each slice.
4. Feed bridge findings into BiblionOCR-PyQt6 planning and implementation backlog.

Exit criteria:

1. OSS Qt6 Python baseline is stable on Windows and Linux.
2. Installer/setup documentation for contributor Python environments is validated.
3. Qt6 Python baseline is tagged as handoff reference for C++ migration.
4. C++ binary pre-release may proceed in parallel if C++ quality and compliance gates pass.

### Phase 1: Shared Core Port

1. Port project/session/workflow state models to C++.
2. Port database access and schema adapters.
3. Port workflow action policy and menu-governance rules.
4. Add compatibility bridge so Python modules can invoke migrated services during transition.

Exit criteria:

1. Core library test pass on Windows and Linux.
2. No behavioral regressions in shared state transitions.

### Phase 2: Module Port Sequence

Port in this order:

1. MyScanner
2. MyPixler
3. MyTrainer
4. MyWriter
5. MyReader

For each module:

1. Port menu/actions and startup behavior.
2. Port project status and workflow wiring.
3. Port persistence and inter-module handshakes.
4. Validate parity using scripted and manual test suites.

Exit criteria per module:

1. Startup smoke pass on Windows and Linux.
2. Functional parity checklist pass.
3. Packaging artifact generated and signed where applicable.

### Phase 3: Remaining Modules And Consolidation

1. Port remaining specialized modules.
2. Remove temporary compatibility bridges no longer needed.
3. Normalize diagnostics and telemetry.
4. Complete installer/upgrade/rollback pathways.

Exit criteria:

1. End-to-end workflow parity across full suite.
2. Stable release candidate binaries on both platforms.

## Quality Gates

Every migration slice must pass:

1. Build and static analysis gates.
2. Targeted unit/integration tests.
3. Startup smoke tests for changed modules.
4. Manual UI behavior checks for changed interaction surfaces.
5. License/provenance review before artifact publication.

## UI Lockstep Policy For Migration

1. Treat each `.ui` source and generated C++ UI binding as one atomic change set.
2. Block merges when UI source and generated bindings drift.
3. Add CI checks that compare expected action labels and menu wiring.
4. Keep Wizard wording canonical across UI source and generated/runtime bindings.

## Release Compliance Checklist

1. Third-party dependency license report completed.
2. Required notices bundled with binaries.
3. Trademark and naming review completed.
4. Paid support/tooling boundaries documented.
5. External OSS legal review completed before first public commercial binary.

## Risk Register (Initial)

1. UI parity drift between Designer source and generated C++ bindings.
Mitigation: enforce lockstep CI and visual/action audits.

2. Runtime behavior drift in workflow/menu policies.
Mitigation: port policy logic early and test it centrally.

3. Binary distribution licensing gaps.
Mitigation: maintain per-release compliance pack and legal signoff gate.

4. Performance or memory regressions in native paths.
Mitigation: baseline telemetry on Python runtime and compare each ported module.

## Immediate Next Execution Slice

1. Create architecture decision record for Qt6 Python intermediary bridge and Qt6 C++ target stack.
2. Define module-by-module parity checklists for MyScanner and MyPixler on the Qt6 Python bridge.
3. Standardize Windows/Linux contributor Python installation profiles and lock files.
4. Add CI pipeline with lockstep, bridge validation, and release-compliance checks.
