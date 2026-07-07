# Publication Guide

Source documents:

- [storyboards/BIBLIONOCR_INTRO_STORYBOARD.md](storyboards/BIBLIONOCR_INTRO_STORYBOARD.md)
- [project/RENDER_SPECIFICATION.md](project/RENDER_SPECIFICATION.md)

This guide describes the publication workflow for the BiblionOCR introduction video.

It provides guidance only.

It does not modify project documentation.

It does not invent public URLs.

## 1. Render RC1

1. Export the first release candidate using the approved render specification.
2. Produce at least:
   - master archival render
   - YouTube upload render
3. Confirm the RC1 file naming follows the approved convention.
4. Generate and store the recommended `SHA-256` checksum for the RC1 output.

## 2. Internal Review

1. Review the RC1 export against the approved storyboard, shot list, narration package, typography guidance, and final QA checklist.
2. Confirm:
   - approved runtime is preserved
   - narration is unchanged
   - transitions remain compliant
   - fade to black is correct
   - typography remains readable and consistent
3. Record any corrections before external upload.
4. If required, revise and regenerate a new candidate before proceeding.

## 3. Upload To YouTube As Unlisted

1. Use the approved YouTube render output.
2. Upload the video to the project’s YouTube destination as `Unlisted`.
3. Apply provisional publication metadata during upload:
   - title
   - description
   - tags if used by the release workflow
4. Do not publish as `Public` at this stage.

## 4. Multi-Device Playback Verification

Review the Unlisted video on multiple playback surfaces.

Recommended devices and contexts:

- desktop browser
- laptop browser
- phone playback
- tablet playback if available
- headphones
- speakers

Verify:

- playback starts cleanly
- narration remains intelligible on small speakers
- typography is legible on mobile screens
- black levels and fades remain clean
- no compression artifacts materially damage overlays or title cards

## 5. Metadata Verification

Before public release, confirm all publication metadata is correct.

Verify:

- video title is final
- description is accurate
- project naming matches `BiblionOCR`
- on-screen GitHub reference matches `github.com/preachermax/BiblionOCR`
- no placeholder metadata remains
- visibility remains `Unlisted` until approval is complete

## 6. Thumbnail Selection

Select a thumbnail that matches the approved visual identity.

Recommended thumbnail qualities:

- clear and readable at small size
- visually consistent with the project identity
- not overly busy
- not misleading about the content

Prefer a frame or designed image that reflects:

- architectural clarity
- minimal identity treatment
- strong contrast

## 7. Publish As Public

1. After internal and Unlisted review are complete, switch the video visibility to `Public`.
2. Confirm the final public version is the approved upload revision.
3. Recheck title, description, thumbnail, and visibility state immediately after publication.

## 8. Record Public YouTube URL

1. Copy the final public YouTube URL after publication.
2. Record it in the release notes or publication tracking location used by the project.
3. Confirm that the recorded URL is the public link, not the internal edit or studio management URL.

## 9. Update GitHub README

1. Open the project README update workflow.
2. Insert or replace the introduction-video link using the final public YouTube URL.
3. Verify the README change before committing or publishing documentation updates.

## 10. Update Project Documentation

1. Update any project documentation that references the introduction video.
2. Use the final public YouTube URL only.
3. Confirm that every documentation reference points to the same published video.

## 11. Update Patreon Introduction Link

1. Open the Patreon introduction or project-link update workflow.
2. Replace any temporary or missing video reference with the final public YouTube URL.
3. Confirm the Patreon-facing link resolves to the published video.

## Final Publication Checklist

- [ ] RC1 has been rendered from the approved timeline.
- [ ] Master archival render exists.
- [ ] YouTube upload render exists.
- [ ] Render naming follows the approved convention.
- [ ] `SHA-256` checksums have been generated for final deliverables.
- [ ] Internal review has been completed.
- [ ] Required corrections have been applied before publication.
- [ ] The review build has been uploaded to YouTube as `Unlisted`.
- [ ] Multi-device playback verification has been completed.
- [ ] Typography remains readable across tested devices.
- [ ] Narration remains intelligible across tested devices.
- [ ] Metadata has been reviewed and approved.
- [ ] Thumbnail has been selected and verified.
- [ ] The video has been switched to `Public`.
- [ ] The final public YouTube URL has been recorded.
- [ ] GitHub README has been updated with the public URL.
- [ ] Project documentation has been updated with the public URL.
- [ ] Patreon introduction link has been updated with the public URL.
- [ ] Final publication approval has been recorded by the release owner.