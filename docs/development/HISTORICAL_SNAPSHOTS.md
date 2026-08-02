# Historical Snapshot Notes

These files are intentionally preserved as historical analysis artifacts and are not the source of truth for the current runtime layout:

- docs/development/VIEWCONTROLLER_ARCHIVE_CANDIDATES.md
- docs/development/viewcontroller_archive_candidates.json
- docs/development/viewcontroller_archive_broken_refs.json

Normalized companions for current-layout lookup:

- docs/development/viewcontroller_archive_candidates_current.json
- docs/development/viewcontroller_archive_broken_refs_current.json

Reason:

- They were generated before the 2026-08 ViewController stage reorganization and developer/runtime separation pass.
- They include references to now-moved paths such as `ViewController/3-ConductOCR` and legacy `0-MainUI` runtime locations.

Current source of truth:

- docs/architecture/PROJECT_ARCHITECTURE.md
- docs/development/QUICK_REFERENCE.md
- docs/development/DEPENDENCIES_AND_RELATIONSHIPS.md
- ViewController/Developer/SeparatedDevFiles/SEPARATION_REPORT.md
- ViewController/Developer/SeparatedDevFiles/MOVED_FILE_MANIFEST.md
