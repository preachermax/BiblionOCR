# Workflow Wizard Phase 1 (2026-08-05)

## Summary

This phase introduces the first production implementation of macro-like workflow orchestration driven by ViewController numbered stage folders.

The implementation is intentionally narrow:

- establish architecture and procedural contract
- integrate with MyLauncher first
- preserve all existing manual module-launch paths
- add shared project metadata updates for columns-per-page from MyServer and MyScanner

No broad module-by-module workflow takeover is included in this phase.

## Why This Is A Major Step

This change moves workflow execution from only ad hoc operator navigation to a dual-mode model:

- manual mode: existing direct module launches remain unchanged
- guided macro mode: stage-scoped and full-sequence launch macros are now available through dedicated workflow wizards

This creates a stable contract for future workflow governance while avoiding immediate regressions in current production behavior.

## Architectural Additions

### 1. Shared Wizard Class

- Added: ViewController/0-MainUI/helpers/workflow_stack_wizard_dialog.py
- Responsibility:
  - stacked stage navigation UI
  - stage-level macro trigger
  - full workflow macro trigger

### 2. MyLauncher Workflow Orchestration

- Updated: ViewController/0-MainUI/MyLauncher.py
- Added capabilities:
  - derive ordered stages from ViewController numbered folders (0-MainUI, 1-PreProcess, 2-TrainTesseract, 3-Process, 4-PostProcess)
  - map stages to module launch steps
  - expose project workflow wizard and page workflow wizard entry points
  - run stage-only or full macro launch sequence

### 3. UI Action Surface (Code + Designer)

- Updated generated UI modules:
  - ViewController/0-MainUI/MyLauncherUI.py
  - ViewController/0-MainUI/MyServerUI.py
  - ViewController/0-MainUI/MyScannerUI.py
- Updated Qt Designer sources:
  - Developer/QtDesignerUI/MyLauncherUI.ui
  - Developer/QtDesignerUI/MyServerUI.ui
  - Developer/QtDesignerUI/MyScannerUI.ui

New action entries:

- MyLauncher Project menu:
  - Project Workflow Wizard
  - Page Workflow Wizard
- MyServer Project menu:
  - Set Columns Per Page
- MyScanner File menu fallback:
  - Set Columns Per Page

## Project/Page Workflow Boundary

The procedural split for this phase is:

- Project workflow administration remains anchored in MyServer.
- Page-oriented macro entry is provided from MyLauncher.
- Scanner receives a fallback menu entry for columns-per-page updates where a Project menu is not present.

## Shared Metadata Update Contract

- Added: ViewController/0-MainUI/helpers/project_column_settings.py
- Functions:
  - resolve project metadata sqlite path
  - update NumberColumns and NumberPageBoxes atomically through Core.project_database normalization flow

Runtime integrations:

- MyServer set-columns action updates project metadata and refreshes status surface.
- MyScanner set-columns action updates project metadata and refreshes status surface.

## Validation Completed

Targeted regression checks passed using sanitized Qt runtime invocation:

- env -u LD_LIBRARY_PATH QT_QPA_PLATFORM=offscreen python -m pytest -q tests/test_launcher_registry_integration.py tests/test_launcher_entrypoint_compatibility.py tests/test_gui_runtime_env.py

Exit status: 0

## Procedural Rule Adopted For Rollout

For this initiative, changes are split into explicit commits by architectural layer:

1. Phase 1 foundation commit:

- shared wizard class
- MyLauncher wizard orchestration
- initial Server/Scanner column-sync action integration
- documentation

1. follow-up module rollout commits:

- apply equivalent workflow wizard entry and behavior to remaining modules in controlled slices

This prevents a large, mixed commit that is hard to test, review, or rollback.

## Non-Goals In This Phase

- no removal of any existing manual action path
- no forced wizard-only workflow
- no broad behavior rewrite of module internals
- no milestone weighting model changes beyond existing ProjectTracking behavior

## Next Rollout Target (After This Commit)

- propagate wizard entry surfaces and contextual workflow guidance to remaining modules
- keep menu policy: Project menu when available, otherwise File menu fallback
- maintain compatibility with existing launchers and session behavior
