# MyServer Now Treats Project Creation as a Workflow

This draft is written for members, so it stays closer to the active build surface and assumes interest in the day-to-day engineering and editorial decisions behind Biblion.

Today’s focus is myserver now treats project creation as a workflow, which sits at the intersection of the project’s public story and the practical work needed to keep the platform moving.

MyServer's project-creation path now joins project structure, workflow definitions, source acquisition, database state, and preview behavior under a more explicit contract.

More than making folders:

Creating a BiblionOCR project now means more than copying a directory template. MyServer coordinates project metadata, canonical folder structure, workflow definitions, source selection, and persistent tracking so later modules inherit a coherent starting point.

The underlying project database and tracking code were aligned with that behavior, and the minimum project structure was tested as a contract rather than left as an assumption.

A visible source workflow:

Project creation also gained a clearer source-document path and PDF viewing support. The wizard and help material now explain what source is being acquired, where it belongs, and how it enters the processing workflow.

This is part of a larger architectural goal: every stage should know which artifact it owns, which artifact it received, and what it must hand to the next stage.

Useful links:

- Project creation architecture: https://github.com/preachermax/BiblionOCR/blob/master/docs/architecture/PROJECT_CREATION_ARCHITECTURE.md

Members make it possible to spend time on the less visible architectural work that keeps later OCR stages coherent.
