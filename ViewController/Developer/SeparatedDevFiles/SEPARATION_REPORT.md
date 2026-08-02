# Runtime and Developer Separation Report

Date: 2026-08-02
Branch: ubuntu_development

## Objective

Create a clear separation between runtime-facing ViewController modules and developer-only artifacts.

## Runtime Root Policy

Each runtime stage root now contains only entry modules and a helpers folder.

- ViewController/0-MainUI
- ViewController/1-PreProcess
- ViewController/2-TrainTesseract
- ViewController/3-Process
- ViewController/4-PostProcess

## Developer Files Destination

Developer-oriented files were moved under:

- ViewController/Developer/SeparatedDevFiles

Subareas used:

- ViewController/Developer/SeparatedDevFiles/0-MainUI
- ViewController/Developer/SeparatedDevFiles/1-PreProcess
- ViewController/Developer/SeparatedDevFiles/2-TrainTesseract
- ViewController/Developer/SeparatedDevFiles/3-Process
- ViewController/Developer/SeparatedDevFiles/4-PostProcess

## What Was Moved (Summary)

- Legacy migration and platform copy folders (Windows/Linux snapshots and backups)
- Notes/checklists and Copilot instruction artifacts
- Smoke test and ad-hoc debug files
- UI regeneration and font conversion tooling scripts
- Reference folders and stage archives moved out of runtime roots
- Cache folders such as __pycache__ moved out of runtime roots/helpers

## File Counts In SeparatedDevFiles

- 0-MainUI: 132 files
- 1-PreProcess: 25 files
- 2-TrainTesseract: 18 files
- 3-Process: 34 files
- 4-PostProcess: 43 files

## Manifest Updates

Path list files were updated to point moved developer artifacts to SeparatedDevFiles while preserving runtime module paths.

Updated manifests:

- ProjectFolderList.txt
- ViewController/GeneralProjectFolderList.txt
- ViewController/ScriptureProjectFolderList.txt
- ViewController/0-MainUI/helpers/ProjectFolderList.txt
- ViewController/0-MainUI/helpers/ScriptureProjectFolderList.txt
- ViewController/0-MainUI/helpers/ProjectFolderList.py

## Validation Performed

- Stale-reference checks for moved paths in manifests
- Runtime entry module import smoke tests in .venv
- Compile checks for retained runtime modules

Validation result: runtime import smoke checks returned exit code 0 for all retained entry modules across 0-MainUI, 1-PreProcess, 2-TrainTesseract, 3-Process, and 4-PostProcess.

## Notes

This report is intentionally concise. For exact file-level provenance, use git diff or git status from the repository root.
