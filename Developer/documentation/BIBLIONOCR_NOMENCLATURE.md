# BiblionOCR Project Nomenclature

## Purpose

This document helps human developers and GitHub Copilot interpret informal, abbreviated, misspelled, historical, or ambiguous language without reproducing that ambiguity in code, user interfaces, documentation, tests, commits, or pull requests.

The governing principle is:

> Input may be informal; committed output must use canonical terminology.

A recognized misspelling is an interpretation aid, not an approved alternate spelling. This guide does not correct a person's conversational style. It preserves creative momentum while giving implementation work a stable shared vocabulary.

## Authority and Precedence

When sources differ, use this order:

1. Exact code identifiers, persisted field names, schemas, and public API names control technical spelling where compatibility requires them.
2. This document controls preferred contributor-facing names and recognized aliases.
3. `docs/development/DESIGN_SPECIFICATION.md` controls domain-class meanings and boundaries.
4. `docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md` controls whether an architectural concept is implemented, emerging, planned, historical, or contradictory.
5. Current runtime code and tests control verified behavior.
6. Archived, reference, backup, and moved-candidate files provide history but do not establish current terminology.

When a phrase could map to different behavior, do not silently choose. Inspect the nearest context and ask for clarification only when the distinction would alter scope, data, ownership, or user-visible behavior.

## Product and Repository Names

| Canonical term | Recognized informal forms | Meaning and usage | Avoid in committed output |
| --- | --- | --- | --- |
| **Biblion** | Biblion Project, broader Biblion ecosystem | The broader preservation, research, publication, and software initiative. | Using Biblion when only the OCR application is meant. |
| **BiblionOCR** | Biblion OCR, current repo, OCR system | The present Apache-2.0 Python/Qt application and repository. | `BiblionOcr`, `Biblion OCR` as a product name. |
| **BiblionOCR-Qt6** | Qt6 repo, PyQt6/PySide6 repo | Neutral working name for the planned Qt 6 descendant until its binding is selected. | Naming it PySide6 or PyQt6 before the decision gate. |
| **PyQt5** | pyqt5, Qt5 binding | The binding used by the current BiblionOCR runtime. | `PyQT5`. |
| **PyQt6** | pyqt6, PyQT6 | One candidate Qt 6 binding. Capitalization is exact. | `PyQT6`. |
| **PySide6** | pyside6, PySide 6 | The currently favored Qt 6 candidate, subject to the documented decision and licensing gates. | Treating preference as a final selection. |
| **MyScanner** | scanner module, Scanner | The current BiblionOCR code module and active Product 1 development surface. | Calling it release-ready because it launches. |
| **BiblionScanner** | standalone scanner, commercial scanner | Provisional product name for a separately productized MyScanner distribution. | Using it as the current Python module name. |
| **Product 1** | first product, first commercial track | MyScanner's priority in the active productization sequence. It is a planning status, not release approval. | `Release 1` or `release-ready` unless release gates pass. |
| **development build** | dev build, full repo build | A build of the complete development workspace used for engineering and validation. | Presenting it as a supported commercial binary. |
| **product binary** | commercial binary, standalone binary | A separately packaged module distribution that has passed its product, technical, licensing, and release gates. | Assuming closed-source status or license rights without review. |

## Modules

Use the exact `My...` name when identifying an application module. A module supports workflows and implements processes; it is not itself a workflow.

| Canonical module | Primary responsibility | Ambiguity to avoid |
| --- | --- | --- |
| **MyLauncher** | Starts canonical BiblionOCR modules. | Do not call it MyServer or the workflow engine. |
| **MyServer** | Main project-administration and runtime-coordination surface. | It is not a network server, HTTP service, or remote API. |
| **MyExplorer** | Project-aware file and folder selection surface. | Do not use “Explorer” to imply the operating-system picker. |
| **MyScanner** | Scanner acquisition and scanner-related image workflow. | Distinguish the code module from provisional BiblionScanner packaging. |
| **MyPixler** | Image viewing, preparation, and page workflow operations. | Prefer MyPixler over Pixler in committed user-facing text. Do not normalize it to “MyPixel.” |
| **MyBoxer** | Bounding-box, line, and ground-truth preparation operations. | A box is an image/character region, not a UI card. |
| **MyGlypher** | Glyph inspection and editing operations. | Distinguish a glyph from a word or generic image crop. |
| **MyGrounder** | Ground-truth preparation and review support. | “Grounder” does not mean project initialization. |
| **MyTrainer** | Tesseract training workflows and assets. | Distinguish model training from OCR execution. |
| **MyReader** | Document reading and reference-oriented viewing. | Reference viewing must not silently change the current project page. |
| **MyLexer** | Dictionary and lexical-data operations. | Distinguish lexical data from OCR language-model selection. |
| **MyVersifier** | Verse segmentation, structure, and correction operations. | Distinguish verses from generic text lines. |
| **MyResolver** | Textual-variant resolution operations. | Distinguish variant decisions from OCR correction generally. |
| **MyWriter** | Text editing, formatting, and output preparation. | Distinguish edited text from immutable source/reference material. |

