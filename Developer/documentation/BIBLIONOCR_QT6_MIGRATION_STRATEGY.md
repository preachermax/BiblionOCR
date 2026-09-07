# BiblionOCR Qt 6 Migration Strategy

## Purpose

This document defines how to create an isolated local descendant of BiblionOCR and migrate it from PyQt5/Qt 5 to Qt 6. The target repository may ultimately use PySide6 or PyQt6. PySide6 is the preferred candidate for the first implementation trial because its LGPL option may better fit commercial distribution, subject to a formal licensing review before any binary release.

The migration must not destabilize the current BiblionOCR repository or interrupt ongoing UI work and MyPixler debugging. The existing repository remains the Qt 5 source of truth until a Qt 6 acceptance gate is explicitly passed.

## Current Repository Facts

The migration starts with these verified conditions:

1. Runtime modules, tests, generated UI modules, and scanner code contain extensive direct `PyQt5` imports.
2. Qt Designer `.ui` files under `Developer/QtDesignerUI` are the editable UI authority.
3. `Developer/update_ui_resources.py` currently invokes `PyQt5.uic.pyuic` and `PyQt5.pyrcc_main` and selectively replaces only changed generated files.
4. Generated UI modules contain Qt 5 forms such as `QtWidgets.QAction` and `exec_()` that differ under Qt 6.
5. Runtime code uses PyQt-specific names such as `pyqtSignal` and `pyqtSlot`.
6. `requirements-qt-pdf.txt` currently pins `PyQt6==6.10.2`, while the active application remains predominantly PyQt5. Dependency manifests therefore need consolidation before they can be treated as authoritative.
7. The repository contains active runtime code as well as archives, references, backups, and moved candidates. Those historical trees must not be included in an automatic first-pass conversion.
8. BiblionOCR source is licensed under Apache License 2.0. The Qt binding and bundled-binary obligations must be evaluated separately.

## Target Outcome

The migration is complete when the new repository:

1. Uses exactly one selected Qt 6 binding in production builds.
2. Regenerates every active UI and resource module from its source file with the selected Qt 6 tools.
3. Contains no PyQt5 imports in active runtime, generated, launcher, or test code.
4. Starts all canonical modules on supported Windows and Linux versions.
5. Preserves project data, OCR workflows, page-state behavior, and inter-module handoffs.
6. Builds reproducible development and distributable environments without mixing Qt bindings.
7. Has a documented and reviewed licensing path for open-source and commercial distribution.

Use `BiblionOCR-Qt6` as the neutral working repository name until the binding decision is recorded. Rename it to `BiblionOCR-PySide6` or `BiblionOCR-PyQt6` only after the decision gate.

## Repository Isolation

### 1. Prepare a Stable Source Point

Do not clone an uncommitted working tree. Finish or checkpoint the current aesthetic UI work and MyPixler debugging first, then identify a tested commit on `ubuntu_development`:

```bash
cd ~/Projects/BiblionOCR
git status --short
git rev-parse HEAD
git tag -a qt5-migration-baseline-YYYY-MM-DD -m "Qt 5 baseline for Qt 6 migration"
git push origin qt5-migration-baseline-YYYY-MM-DD
```

Create the tag only when the baseline is intentionally ready and the user explicitly requests the commit/tag/push operation.

### 2. Create a Sibling Clone

Clone from Git history instead of copying the working directory. This preserves authorship, the Apache-2.0 history, and future comparison with the Qt 5 repository.

```bash
cd ~/Projects
git clone https://github.com/preachermax/BiblionOCR.git BiblionOCR-Qt6
cd BiblionOCR-Qt6
git switch ubuntu_development
git switch -c migration/qt6-foundation
```

Create an empty remote repository for the Qt 6 project, then retain the original repository as `upstream`:

```bash
git remote rename origin upstream
git remote add origin <new-BiblionOCR-Qt6-repository-URL>
git remote -v
git push -u origin migration/qt6-foundation
```

Never point both repositories at the same runtime-state directories through symlinks. Each checkout must have its own virtual environment, logs, output, caches, and mutable `Model/Project/Data/json` state.

### 3. Keep Environments Independent

