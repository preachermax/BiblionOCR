# From PDF Source to Page Images Without Freezing the Interface

This draft is written as a public-facing Patreon update, with enough context for someone following the project without needing to track every internal implementation detail.

Today’s focus is from pdf source to page images without freezing the interface, which sits at the intersection of the project’s public story and the practical work needed to keep the platform moving.

The source-document pipeline now separates PDF inspection from full TIFF extraction and performs long-running work without locking the main interface.

Two jobs, two stages:

BiblionOCR now distinguishes the quick work needed to inspect a PDF from the heavier work needed to extract a complete set of TIFF page images. That keeps project setup responsive while preserving a deliberate path toward processing-ready source pages.

The shared source-document code handles PDF and TIFF inputs, while project creation and the PDF viewer expose progress and cancellation behavior around operations that may take time.

Why threading matters:

Large source documents should not make the application appear dead. Moving extraction work off the main UI thread allows the interface to keep responding and gives the user meaningful feedback while pages are prepared.

Focused tests now cover source selection, conversion behavior, progress reporting, cancellation, and the handoff into MyPixler.

Useful links:

- Project creation architecture: https://github.com/preachermax/BiblionOCR/blob/master/docs/architecture/PROJECT_CREATION_ARCHITECTURE.md

Share this update with anyone interested in practical OCR pipeline engineering and preservation-oriented source handling.