## Architecture and Workflow Terms

| Canonical term | Meaning | Recognized or deprecated wording |
| --- | --- | --- |
| **System** | The full BiblionOCR platform, including code, reusable data, documentation, and generated projects. | “Application” may mean only a runtime executable; inspect context. |
| **Workspace** | A checked-out development tree of the System. | repo folder, checkout, dev tree |
| **Project** | A user-created, externally stored work unit with provenance, deterministic structure, artifacts, and project-local state. | Do not use Project for the repository Workspace. |
| **Module** | A concrete application or code unit exposing capabilities. | app, tool; never assume it means Workflow. |
| **Workflow** | An ordered business-level path that advances a Project toward an outcome and may span modules. | flow, pipeline; “Macro” is deprecated for wizard-run workflows. |
| **Process** | One executable transformation or operation inside a Workflow. | operation, task, action |
| **Stage** | A named checkpoint or state boundary in a Workflow or Process chain. | step, milestone; use the more precise term where known. |
| **milestone** | A tracked completion/progress point at project or page scope. | checkpoint; do not conflate with every wizard step. |
| **Artifact** | A durable file or folder produced, consumed, or transformed by the System. | output, asset; distinguish generated output from reusable Reference Data. |
| **Reference Data** | Shared reusable data that informs runtime behavior but is not the user's direct work product. | template data, support data |
| **Session** | Persisted runtime state used to restore operator context. | session JSON; it is not workflow provenance. |
| **Event** | An immutable record of a meaningful system transition. | notification or signal may not be a persisted Event. |
| **UI Surface** | A main window, dialog, wizard, menu, control group, or other user-facing interaction boundary. | screen, form, panel |

## Authority, State, and Provenance Terms

| Canonical term | Meaning | Ambiguity to avoid |
| --- | --- | --- |
| **source of truth** | The designated authoritative representation for one defined concern. | Always name the concern; no file is automatically authoritative for everything. |
| **data authority** | The format or store whose values control runtime interpretation for a specified dataset or workflow. | Authority is a contract, not merely the newest file. |
| **ODS authority** | An ODS spreadsheet designated as the human-editable authority for a specified matrix or definition. | Do not imply every ODS file controls runtime behavior. |
| **CSV authority** | A CSV artifact designated as authoritative or as the canonical runtime export for a specified concern. | State whether CSV is primary authority or a generated projection of ODS. |
| **workflow definition** | Structured data describing workflow steps, ordering, ownership, inputs, outputs, or milestones. | Distinguish the definition from a running Workflow and its current state. |
| **active workflow definition** | The specific workflow definition selected for the current project/module context. | Do not silently use a stale, cached, or differently rooted definition. |
| **active project** | The Project currently selected in session/runtime context. | It is not necessarily the repository Workspace or most recently modified folder. |
| **project root** | Top-level filesystem directory of one Project. | Distinguish from repository root, module directory, or current working directory. |
| **repository root** | Top-level directory of the checked-out BiblionOCR Workspace. | Do not use as a synonym for project root. |
| **provenance** | Traceable information about an artifact's origin, transformations, and relevant context. | Session convenience data is not a substitute for provenance. |
| **RIS** | BiblionOCR's provenance record and related project-creation contract, as implemented and documented by the current Core RIS surfaces. | Do not assume every use means the generic bibliographic interchange format without checking BiblionOCR context. |
| **event-sourced truth** | Architectural goal or implemented subset in which durable state can be reconstructed from persisted Events. | The truth table currently governs whether this claim is implemented globally or remains emerging. |
| **projection** | A derived representation built from an authority or event stream for runtime, display, export, or query use. | A projection does not become authority merely because code reads it. |
| **runtime state** | Mutable state used while the application operates, including session context. | Do not commit incidental runtime state as source or documentation authority. |

