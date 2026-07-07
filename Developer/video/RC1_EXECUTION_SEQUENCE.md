# RC1 Execution Sequence

This sequence follows the next practical path for the BiblionOCR introduction video:

1. Assemble the timeline
2. Render RC1
3. Review RC1

## Step 1. Assemble The Timeline

Use these documents together:

- [project/TIMELINE_ASSEMBLY_GUIDE.md](project/TIMELINE_ASSEMBLY_GUIDE.md)
- [project/RESOLVE_PROJECT_MANIFEST.md](project/RESOLVE_PROJECT_MANIFEST.md)
- [project/TYPOGRAPHY_GUIDE.md](project/TYPOGRAPHY_GUIDE.md)
- [audio/NARRATION_PACKAGE.md](audio/NARRATION_PACKAGE.md)

Execution order:

1. Create the Resolve project and timeline.
2. Set `24 fps`, `48 kHz`, and `1920x1080 minimum`.
3. Build the track layout:
   - `V1 Background`
   - `V2 Visual overlays`
   - `V3 Typography`
   - `A1 Narration`
   - `A2 Ambient audio`
4. Place scenes in the approved order and timing:
   - `0:00-0:05`
   - `0:05-0:12`
   - `0:12-0:25`
   - `0:25-0:38`
   - `0:38-0:45`
5. Apply only approved transitions.
6. Confirm Scene 5 ends with narration before fade to black and the final black hold.

Completion condition:

- The timeline matches the approved storyboard, shot list, and narration package exactly.

## Step 2. Render RC1

Use these documents together:

- [project/RENDER_SPECIFICATION.md](project/RENDER_SPECIFICATION.md)
- [project/RESOLVE_PROJECT_MANIFEST.md](project/RESOLVE_PROJECT_MANIFEST.md)

Execution order:

1. Export the master archival render.
2. Export the YouTube review render.
3. Name both files using the approved naming convention.
4. Place outputs in the production export area.
5. Generate `SHA-256` checksums for the final export files.

Completion condition:

- RC1 exists as an actual reviewable video export, not just a project timeline.

## Step 3. Review RC1

Use these documents together:

- [FINAL_QA_CHECKLIST.md](FINAL_QA_CHECKLIST.md)
- [PRODUCTION_READINESS_REPORT.md](PRODUCTION_READINESS_REPORT.md)
- [PUBLICATION_GUIDE.md](PUBLICATION_GUIDE.md)

Execution order:

1. Review the RC1 export locally.
2. Check storyboard and shot-list compliance.
3. Check narration timing and audio balance.
4. Check typography readability and transition consistency.
5. Confirm final runtime and fade-to-black behavior.
6. If acceptable, upload to YouTube as `Unlisted` for the next review stage.

Completion condition:

- RC1 is either approved for the Unlisted publication step or returned for correction with specific findings.

## Current Blocker

The repository does not currently contain a rendered intro video export under [exports](exports), so the workflow cannot move beyond documentation until the Resolve timeline is actually assembled and rendered.