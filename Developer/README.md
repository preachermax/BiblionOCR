# Developer Extensions

Developer capabilities are installed and launched outside production application menus.

## Development Workflow Documentation

Operational documents used during module development live in `Developer/documentation`:

- [Change-Set Prompt Pack](documentation/CHANGESET_PROMPT_PACK_2026-08-07.md)
- [Development Routine Checklist](documentation/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md)
- [Development Routine Playbook](documentation/DEVELOPMENT_ROUTINE_PLAYBOOK.md)
- [Development Notebook](documentation/DEV_NOTEBOOK.md)
- [BiblionOCR Qt 6 Migration Strategy](documentation/BIBLIONOCR_QT6_MIGRATION_STRATEGY.md)

## Human Developer Workflow

Human developers use the workflow wizard instead of manually tracking the development checklist. Launch it from the repository root.

Linux:

```bash
.venv/bin/python -m Developer.Developer
```

Windows:

```powershell
.venv\Scripts\python.exe -m Developer.Developer
```

The wizard preserves freedom over design, implementation, and Copilot collaboration. It requires developers to define the goal, anchor the investigation in evidence, state a falsifiable hypothesis, bound the change set, and choose the smallest appropriate validation.

### Mandatory Pre-PR Requirements

The wizard enforces 19 evidence gates drawn from the repository checklist. Universal gates must pass with evidence. Conditional gates may be marked `Not applicable` only when the wizard offers that status and the developer supplies a factual justification.

Required evidence includes:

- explicit requirement, module, intended files, and excluded work;
- preservation of unrelated worktree changes;
- production UI source/generated/runtime lockstep when UI changes;
- workflow, page-state, file-picker, and removed-control audits when affected;
- full-workspace and in-scope Problems totals;
- focused tests, compilation/static checks, runtime smoke checks, and manual UI observations as applicable;
- the canonical launcher smoke result;
- final diff, staged scope, branch, remote, documentation, risk, and handoff status;
- architecture evidence when the architecture-normalization lane applies;
- confirmation that contribution proceeds only through PR and review.

Evidence must name commands and outcomes, observed behavior, files or symbols reviewed, or a concrete reason a conditional gate is unaffected. `Done`, `checked`, a failing command, or lack of time is not sufficient evidence and is not a valid reason to select `Not applicable`.

### PR Eligibility

The wizard will not advance to its final PR handoff until all gates are resolved. **Save Draft Report** remains available during incomplete work. After the wizard reports `PR ELIGIBLE`:

1. Complete the handoff and risk notes.
2. Use **Copy PR Evidence**.
3. Replace the corresponding placeholder in the pull request template with the complete generated block.
4. Request Copilot/agent review and then repository owner/maintainer approval.

The repository Action validates the gate version, required declarations, and all 19 evidence rows. `PR ELIGIBLE` does not guarantee acceptance or replace technical review. Inaccurate, vague, or irrelevant evidence can still cause the PR to be returned for correction.

Draft and final Markdown reports are written only to a developer-selected location. The wizard does not transmit data, edit source code, run tests, commit, push, or open a PR automatically. Press F1 or use **Help** for Overview, Requirements, Usage Guide, Development, and About content.

## Extension Manager

Launch the manager from a development checkout:

```bash
.venv/bin/python -m Developer.extension_manager_dialog
```

The manager discovers bundled extensions under `Developer/extensions`, installs them into the current user's application-data directory, lists services declared by installed extensions, and dynamically opens a selected service.

Default installation roots:

- Linux: `$XDG_DATA_HOME/BiblionOCR/extensions` or `~/.local/share/BiblionOCR/extensions`
- Windows: `%LOCALAPPDATA%/BiblionOCR/extensions`
- macOS: `~/Library/Application Support/BiblionOCR/extensions`

Set `BIBLIONOCR_EXTENSION_HOME` to use an explicit extension root for development or testing.

## First Extension

`developer-services` is the first bundled installable extension. Its first service is Developer Backup/Restore, which creates development snapshots and non-destructive staged restores.

## Adding Services

Each extension directory contains an `extension.json` schema-version 1 manifest. Add future services to its `services` array:

```json
{
  "id": "service-id",
  "name": "Visible Service Name",
  "description": "Short purpose statement.",
  "entry_point": "module.py:DialogClass"
}
```

Extension and service IDs use lowercase letters, digits, and hyphens. Entry-point modules must remain inside the installed extension directory. A UI service class must be constructible with `parent=<QWidget>` and behave as a Qt dialog or window.

The current installer accepts bundled extensions only. Support for third-party package trust, signatures, dependency resolution, and remote catalogs is intentionally deferred.
