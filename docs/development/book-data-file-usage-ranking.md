# Book data file usage ranking

This note ranks the CSV files under [Model/Project/Data/csv](../../Model/Project/Data/csv) by how directly they appear to be used by the current codebase.

## Directly used by code

These are the files that currently show concrete references from the repository and look like active or near-active data sources:

- [Model/Project/Data/csv/BooksAbbrName.csv](../../Model/Project/Data/csv/BooksAbbrName.csv) — directly referenced by post-processing helpers for book abbreviations and names.
- [Model/Project/Data/csv/BooksAbbrNameNumIndex.csv](../../Model/Project/Data/csv/BooksAbbrNameNumIndex.csv) — useful for ordered indexing and book sequence handling.
- [Model/Project/Data/csv/BooksMarkDown.csv](../../Model/Project/Data/csv/BooksMarkDown.csv) — still relevant for markdown/book-slug style metadata.
- [Model/Project/Data/csv/FROMVS3_0_PUA_Norm.csv](../../Model/Project/Data/csv/FROMVS3_0_PUA_Norm.csv) — referenced by normalization helpers.
- [Model/Project/Data/csv/FromvsDiacritics.csv](../../Model/Project/Data/csv/FromvsDiacritics.csv) — referenced across several normalization and text-processing helpers.
- [Model/Project/Data/csv/EnglishProperNames.csv](../../Model/Project/Data/csv/EnglishProperNames.csv) — referenced by English normalization helpers.
- [Model/Project/Data/csv/ProperNames.csv](../../Model/Project/Data/csv/ProperNames.csv) — referenced by similar normalization workflows.

## Likely archive candidates

These files appear to be mostly legacy, export-oriented, or specialized enough that they are good candidates for the archives alongside the three already recommended:

- [Model/Project/Data/csv/BooksAbbr.csv](../../Model/Project/Data/csv/BooksAbbr.csv) — abbreviation-only list with limited value on its own.
- [Model/Project/Data/csv/BooksName.csv](../../Model/Project/Data/csv/BooksName.csv) — descriptive book-name list with limited runtime value.
- [Model/Project/Data/csv/csv4json/BooksMarkDown.csv](../../Model/Project/Data/csv/csv4json/BooksMarkDown.csv) — duplicate/export-oriented variant with low practical value.
- [Model/Project/Data/csv/BoxerSession.csv](../../Model/Project/Data/csv/BoxerSession.csv) — session artifact rather than core reference data.
- [Model/Project/Data/csv/GlypherSession.csv](../../Model/Project/Data/csv/GlypherSession.csv) — session artifact rather than core reference data.
- [Model/Project/Data/csv/ReaderSession.csv](../../Model/Project/Data/csv/ReaderSession.csv) — session artifact rather than core reference data.
- [Model/Project/Data/csv/ScannerSession.csv](../../Model/Project/Data/csv/ScannerSession.csv) — session artifact rather than core reference data.
- [Model/Project/Data/csv/Session.csv](../../Model/Project/Data/csv/Session.csv) — generic session artifact with limited value as reference data.
- [Model/Project/Data/csv/Workflow.csv](../../Model/Project/Data/csv/Workflow.csv) — workflow state artifact rather than canonical data.
- [Model/Project/Data/csv/WriterSession.csv](../../Model/Project/Data/csv/WriterSession.csv) — session artifact rather than core reference data.

## Low-priority / likely unused files

The following files appear to be mostly specialized or supplemental and are unlikely to be needed in normal active workflows:

- [Model/Project/Data/csv/ChrRef.csv](../../Model/Project/Data/csv/ChrRef.csv)
- [Model/Project/Data/csv/Preserved.csv](../../Model/Project/Data/csv/Preserved.csv)
- [Model/Project/Data/csv/PageVerseCrossReference.csv](../../Model/Project/Data/csv/PageVerseCrossReference.csv)
- [Model/Project/Data/csv/PageVerseCrossReferenceInit.csv](../../Model/Project/Data/csv/PageVerseCrossReferenceInit.csv)
- [Model/Project/Data/csv/PageVerseSessionReference.csv](../../Model/Project/Data/csv/PageVerseSessionReference.csv)
- [Model/Project/Data/csv/PageVerseXref.csv](../../Model/Project/Data/csv/PageVerseXref.csv)
- [Model/Project/Data/csv/RISTags.csv](../../Model/Project/Data/csv/RISTags.csv)
- [Model/Project/Data/csv/RISrefTypes.csv](../../Model/Project/Data/csv/RISrefTypes.csv)
- [Model/Project/Data/csv/ProjectUnicodeRanges.csv](../../Model/Project/Data/csv/ProjectUnicodeRanges.csv)
- [Model/Project/Data/csv/UnicodeRanges.csv](../../Model/Project/Data/csv/UnicodeRanges.csv)

## Summary

If the goal is to reduce clutter while preserving the most practical data, keep the active reference files in place and move the session artifacts and the low-value book-list files to the archives first.
