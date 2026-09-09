# Page Workflow Wizard Architecture

## Authority

`Model/Project/Data/csv/ProjectWorkflow.ods` is the workflow authority. The exported `page_workflow.csv` supplies each module's ordered sequence rows and `page_workflow_milestones.csv` supplies progress metadata.

## Designer Lockstep

Each module-specific page workflow wizard follows the New Project wizard convention:

1. The editable `Developer/QtDesignerUI/<Module>PageWorkflowWizardUI.ui` file owns the complete stacked-widget structure and stable controls.
2. Every worksheet row for that module has one predeclared stacked page. A page is identified by the ordered tuple `(PageSections, Sequence, MilestoneName, Method)`, not by `Sequence` or `MilestoneName` alone because those values can repeat across sections.
3. The generated `ViewController/.../<Module>PageWorkflowWizardUI.py` file is produced with `pyuic5` and is not manually edited.
4. The behavior class validates the worksheet's ordered keys and Designer page count before the wizard opens. A worksheet change therefore requires a matching Designer update and regeneration.
5. Python populates runtime values, invokes existing module methods, reads milestone state, and controls navigation. It does not create workflow pages.

## MyPixler

MyPixler is the first module using this convention:

- Designer source: `Developer/QtDesignerUI/MyPixlerPageWorkflowWizardUI.ui`
- Generated UI: `ViewController/1-PreProcess/MyPixlerPageWorkflowWizardUI.py`
- Behavior: `ViewController/1-PreProcess/MyPixlerPageWorkflowWizard.py`

The Designer source contains all 30 current MyPixler worksheet rows. At runtime, navigation shows only rows matching the active page's source section. Completed steps remain reviewable, the first incomplete step is the only runnable step, and later steps remain visible but cannot run out of order.

After an existing MyPixler action returns, the wizard reloads page milestone state. Extraction and conversion actions record their own milestones. Interactive actions that return `True`, such as accepted clip and erase previews, are recorded by the wizard. Successful completion updates progress and selects the next sequence page.

### PDF Book Extraction Contract

MyServer stages the project source PDF and MyPixler completes the second half of the staging handshake. MyPixler first separates the source into front matter, middle matter, verse, and back matter multipage PDFs. The middle-matter and verse book-extraction steps then distribute selected source ranges as individual-page PDFs under generated book folders.

Book identity is canonicalized through `Model/Project/Data/json/BooksMarkDown.json`. Runtime code accepts a book abbreviation, canonical BookMarkdown value such as `_book_41_Mark`, or generated folder name such as `book_41_Mark`. MyPixler writes the active abbreviation, BookMarkdown, and folder name into the active project's `Model/Project/Data/json/Session.json`. MyServer reads that project-local state and keeps its book combo box synchronized; a manual MyServer selection writes the same canonical context back for the next MyPixler extraction view.

Middle matter is sparse by design. Many New Testament books have no middle-matter annotation pages, and incomplete manuscripts can omit later material. Book extraction therefore observes these rules:

1. Only a successfully extracted book consumes source pages when calculating the next default range.
2. Extraction status has exactly two persisted values: `pending` and `complete`.
3. Successful extraction changes the dialog status and its owning milestone to complete.
4. `Skip` followed by confirmation records an intentional no-output completion and changes the status to complete.
5. `Cancel` returns to the current book without advancing or completing it.
6. Complete section steps and complete book dialogs are omitted from subsequent extraction loops.
7. Unchecking a completed milestone in MyServer makes its step eligible again. Saved complete dialogs reset to pending, and book extraction recovers its source from the predecessor's Complete handoff when necessary.
8. Previous and Next navigate pending books without extracting or consuming a source range.
9. Saved ranges, statuses, completion sources, overrides, and the current book index remain project-local session state.

`ProjectTracking.json` is the visibility authority and is read at the beginning of every extraction invocation, before source-file availability is checked. Session status supports display and resumption but cannot make a completed milestone visible. When every dialog milestone in a loop is complete, MyPixler opens no extraction dialog and reports each completed item as `Sequence - MilestoneName`, with instructions to re-enable it by unchecking Complete in `MyServer > Project Settings > Milestone Settings`.

After a successful extraction or confirmed Skip records its milestone, MyPixler refreshes the project progress surfaces, updates the active dialog status to complete, and processes pending UI events before advancing. This keeps the progress bar and completion label synchronized with the authoritative tracking state.

Every file-producing extraction displays a temporary indeterminate progress dialog before filesystem work begins and closes it in a `finally` path. The indicator is non-modal, matching the source reader and extraction-dialog interaction model, and is removed after either success or failure.

The shared source reader used by MyServer, MyPixler, and project-creation previews accepts only PDF or TIFF documents with at least two pages. Its Open toolbar control replaces the displayed reference in place without changing MyServer's registered project-source metadata; docked, floating, and standalone readers remain non-modal.

Source Reader presentation follows the repository's Designer separation:

- `Developer/QtDesignerUI/SourceReader.ui` is the editable visual source of truth for alignment, spacing, sizing, labels, and control placement.
- `ViewController/0-MainUI/helpers/SourceReaderUI.py` is generated by `Developer/update_ui_resources.py` and must not be edited directly.
- `ViewController/0-MainUI/helpers/source_reader.py` owns loading, rendering, navigation, document replacement, and dock/dialog behavior.

Section extraction may use a saved or operator-selected destination that is broader than the workflow row's canonical book-specific path. Completion advances files from the dialog's actual destination into the configured Complete and handshake paths. The status and milestone become complete only after that handoff succeeds; a failed handoff leaves the step pending and reports the failure without terminating MyPixler.

The saved active section is restored by workflow sequence, not by its position in the filtered pending list. Removing completed milestones from a four-section loop therefore cannot shift an SSHV retry onto SSHB.

The same rules apply to verse extraction when a source manuscript is incomplete.

## Module Rollout

Apply this pattern one module at a time. Do not route a module to a generic placeholder sequence once its worksheet-defined wizard exists. Each rollout requires:

- a complete module-specific Designer stack;
- generated-Python byte comparison against fresh `pyuic5` output;
- an ordered worksheet/UI contract check;
- tests for section filtering, sequential execution, milestone recording, progress updates, and next-step navigation.
