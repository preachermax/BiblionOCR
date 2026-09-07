# Keeping Every Module on the Same Project Page

This draft is written for members, so it stays closer to the active build surface and assumes interest in the day-to-day engineering and editorial decisions behind Biblion.

Today’s focus is keeping every module on the same project page, which sits at the intersection of the project’s public story and the practical work needed to keep the platform moving.

Current-page state, session persistence, MyExplorer filtering, and the MyPixler Page Workflow Wizard now work together around a shared page-level workflow.

One page, many modules:

OCR work moves through several specialized modules, but the person doing that work should not have to repeatedly rediscover the active page. Project tracking and session persistence now carry the current project page and its milestone context across module boundaries.

Reference images and reference text remain available without accidentally replacing the active project page. Image and text counterparts also retain matching page numbers when both exist.

MyPixler gained an explicit guide:

MyPixler now has a dedicated Page Workflow Wizard backed by the canonical page workflow definition. It presents the preprocessing stages as an intentional sequence rather than a collection of disconnected controls.

MyExplorer's filtering and picker behavior were aligned with the same model, and focused tests cover page state, workflow progression, source display, and handoffs.

Useful links:

- Page Workflow Wizard architecture: https://github.com/preachermax/BiblionOCR/blob/master/docs/architecture/PAGE_WORKFLOW_WIZARD_ARCHITECTURE.md

Member support funds the careful cross-module testing needed to make a multi-stage desktop workflow feel like one application.