## Project and Page Workflow Terms

| Canonical term | Exact meaning | Do not confuse with |
| --- | --- | --- |
| **Project Workflow Wizard** | MyServer-owned wizard for project-level workflow orchestration. | A module Page Workflow Wizard. |
| **Page Workflow Wizard** | Wizard for advancing the active project page through module-relevant page steps. | Project creation or a whole-project run. |
| **current project page** | The active work page represented by `CurrentProjectPage`. | A reference image/text page. |
| **current project milestone** | Project-level progress represented by `CurrentProjectMilestone`. | The current page's milestone. |
| **current page milestone** | Page-level progress represented by `CurrentPageMilestone`. | Project-wide completion. |
| **reference page** | Image or text displayed for comparison, consultation, or reading without becoming the current project page. | Active work page. |
| **handoff** | Transfer of work/context to another module while preserving the calling module and current-page contract. | Replacing or closing the calling module. |
| **Workflow directory** | Staging location for artifacts still being processed. | Workflow as the business-level sequence. |
| **Complete directory** | Destination for artifacts whose applicable milestone has completed. | Project completion as a whole. |
| **Wizard** | Guided user interface for a structured workflow. | “Macro,” which is deprecated in workflow UI text. |

## Source, Reference, and Output Terms

| Canonical term | Meaning | Notes |
| --- | --- | --- |
| **source document** | The active project's original PDF or multipage TIFF acquisition source. | It may be displayed by MyPixler's shared Source Reader without becoming a mutable output. |
| **source image** | An image acquired or derived as input to page processing. | Use provenance to distinguish original acquisition from a derived image. |
| **reference image** | An image displayed for comparison or consultation. | Must not become `CurrentProjectPage` merely by being viewed. |
| **reference text** | Text displayed for comparison, reading, or correction context. | Distinguish from editable/output text. |
| **processed image** | An image changed by a Process such as conversion, deskew, crop, or cleanup. | Name the specific stage when it matters. |
| **OCR output** | Machine-recognized text produced from an image. | It is not corrected text until reviewed/corrected. |
| **corrected text** | OCR-derived text after the applicable correction process. | It remains distinct from immutable source/reference text. |
| **image/text pair** | Related page artifacts that share the same page number. | Do not assign mismatched page numbers when both exist. |

## UI and Generated-File Terms

| Canonical term | Meaning | Recognized informal forms |
| --- | --- | --- |
| **Designer source** | Editable Qt Designer `.ui` file under `Developer/QtDesignerUI`. | UI file, form source |
| **generated UI module** | Python output generated from a Designer source file. | `UI.py`, generated Python, generated form |
| **runtime wiring** | Controller code that instantiates generated UI and connects behavior. | hookups, signals, handlers |
| **UI lockstep** | Required agreement among Designer source, generated UI module, and runtime wiring. | lock-step, lock step, lock-tain, lock train |
| **selective regeneration** | Generate into temporary storage and replace only outputs whose bytes changed. | UI refresh, regenerate resources |
| **drift check** | A no-write comparison proving whether generated outputs match their sources and configured deterministic prefixes. | generation check, stale-output check |
| **MyExplorer file-picker policy** | Open-file controls use MyExplorer as the sole system file-selection boundary or the shared interception that routes through it. | project picker policy |

Developer-only `Developer/Developer.py` and `Developer/developer_help.py` are hand-maintained exceptions to production Designer/generated UI lockstep.

## Development and Review Terms

