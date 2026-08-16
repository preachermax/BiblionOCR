# BiblionOCR Change-Set Prompt Pack

Date: 2026-08-07
Purpose: Reduce prompt-writing overhead while preserving safety, module boundaries, and validation discipline.

## Operating Intent Locked In

- Work one module per change set unless user explicitly requests a grouped rollout.
- MyLexer is intentionally deferred as a required placeholder and must remain untouched until user audit reaches it.
- Preserve existing custom context-menu defaults.
- Keep UI lock-step: edit Designer source first, then regenerate paired UI.py.
- Treat inferred workflow sequence (menu + toolbar order) as provisional baseline only.
- Re-establish and edit exact step order per module during each prompt-pack pass.
- Remove redundant MyExplorer controls rather than hiding them, and do not change wording unless requested.
- Do not claim clean unless full workspace Problems scan is clean.
- Report both counts every cycle:
  - Full workspace Problems total.
  - In-scope module/file Problems total.

## Universal Prompt Header (Strict)

Use this as the opening block for every module prompt:

You are making one bounded change set in BiblionOCR.

Rules:

1. Scope only this module and its directly required shared helper touches.
2. Do not modify MyLexer under any circumstance (deferred placeholder until user audit reaches it).
3. Preserve existing custom context-menu defaults.
4. Keep UI lock-step:
   - edit Developer/QtDesignerUI/[MODULE_UI].ui as source of truth,
   - regenerate paired ViewController/.../[MODULE_UI].py with pyuic5,
   - avoid manual drift in generated UI.py.
5. Treat inferred workflow sequence (menu + toolbar order) as a default starting point only.
6. Re-establish exact step ordering from real module behavior and edit as needed.
7. Remove redundant MyExplorer controls if found; do not just hide/disable them.
8. Before completion, run full workspace Problems scan and report:
   - full workspace count,
   - in-scope count.
9. If either count is non-zero, continue fixing until both are zero or report blocker with exact file and reason.
10. Never revert unrelated existing changes.
11. Follow the DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md for each change set and pause before committing.

Output format required:

- Files changed.
- Behavior changed.
- Workflow sequence delta from inferred baseline (what was re-ordered and why).
- Validation commands run.
- Problems totals (full + in-scope).
- Residual risks (if any).

## Universal Prompt Footer (Lean)

Use this short close when you want speed:

Validate with full workspace Problems, py_compile for touched Python files, and a quick module startup smoke run if entrypoint changed. Report full count and in-scope count separately. Stop only at zero or with a concrete blocker.

## Quick Start (2-Minute Use)

1. Pick the next module from the queue below.
2. Copy the strict header.
3. Copy that module Task and Likely paths.
4. Add the lean footer.
5. Send the combined prompt as-is.

Minimal copy/paste command prompt:

Run the module prompt from docs/development/CHANGESET_PROMPT_PACK_2026-08-07.md for [MODULE_NAME] exactly as written (strict header + module task + lean footer). Keep MyLexer deferred and untouched. Report files changed, behavior changed, validation commands, full workspace Problems count, and in-scope count.

Expected completion response shape:

- Files changed.
- Behavior changed.
- Validation commands run.
- Problems totals: full workspace total and in-scope total.
- Residual risks.

## Module Prompt Queue (Copy/Paste)

### 1) MyServer

Status: Part 1 completed and accepted on 2026-08-16. Part 2 is reserved for follow-up debugging.

Apply the strict header above.

Task:

- Audit and fix MyServer runtime and UI lock-step only.
- Confirm file-picker and drag/drop behavior remains replacement-only and stable.
- Preserve existing context-menu defaults.
- Remove any remaining redundant MyExplorer controls in MyServer surfaces.
- Regenerate paired UI.py from Designer source if UI changed.

Likely paths:

- Developer/QtDesignerUI/MyServerUI.ui
- ViewController/0-MainUI/MyServer.py
- ViewController/0-MainUI/MyServerUI.py
- Core/workflow_wizard_actions.py (only if strictly required by MyServer behavior)

Append the lean footer.

### 2) MyScanner

Apply the strict header above.

Task:

- Audit MyScanner menu actions, file-picker wiring, and panel drag/drop acceptance.
- Preserve existing context-menu defaults.
- Keep all UI and runtime changes lock-step.

Likely paths:

- Developer/QtDesignerUI/MyScannerUI.ui
- ViewController/0-MainUI/MyScanner.py
- ViewController/0-MainUI/MyScannerUI.py
- Core/workflow_wizard_actions.py (only if required)

Append the lean footer.

### 3) MyBoxer

Apply the strict header above.

Task:

