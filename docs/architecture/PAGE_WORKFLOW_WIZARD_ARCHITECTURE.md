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

## Module Rollout

Apply this pattern one module at a time. Do not route a module to a generic placeholder sequence once its worksheet-defined wizard exists. Each rollout requires:

- a complete module-specific Designer stack;
- generated-Python byte comparison against fresh `pyuic5` output;
- an ordered worksheet/UI contract check;
- tests for section filtering, sequential execution, milestone recording, progress updates, and next-step navigation.