| Canonical term | Meaning | Notes |
| --- | --- | --- |
| **GitHub Copilot** | The AI design and implementation partner used in the documented workflow. | Prefer GitHub Copilot over CoPilot, Co-pilot, or “the agent” when naming the product. |
| **coding agent** | The active automated collaborator executing repository work. | May be GitHub Copilot; describes a role rather than a product name. |
| **human developer** | A contributor responsible for requirements, judgment, truthful evidence, review response, and PR submission. | The wizard supports but does not replace accountability. |
| **concrete anchor** | A file, symbol, failing behavior, command, test, or nearby implementation surface where investigation starts. | starting point |
| **local hypothesis** | A falsifiable explanation tied to the controlling nearby code path. | theory; must be testable. |
| **disconfirming check** | The cheapest check capable of showing the local hypothesis is wrong. | validation probe |
| **focused validation** | The narrowest executable check that can falsify the current implementation claim. | targeted test, compile check |
| **Problems** | VS Code diagnostics reported for the workspace or scoped files. | Do not use “no problems” without stating full-workspace and in-scope totals. |
| **PR ELIGIBLE** | All local Developer Workflow Wizard gates contain structurally complete statuses and evidence. | It is not approval, acceptance, or permission to merge. |
| **Not applicable** | An allowed conditional gate status supported by a factual explanation that the named surface is unaffected. | Not a waiver for time, failure, inconvenience, or missing evidence. |
| **handoff checkpoint** | Restart-safe record of scope, files, validation, risks, blockers, and next action. | status note |
| **commit-worthy Developer content** | Human-useful tools, instructions, documentation, and maintained support files intended for version control. | Excludes runtime noise, caches, personal scratch material, broad archives, and unused assets. |

## Common Interpretation Map

| Informal or misspelled input | Interpret as | Required committed form |
| --- | --- | --- |
| Biblion OCR, BiblionOcr | Product/repository name | BiblionOCR |
| PyQT6 | Candidate binding | PyQt6 |
| PySide6and PyQt6 | “PySide6 and PyQt6” when grammar makes the conjunction clear | PySide6 and PyQt6 |
| CoPilot, Co-pilot | AI product | GitHub Copilot |
| lock-tain, lock train, lock step | UI source/generated/runtime alignment | UI lockstep |
| macro or workflow macro | Guided workflow action | Wizard or Workflow Wizard |
| server | MyServer only when project/runtime coordination is meant | MyServer |
| project folder | Project root or a folder inside it; inspect context | Project root or exact folder name |
| current page | Current project page unless reference-view context says otherwise | current project page |
| source | Source document, source image, source code, or source branch; inspect context | Use the specific applicable term. |
| authority | ODS authority, CSV authority, database authority, or another scoped source of truth; inspect context | Name both the authoritative representation and its concern. |
| workflow file | Workflow definition, workflow state, or an artifact in a Workflow directory; inspect context | Use the exact applicable term and path. |
| root | Repository root, project root, source root, or selected folder; inspect context | Name the exact root. |
| complete | Complete directory, completed milestone, or finished task; inspect context | Use the specific applicable term. |
| sync | Fetch, merge/fast-forward, push, branch parity, or all of these; inspect context | Name the exact Git operation or parity result. |
| clean | No diagnostics, clean worktree, passing tests, or visually correct; inspect context | State the exact clean condition and evidence. |

This table should remain selective. Add a form when it recurs, affects implementation, or creates a material review risk. Do not catalog harmless one-time typographical errors.

## Contributor Interpretation Protocol

When receiving an informal request:

1. Preserve the likely intent without correcting conversational wording unnecessarily.
2. Resolve recognized aliases through this guide.
3. Inspect repository evidence for the nearest concrete meaning.
4. State the canonical term when planning or implementing the work.
5. Ask a concise clarification question only when plausible interpretations lead to materially different behavior or scope.
6. Use canonical terminology in code, UI text, help, tests, commits, and PR evidence.
7. Record a new alias here only when it is recurrent or operationally important.

## Change Control

Update this document when:

- a product, module, workflow, state field, or architectural concept is added or renamed;
- an informal alias repeatedly causes ambiguity;
- a historical term is deprecated;
- a provisional name becomes final;
- runtime behavior proves an existing definition wrong;
- the Qt 6 binding decision changes repository or product naming.

For each change:

1. Verify meaning against runtime code, tests, design specification, and architectural truth status.
2. Update affected help, UI wording, documentation, and Developer Workflow guidance.
3. Add compatibility handling where persisted fields or public APIs cannot be renamed immediately.
4. Do not silently rewrite historical records or archived files merely to modernize terminology.
5. Include nomenclature review evidence in the Developer Workflow documentation gate.

## Related Sources

- `docs/development/DESIGN_SPECIFICATION.md`
- `docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md`
- `docs/architecture/BiblionOCR_Architectural_Evidence_Review.md`
- `Developer/documentation/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md`
- `Developer/documentation/DEVELOPMENT_ROUTINE_PLAYBOOK.md`
- `Developer/Developer.py`
- `Developer/developer_help.py`