```bash
cd ~/Projects/BiblionOCR-Qt6
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Create binding-specific dependency inputs during the trial:

- `requirements-qt6-common.txt`: non-Qt dependencies shared by both trials.
- `requirements-pyside6.txt`: common dependencies plus one pinned PySide6 version.
- `requirements-pyqt6.txt`: common dependencies plus one pinned PyQt6 version.

Do not install PyQt5, PyQt6, and PySide6 into the same migration environment. Separate virtual environments make import leakage and plugin-path conflicts visible.

## Change Synchronization Policy

The Qt 5 repository remains the source for current product work while the migration is experimental. Synchronize intentionally:

1. Finish and test a coherent Qt 5 change first.
2. Fetch it in the Qt 6 clone from `upstream`.
3. Cherry-pick narrowly when the change is independent, or merge a named baseline only at planned synchronization points.
4. Reapply binding-specific adaptations in a separate commit.
5. Never copy generated `UI.py` files from Qt 5 into the Qt 6 repository. Transfer `.ui` changes and regenerate them with the selected Qt 6 binding.
6. Record the latest incorporated Qt 5 commit in a migration ledger.

Suggested commit separation:

1. Upstream behavior/UI synchronization.
2. Qt 6 mechanical adaptation.
3. Qt 6 behavioral repair and tests.
4. Documentation or packaging changes.

This structure keeps regressions attributable and makes later upstream synchronization practical.

## Scope Classification Before Conversion

Build a machine-readable inventory and classify each Qt-bearing file as one of:

- `active-runtime`
- `generated`
- `test`
- `developer-tool`
- `archive-reference`
- `third-party-vendored`

Convert only the first four categories. Preserve archives and references as historical Qt 5 material unless an active module still imports them. Review bundled third-party code independently; do not mechanically rewrite it or assume BiblionOCR's license governs it.

The inventory should record:

- direct binding imports;
- signals, slots, properties, and thread classes;
- `exec_()` calls;
- Qt 5 enum syntax;
- classes moved between Qt modules;
- deprecated or removed Qt APIs;
- runtime `uic.loadUi` use;
- generated UI/resource source-target pairs;
- optional Qt components such as PDF, SVG, multimedia, print support, or WebEngine;
- tests that instantiate `QApplication` or require an offscreen platform.

Commit the inventory before conversion so progress can be measured rather than inferred from broad search totals.

## Binding Evaluation Gate

### PySide6 Candidate

Advantages to verify:

- Official Qt for Python binding.
- LGPLv3 licensing option in addition to GPL/commercial options.
- Qt Company tooling and documentation alignment.
- Signal names `Signal`, `Slot`, and `Property` avoid PyQt-specific terminology.

Obligations and risks to review:

- LGPL compliance for distributed binaries, including notices, license text, relinking/replacement rights, and any modifications to LGPL components.
- Licensing of Qt modules that are not offered under LGPL.
- Packaging behavior when Qt shared libraries and plugins are bundled.
- API differences from both PyQt5 and PyQt6.

### PyQt6 Candidate

Advantages to verify:

- Familiarity for a codebase currently using PyQt5.
- Similar PyQt signal/slot naming.
- Mature SIP-based ecosystem and tooling.

Obligations and risks to review:

- PyQt6 is generally offered under GPL or a commercial license, not LGPL.
- Closed-source commercial distribution generally requires an appropriate commercial license unless the complete distribution complies with the GPL.
- PyQt and Qt licenses are separate considerations.

### Decision Method

Create two short-lived branches from the same inventory commit:

```text
trial/pyside6-vertical-slice
trial/pyqt6-vertical-slice
```

Implement the same bounded vertical slice on both branches. The slice should include:

1. One generated Designer form and one resource file.
2. A simple application launcher.
3. A signal/slot worker interaction.
4. One shared dialog or workflow action.
5. One PDF or image-rendering path relevant to MyScanner/MyPixler.
6. Headless tests and a packaged smoke build on Windows and Linux.

Score each trial on:

- source changes required;
- generator reliability;
- type-checker quality;
- test and startup stability;
- PDF/image/scanner compatibility;
- packaging size and startup behavior;
- Windows and Linux plugin deployment;
- third-party dependency compatibility;
- commercial and open-source licensing requirements;
- maintenance burden for contributors.

Record the result in an architecture decision record. Current preference may be PySide6, but do not finalize the repository name or remove the alternate trial until this gate is complete.

Licensing statements in this document are planning guidance, not legal advice. Before distributing commercial binaries, inventory every Qt module and third-party library, retain applicable notices and source-offer/relinking materials, and obtain qualified legal review or written licensing guidance from the relevant vendor.

## Migration Architecture

### Prefer One Production Binding

Do not maintain two production bindings indefinitely unless there is a demonstrated product requirement. Dual-binding compatibility multiplies generated-file, enum, overload, packaging, and test combinations.

During the trial, isolate the small naming differences behind a temporary internal module only where useful. For example, a selected-binding module can expose `Signal`, `Slot`, and `Property`. Do not create wrappers for the whole Qt API; normal imports from the selected binding remain clearer after the decision.

### Preserve Designer as UI Authority

Keep `Developer/QtDesignerUI/*.ui` as source of truth. Extend `Developer/update_ui_resources.py` in the Qt 6 repository so it:

1. Selects one configured binding.
2. Uses `pyside6-uic` and `pyside6-rcc`, or PyQt6's `pyuic6` and `pyrcc6` equivalents.
3. Generates into temporary files.
4. Applies only documented deterministic headers or import adaptations.
5. Atomically replaces targets only when generated bytes differ.
6. Offers `--check` without writes.
7. Fails when the installed generator binding differs from the configured runtime binding.

Generated files must never be hand-ported. Regenerate one source-target pair, repair the runtime caller, validate it, and then proceed to the next pair.

### Keep Domain Logic Qt-Light

Where practical, move OCR, project-state, database, path, and workflow calculations behind plain Python interfaces before converting their UI callers. This is not a broad rewrite: extract only logic that currently blocks testing or forces Qt objects across ownership boundaries.

Use Qt signals and event-loop objects at UI/thread boundaries. Keep serializable state and core computations independent so they can be tested without a `QApplication`.

## Known Qt 6 Repair Categories

Each converted module must be checked for these changes rather than relying on import replacement alone:

1. Replace `exec_()` with `exec()` where required.
2. Update scoped enums, flags, and roles, such as `Qt.AlignmentFlag`, `Qt.ItemDataRole`, and class-specific enum types.
3. Import `QAction`, `QShortcut`, and related classes from `QtGui` where Qt 6 requires it.
4. Replace removed APIs such as `QDesktopWidget` and `QRegExp` with supported Qt 6 alternatives.
5. Review mouse, wheel, keyboard, drag/drop, and native event APIs whose position and enum return types changed.
6. Review overloaded signals and slots; PySide6 and PyQt6 can resolve overloads differently.
7. Normalize signal declarations to the selected binding (`Signal`/`Slot` for PySide6 or `pyqtSignal`/`pyqtSlot` for PyQt6).
8. Remove obsolete Qt 5 high-DPI application attributes and verify scaling on both platforms.
9. Verify `QImage`, `QPixmap`, buffer, and NumPy/OpenCV conversion semantics.
10. Verify thread shutdown, queued connections, and object ownership under the Qt 6 event loop.
11. Review `QFileDialog` return values, URL/path conversion, and model/view roles.
12. Verify resource import names and `:/Icons/...` paths after regeneration.
13. Replace binding-specific `sip` or `shiboken` assumptions deliberately.
14. Confirm PDF support uses the selected binding's available Qt PDF modules or the existing non-Qt `pypdf` path as appropriate.

## Phased Implementation

### Phase 0: Baseline and Safety Net

1. Finish the current UI update cycle and resume/complete the planned MyPixler debugging run in the Qt 5 repository.
2. Establish passing launcher, workflow, project-state, scanner, PDF, and image tests.
3. Record known failures, including platform-specific crashes, so they are not misattributed to Qt 6.
4. Capture representative screenshots and workflow fixtures for visual comparison.
5. Tag the approved Qt 5 baseline.

Exit gate: the exact source commit, test results, known failures, and supported platforms are recorded.

### Phase 1: Clone and Inventory

1. Create the sibling clone, independent environment, new remote, and migration branch.
2. Classify Qt-bearing files by ownership and activity.
3. Consolidate dependency inputs without changing runtime behavior.
4. Add a CI matrix skeleton for Linux and Windows.

Exit gate: the clone reproduces the Qt 5 baseline and the active migration scope is explicit.

### Phase 2: Parallel Binding Trials

1. Create equal PySide6 and PyQt6 trial branches.
2. Parameterize the selective generator only as far as needed for the trial.
3. Port the same small launcher/dialog/worker/media slice.
4. Test source execution and packaged execution on both platforms.
5. Complete the licensing and dependency-module inventory.

Exit gate: a written decision selects one production binding with evidence.

### Phase 3: Shared Foundation

1. Pin the selected binding and remove the alternate binding from the production environment.
2. Finalize Qt 6 UI/resource generation and drift checks.
3. Convert shared dialogs, event helpers, project-state UI boundaries, icons, themes, and launcher utilities.
4. Add reusable test fixtures for one `QApplication`, temporary project state, and headless execution.

Exit gate: shared infrastructure and one simple canonical launcher run without PyQt5.

### Phase 4: Product 1 Vertical Slice

Use MyScanner as the first product-level vertical slice because it is BiblionOCR Product 1, but do not call it release-ready merely because it launches.

Convert together:

- MyScanner runtime and generated UI;
- `Core/Scanner` dependencies;
- device discovery and worker threads;
- image preview/conversion boundaries;
- project and workflow integration;
- launcher paths and scanner-focused tests.

Use real-device tests where hardware is available and deterministic mock-device tests in CI. Test cancellation, no-device, permission-denied, malformed-image, and shutdown paths.

Exit gate: MyScanner passes the Product 1 readiness checklist on Windows and Linux with licensing and packaging evidence still tracked as separate gates.

### Phase 5: Remaining Modules

Migrate by dependency order, not directory-wide replacement:

1. MyLauncher and MyServer coordination surfaces.
2. MyExplorer and shared file/project dialogs.
3. MyPixler, including the page workflow wizard and PDF/image viewer path.
4. Remaining preprocessing and training modules.
5. Processing and post-processing modules.
6. Developer extensions and active utilities.
7. Tests and documentation in lockstep with each module.

For every module, convert `.ui` source, generated output, runtime wiring, tests, and launcher in one bounded change set.

### Phase 6: Packaging and Release Qualification

1. Build clean Windows and Linux artifacts from pinned dependencies.
2. Audit bundled Qt libraries, plugins, image formats, platform plugins, and optional modules.
3. Generate third-party notices and license materials from the actual artifact contents.
4. Test installation, first launch, upgrades, data migration, and uninstall behavior.
5. Run the full workflow and launcher matrix on clean machines or clean virtual machines.
6. Measure startup time, memory, artifact size, and OCR/image performance against the Qt 5 baseline.
7. Conduct accessibility, high-DPI, multi-monitor, keyboard, and visual regression checks.

Exit gate: release evidence supports the chosen open-source and commercial distribution model.

## Per-Module Change-Set Gate

Every migration change set must satisfy all of the following:

1. The `.ui` source and generated Python module are in lockstep.
2. Regeneration changes no unaltered target files.
3. Active code in scope contains no PyQt5 import or Qt 5-only API.
4. Touched Python files compile and pass type analysis.
5. Focused unit and integration tests pass.
6. The module starts without traceback on the active platform.
7. Menus, shortcuts, icons, dialogs, drag/drop, threads, and shutdown are exercised where applicable.
8. Project/session state is written only inside the Qt 6 checkout's test or runtime area.
9. The Qt 5 behavior baseline is preserved unless a deliberate behavior change is documented.
10. The migration ledger records the source baseline, files converted, tests run, and residual risks.

## CI and Test Matrix

Minimum continuous validation:

| Axis | Required coverage |
| --- | --- |
| Operating system | Ubuntu 24.04 and a supported Windows release |
| Python | One pinned production version, then the next candidate version |
| Binding | Selected production binding only after the decision gate |
| Display | Native display smoke and headless/offscreen tests where supported |
| Generation | `--check` proves no UI/resource drift |
| Runtime | Canonical launcher smoke tests |
| Data | Temporary clean project plus a copied representative project fixture |
| Packaging | Source checkout and frozen/bundled artifact |

GUI test crashes must be investigated as process-level failures, not treated as ordinary assertion failures. Keep subprocess isolation for tests involving native plugins, scanner drivers, PDF rendering, or event-loop teardown.

## Rollback and Stop Conditions

Keep the Qt 5 repository buildable throughout migration. Stop expansion and repair the current phase when any of these occurs:

- project data is corrupted or written across checkout boundaries;
- the generated source-target relationship becomes ambiguous;
- both bindings enter one production environment;
- a required Qt module has unresolved commercial licensing terms;
- scanner, PDF, image, or platform plugins cannot be packaged reproducibly;
- a module only works through hand-edited generated code;
- native crashes lack a minimal isolated reproduction;
- the migration requires an unrelated architectural rewrite to proceed.

Rollback is normally a branch reset or revert inside the Qt 6 repository, never a rewrite of the stable Qt 5 repository. Preserve failed trial branches long enough to document why they failed.

## First Execution Milestone

After the current aesthetic updates and MyPixler debugging cycle are complete, the first migration milestone should be:

1. Approve and tag a tested Qt 5 baseline.
2. Create the isolated `BiblionOCR-Qt6` sibling clone and remote.
3. Produce the active-file Qt dependency inventory.
4. Create separate PySide6 and PyQt6 trial environments and branches.
5. Port one identical generated-form, worker-signal, and image/PDF vertical slice.
6. Record a binding decision with licensing, packaging, and maintenance evidence.

No full-repository conversion should begin before that milestone is reviewed.