- Audit MyBoxer for replacement-only picker behavior and panel drag/drop acceptance.
- Keep existing context-menu defaults and WordBox surfaces intact.
- Regenerate UI.py from Designer source if any UI edits occur.

Likely paths:

- Developer/QtDesignerUI/MyBoxerUI.ui
- ViewController/1-PreProcess/MyBoxer.py
- ViewController/1-PreProcess/MyBoxerUI.py

Append the lean footer.

### 4) MyGlypher

Apply the strict header above.

Task:

- Audit MyGlypher picker actions, tooltip/button semantics, and drag/drop acceptance.
- Ensure no image/text control semantic swaps were introduced.
- Preserve default context menus.

Likely paths:

- Developer/QtDesignerUI/MyGlypherUI.ui
- ViewController/1-PreProcess/MyGlypher.py
- ViewController/1-PreProcess/MyGlypherUI.py

Append the lean footer.

### 5) MyPixler

Apply the strict header above.

Task:

- Audit MyPixler for redundant MyExplorer control removal and behavior stability.
- Verify replacement-only picker behavior and panel drag/drop acceptance.
- Preserve existing context-menu defaults.

Likely paths:

- Developer/QtDesignerUI/MyPixlerUI.ui
- ViewController/1-PreProcess/MyPixler.py
- ViewController/1-PreProcess/MyPixlerUI.py

Append the lean footer.

### 6) MyGrounder

Apply the strict header above.

Task:

- Audit MyGrounder picker/menu integration and drag/drop acceptance.
- Preserve existing custom context-menu defaults.
- Keep source UI and generated UI.py in lock-step.

Likely paths:

- Developer/QtDesignerUI/MyGrounderUI.ui
- ViewController/2-TrainTesseract/MyGrounder.py
- ViewController/2-TrainTesseract/MyGrounderUI.py

Append the lean footer.

### 7) MyReader

Apply the strict header above.

Task:

- Audit MyReader picker behavior and drag/drop acceptance for image/text panels.
- Preserve existing context-menu defaults.
- Regenerate UI.py from Designer source for any UI changes.

Likely paths:

- Developer/QtDesignerUI/MyReaderUI.ui
- ViewController/2-TrainTesseract/MyReader.py
- ViewController/2-TrainTesseract/MyReaderUI.py

Append the lean footer.

### 8) MyTrainer

Apply the strict header above.

Task:

- Audit MyTrainer menu/picker behavior and panel drag/drop acceptance.
- Preserve context-menu defaults and keep lock-step UI regeneration.

Likely paths:

- Developer/QtDesignerUI/MyTrainerUI.ui
- ViewController/2-TrainTesseract/MyTrainer.py
- ViewController/2-TrainTesseract/MyTrainerUI.py

Append the lean footer.

### 9) MyResolver

Apply the strict header above.

Task:

- Audit MyResolver picker integration and drag/drop acceptance.
- Preserve existing menu defaults and lock-step UI generation.

Likely paths:

- Developer/QtDesignerUI/MyResolverUI.ui
- ViewController/3-Process/MyResolver.py
- ViewController/3-Process/MyResolverUI.py

Append the lean footer.

### 10) MyVersifier

Apply the strict header above.

Task:

- Audit MyVersifier file picker behavior, menu defaults, and drag/drop acceptance.
- Keep source UI and generated UI.py synchronized.

Likely paths:

- Developer/QtDesignerUI/MyVersifierUI.ui
- ViewController/3-Process/MyVersifier.py
- ViewController/3-Process/MyVersifierUI.py

Append the lean footer.

### 11) MyWriter

Apply the strict header above.

Task:

- Audit MyWriter picker and drag/drop behavior for replacement-only integration.
- Preserve existing custom context-menu defaults.
- Maintain UI source and generated UI lock-step.

Likely paths:

- Developer/QtDesignerUI/MyWriterUI.ui
- ViewController/4-PostProcess/MyWriter.py
- ViewController/4-PostProcess/MyWriterUI.py

Append the lean footer.

## Optional Batch Prompt (Use Only If User Explicitly Requests Global Rollout)

Apply the strict header above, but expand scope to the listed modules only and still exclude MyLexer. Work module-by-module within one run and report a mini-summary per module before final aggregate validation.

## Night-Restart Fast Prompt

Use this to resume quickly after a break:

Resume BiblionOCR module-by-module audit workflow using docs/development/CHANGESET_PROMPT_PACK_2026-08-07.md. Keep MyLexer deferred and untouched. Start at module [MODULE_NAME]. Enforce strict header rules, run full workspace Problems check before completion, and report full + in-scope counts.
