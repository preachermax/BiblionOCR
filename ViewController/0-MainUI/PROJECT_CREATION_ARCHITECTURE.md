# Project Creation Architecture

## Version 1.4 — ProjectFolderList Runtime Contract

**Status:** Active implementation contract  
**Scope:** MyServer, Core project engine, RIS generation, event emission, local Git project creation, ProjectFolderList structure generation  
**Last updated:** 2026-07-04

---

## 1. Current Runtime State

New project creation is being normalized around `Core/engine.py`.

Current rules:

* Projects are created under the user Projects folder.
* Windows target: `C:/Users/Max/Projects`.
* Runtime expression: `os.path.join(os.path.expanduser("~"), "Projects")`.
* Each project must be initialized as a local Git repository.
* Project folder structure should be generated from `ProjectFolderList.txt`.
* File entries in `ProjectFolderList.txt` are treated as parent-directory requirements.
* Empty directories receive `.gitkeep` placeholders so Git can track them.
* The curated manifest must stay project-safe: new projects should include runtime JSON data, the `Model/Project/Data/esword` tree reserved for future MyWriter generation/update workflows, and minimal workflow/training scaffolding, but should not expand broad `Model/Project/Data/SQLite`, `Model/Project/Data/csv`, or deep historical training payloads by default.

Temporary implementation note:

* `MyServer.py` still contains local Core-style project creation classes.
* Long-term target is to make `Core/engine.py` the single source of truth and reduce `MyServer.py` to UI/controller wiring.
* The current `MyServer` entry path now uses a guided two-step modal dialog instead of chained text prompts.
* New project dialogs should follow the same stacked-label, direct-action format already used by existing BiblionOCR custom dialogs.
* The dialog supports optional loading of user-provided provenance files in `json`, `ris`, `txt`, or `csv` format to prefill required provenance fields before project creation starts.
* The provenance file picker now opens from the user Projects root rather than defaulting to `Downloads`.
* The second step includes an in-dialog review summary before project creation is dispatched to the worker.
* The new `Open Project` action and MyExplorer entry path both start from the same user Projects root, so project selection and file browsing share a single top-level anchor.

---

## 2. Required Project Creation Output

A valid project should include:

```text
<ProjectName>/
├── .git/
├── .gitignore
├── README.md
├── project.ris.json
├── src/
│   └── manifests/
│       └── ProjectFolderList.txt
├── assets/
├── logs/
│   └── processing/
│       └── project_folder_list_structure_rebuild.md
├── output/
├── Model/
│   └── Project/
└── ViewController/
```

The full `Model/Project/...` and `ViewController/...` directory tree is derived from `ProjectFolderList.txt`.

Manifest curation rules for new-project generation:

* Keep `Model/Project/Data/json` contents needed by runtime modules.
* Keep `Model/Project/Data/esword` contents and placeholders; MyWriter is expected to generate and refresh that data later.
* Keep minimal image workflow folders and the top-level `Model/Project/Training` scaffold.
* Exclude heavy data trees such as `Model/Project/Data/SQLite`, `Model/Project/Data/csv`, and deep training support payloads unless there is an explicit one-off regeneration case.

---

## 3. Core Engine Structure Generation

`Core/engine.py` now supports:

* optional `folder_list_path` constructor argument
* automatic discovery of `ProjectFolderList.txt`
* default scaffold folders if no list is found
* ProjectFolderList-driven directory creation
* `.gitkeep` placeholder creation for empty folders
* copying the source folder list into `src/manifests/ProjectFolderList.txt`
* writing a rebuild log to `logs/processing/project_folder_list_structure_rebuild.md`
* emitting `project_structure_created`

Folder list search order:

1. explicit `folder_list_path`
2. `ProjectFolderList.txt` under current working directory
3. `ViewController/0-MainUI/ProjectFolderList.txt` under current working directory
4. `ProjectFolderList.txt` under repository root
5. `ViewController/0-MainUI/ProjectFolderList.txt` under repository root

---

## 4. Required RIS Payload Fields

The project creation payload must include:

```json
{
  "project_name": "ProjectName",
  "project_purpose": "Purpose text",
  "creation_trigger": "MyServer_button",
  "source_context": "MyServer_UI",
  "user_intent_summary": "Intent summary"
}
```

