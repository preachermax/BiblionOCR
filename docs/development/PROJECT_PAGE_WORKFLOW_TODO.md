# Project Page Workflow Architecture TODO

## Purpose

Track each source page through the full project lifecycle, including per-page and per-column progress, and expose active page context consistently across modules.

## Scope For This Initiative

- Extend project metadata schema for page-centric workflow tracking.
- Add Scriptural/Secular-specific structures for folders and workflow defaults.
- Surface key page workflow fields in module status bars.
- Integrate trackable fields with SessionManager.
- Build a tabbed Project Settings dialog (Qt Designer editable `.ui`) for Paths, Milestones, Values, and Folders.

## Proposed New Project Data Fields

- [x] `ProjectType` (enum): `Secular` or `Scriptural`
- [x] `ProjectPageNumber` (int): current source page number
- [x] `ProjectPageProgress` (percentage): lifecycle completion for current page
- [ ] `ProjectBook` (string, Scriptural only)
- [ ] `ProjectVerse` (string/int, Scriptural only)
- [ ] `ProjectWord` (string/int, Scriptural only)
- [x] `NumberColumns` (int, max `4`)
- [ ] `ColumnName` (list/string mapping): default `left`, `center`, `right`, user-renamable
- [x] `CurrentLanguage` (enum/list): installed Tesseract language codes
- [ ] `Notes` (text)

## Fields To Display In Every Module Status Bar

- [ ] `ProjectPageNumber`
- [ ] `ProjectPageProgress`
- [ ] `ColumnName` (active column context)
- [ ] `CurrentLanguage`

## Phase 1: Data Model And Validation

- [ ] Audit current schema definitions in Core project metadata and DB normalization.
- [ ] Add new field definitions, defaults, and validation rules.
- [ ] Add conditional validation rules for Scriptural-only fields (`ProjectBook`, `ProjectVerse`, `ProjectWord`).
- [ ] Define canonical storage format for columns:
  - [ ] `NumberColumns`
  - [ ] `ColumnName` list constrained by column count
  - [ ] active column pointer/index (if needed)
- [ ] Define `ProjectPageProgress` representation (`0-100` int preferred).
- [ ] Add migration/backfill behavior for older projects missing new fields.

## Phase 2: Folder Structures (Scriptural vs Secular)

- [ ] Define canonical folder templates for `Scriptural` projects.
- [ ] Define canonical folder templates for `Secular` projects.
- [ ] Ensure per-column folders are created under `Model/Project/Images/Source`.
- [ ] Add folder creation logic for column-aware pages.
- [ ] Add optional include/exclude behavior for generated folder sets.
- [ ] Decide whether to use:
  - [ ] separate template tables/lists by project type, or
  - [ ] one template with typed variants and toggles.

## Phase 3: Workflow Lifecycle Tracking Per Page

- [ ] Define page lifecycle stages and milestone events from source to final.
- [ ] Persist per-page state transitions and timestamps.
- [ ] Bind page lifecycle updates to existing module actions.
- [ ] Add helper APIs to get/set current page context across modules.
- [x] Add progress recalculation strategy for `ProjectPageProgress`.

## Phase 4: Status Bar Integration Across Modules

- [ ] Inventory all modules that need page context status badges/labels.
- [x] Add a shared status payload contract for page fields.
- [ ] Implement status bar widgets for:
  - [ ] page number
  - [ ] page progress
  - [ ] column name
  - [ ] current language
- [ ] Update event propagation so field changes refresh status bars in real time.

## Phase 5: SessionManager Tracking Integration

- [ ] Define which project fields are session-tracked vs project-persisted only.
- [ ] Add tracked field registration for new page workflow fields.
- [ ] Ensure session resume restores page context and active column/language.
- [ ] Verify interaction with current project root switching and module launching.

## Phase 6: Project Settings Dialog Redesign (Tabbed)

- [ ] Design a new tabbed `ProjectSettingsDialog` information architecture:
  - [ ] Paths
  - [ ] Milestones
  - [ ] Values
  - [ ] Folders
- [ ] Add folder include/exclude checkboxes for Scriptural/Secular template generation.
- [ ] Ensure values tab supports conditional Scriptural fields.
- [ ] Add language selector backed by installed Tesseract languages.
- [ ] Create Qt Designer editable UI file:
  - [ ] `ProjectSettingsDialogTabbed.ui` (proposed name)
- [ ] Wire UI -> model persistence and validation.

## Phase 7: Project Creation Wizard Updates

- [x] Extend project creation wizard fields for new schema values.
- [x] Add `ProjectType` decision point early in wizard.
- [x] Add initial page context defaults (`ProjectPageNumber`, `ProjectPageProgress`, etc.).
- [x] Add column configuration controls with sensible defaults.
- [x] Add language initialization from installed Tesseract language list.
- [ ] Ensure wizard output drives type-specific folder initialization.

## Phase 10: Workflow Wizard Rollout

- [x] Implement MyLauncher-first macro-style workflow wizard architecture.
- [x] Add Project Workflow Wizard and Page Workflow Wizard actions to MyLauncher Project menu.
- [x] Preserve manual launch actions while introducing macro orchestration.
- [x] Add initial NumberColumns update surfaces in MyServer and MyScanner.
- [ ] Propagate equivalent wizard workflow entry points to remaining modules.

## Phase 8: Testing And Migration Coverage

- [ ] Add unit tests for schema normalization and validation rules.
- [ ] Add tests for Scriptural vs Secular folder generation.
- [ ] Add tests for per-column folder creation under source images.
- [ ] Add tests for status bar field propagation.
- [ ] Add tests for SessionManager persistence/resume behavior.
- [ ] Add regression tests for legacy projects and migration paths.

## Phase 9: Documentation

- [ ] Update architecture docs with page-centric workflow model.
- [ ] Document field semantics and constraints.
- [ ] Document folder templates and include/exclude behavior.
- [ ] Document UI workflow for the tabbed settings dialog.
- [ ] Add developer notes for extending page lifecycle milestones.

## Open Design Decisions

- [ ] Confirm whether `ProjectVerse` and `ProjectWord` should be string or numeric.
- [ ] Confirm whether `ColumnName` is global-per-project or page-specific.
- [ ] Confirm whether `CurrentLanguage` is global, per-page, or per-column.
- [ ] Confirm whether page progress is milestone-count based or weighted by module stages.
- [ ] Confirm whether Scriptural/Secular should use separate DB tables or a typed unified table.

## Immediate Next Execution Slice

- [ ] Implement Phase 1 schema changes with defaults and migration.
- [ ] Add Phase 2 typed folder template generator.
- [ ] Add Phase 6 `ProjectSettingsDialogTabbed.ui` scaffold and basic wiring.
- [ ] Add initial status bar field widgets in MyServer as the reference implementation.