The engine adds runtime metadata such as:

* `ris_version`
* `timestamp`
* `_locked`
* `_hash`

UI collection notes:

* `project_name`, `project_purpose`, and `user_intent_summary` remain required before creation starts.
* `creation_trigger` and `source_context` default to `MyServer_button` and `MyServer_UI` but may be overridden by a loaded RIS file.
* `creator` is optional and is preserved when present in a loaded RIS file.
* Current UI flow: RIS import step, then project details and review step.
* Required fields should show in-dialog validation cues and block final submission until the payload is complete.
* Imported provenance metadata should be preserved in the final project RIS payload under source-provenance fields when available.
* Project name normalization should be visible inside the dialog before submission so the final folder name is not a surprise.

---

## 5. State Machine

Current intended lifecycle:

```text
INIT
  ↓
VALIDATE
  ↓
PROVENANCE
  ↓
RIS
  ↓
WRITE
  ↓
COMPLETE
```

Failure at any step should transition to:

```text
FAILED
```

Rollback support still needs to be normalized between `MyServer.py` and `Core/engine.py`.

---

## 6. Event Contract

Events should follow this shape:

```json
{
  "event": "event_name",
  "timestamp": 0.0,
  "state": "STATE_NAME",
  "project_name": "ProjectName",
  "metadata": {}
}
```

Expected events include:

| Event | Meaning |
| --- | --- |
| `validation_passed` | Project name and destination passed validation |
| `provenance_captured` | RIS/provenance payload captured and locked |
| `ris_generated` | Runtime RIS metadata generated |
| `project_structure_created` | ProjectFolderList/default folder structure created |
| `git_repository_initialized` | Local Git repository initialized |
| `filesystem_written` | Project folder committed to disk |
| `project_created` | Project creation complete |
| `project_failed` | Project creation failed |

---

## 7. Git Requirement

Every new project must be a local Git repository.

Required commands during project creation:

```text
git init
git branch -M main
```

The engine writes:

* `README.md`
* `.gitignore`

---

## 8. Import / UI Guardrails

Do not reintroduce invalid generated-UI imports.

`MainUI.py` does **not** define:

* `MainWindow`
* `MainUI`
* `RISDialogController`

Current correct runtime model:

* `MainWindow` lives in `MyServer.py`.
* Generated UI class comes from `MyServerUI.py`.

---

## 9. Testing Checklist

For each new project creation test:

* [ ] `Core/engine.py` imports and compiles.
* [ ] New project appears under `C:/Users/Max/Projects`.
* [ ] `.git/` exists.
* [ ] `project.ris.json` exists.
* [ ] `README.md` exists.
* [ ] `.gitignore` exists.
* [ ] `src/manifests/ProjectFolderList.txt` exists.
* [ ] `logs/processing/project_folder_list_structure_rebuild.md` exists.
* [ ] `Model/Project/Data/json` exists.
* [ ] `Model/Project/Images/Workflow/pixler/pixler_pages_cropped` exists.
* [ ] `ViewController/0-MainUI` exists.
* [ ] Empty directories contain `.gitkeep` where needed.

---

## 10. Next Implementation Steps

1. Add per-step validation cues and field-level feedback inside the new project dialog.
2. Remove duplicate project engine logic from `MyServer.py`.
3. Add registry writing to Core or define a Core registry event consumed by MyServer.
4. Add rollback cleanup to Core project creation failures.
5. Add SQLite event loading and replay.

---

## 11. Open Behavior Contract

`MyServer` project/file entry points should follow these defaults:

* `Open Project` starts from `os.path.join(os.path.expanduser("~"), "Projects")` and validates the selected folder as a BiblionOCR project root before launching `MyExplorer` there.
* Shared file-open pickers should prefer the current working file/folder when present, otherwise fall back to the same Projects root.
* `MyExplorer` should accept an explicit startup directory from `MyServer` and default to the user Projects root when no project-specific path is supplied.

---

## 12. Design Statement

Project creation must produce a traceable, RIS-backed, locally version-controlled project artifact with a deterministic folder structure generated from `ProjectFolderList.txt`.