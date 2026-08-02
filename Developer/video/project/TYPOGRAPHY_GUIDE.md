# Typography Guide

Source documents:

- [../storyboards/BIBLIONOCR_INTRO_STORYBOARD.md](../storyboards/BIBLIONOCR_INTRO_STORYBOARD.md)
- [RESOLVE_PROJECT_MANIFEST.md](RESOLVE_PROJECT_MANIFEST.md)

This guide provides implementation guidance only for the approved typography already defined in the storyboard.

Do not redesign the storyboard.

Do not introduce additional typography.

## FROMVS.ttf Usage

- Use `FROMVS.ttf` for all approved on-screen text in the introduction video.
- Apply `FROMVS.ttf` consistently across:
  - Scene 1 quotation and scripture reference
  - Scene 4 architectural overlay strings
  - Scene 5 title, tagline, and footer lines
- Do not substitute a secondary display font for any approved text element.
- If a fallback is temporarily required during setup, replace it with `FROMVS.ttf` before RC review.

## Font Sizing Recommendations

These recommendations are for `1920x1080` delivery and may be scaled proportionally for 4K while preserving the same hierarchy.

### Scene 1 - Foundation

- Main quotation: large display size, approximately `64-84 px`
- Scripture reference: secondary size, approximately `32-42 px`
- Keep the quotation clearly dominant over the reference.

### Scene 4 - Architecture Reveal

- Overlay strings: medium-large readable size, approximately `40-56 px`
- Maintain equal weight and similar scale between both overlay lines.

### Scene 5 - Identity

- Title `BiblionOCR`: hero size, approximately `90-120 px`
- Tagline `Making systems visible.`: secondary size, approximately `36-48 px`
- Footer lines: smaller informational size, approximately `24-32 px`
- Preserve a clear hierarchy of title, then tagline, then footer.

## Text Alignment

### Scene 1

- Center align the quotation block.
- Center align the scripture reference beneath the quotation.
- Keep the full text treatment optically centered in frame.

### Scene 4

- Align overlay strings cleanly and consistently.
- Prefer left alignment within the overlay group for system-flow readability.
- Keep both lines visually related as one structured overlay cluster.

### Scene 5

- Center align the title and tagline.
- Center align the footer stack unless production framing requires a clean lower-center grouping.
- Preserve the minimal, confident, timeless presentation defined by the storyboard.

## Fade Durations

Use restrained fades consistent with the approved transition language.

### Scene 1

- Typography fade in: approximately `12-18 frames`
- Typography fade out: approximately `12-18 frames`

### Scene 4

- Overlay introductions: approximately `8-12 frames` if animated in
- Overlay removals: approximately `8-12 frames` if animated out

### Scene 5

- Title and identity typography fade in: approximately `10-16 frames`
- Final fade to black after narration: approximately `12-18 frames`

Do not use abrupt typography pops, flash reveals, or stylized glitch animation.

## Safe Margins

- Keep all typography inside conservative title-safe boundaries.
- Recommended safe margin at `1920x1080`:
  - left and right inset: approximately `10%` of frame width
  - top and bottom inset: approximately `10%` of frame height
- For footer lines in Scene 5, keep the lowest baseline comfortably above the bottom safe boundary.
- Scene 4 overlays must remain inside safe margins even if background imagery becomes visually dense.

## Overlay Timing

### Scene 1

- The quotation and scripture reference occupy the Scene 1 window only: `0:00-0:05`

### Scene 4

- Overlay text appears only during `0:25-0:38`
- Keep the overlays on screen long enough for comfortable reading while narration remains primary.
- If staggered appearance is used, keep timing restrained and ensure both overlays are fully readable within the scene window.

### Scene 5

- Title, tagline, and footer appear only during `0:38-0:45`
- Maintain enough hold time for title recognition before the final fade to black.
- Respect the storyboard note that narration concludes before the fade to black and that black holds approximately one second before video end.

## Contrast Recommendations

- Maintain strong text-to-background contrast in every typographic scene.
- Prefer light text against dark or subdued backgrounds when using imagery from categories A, D, and E.
- If a background becomes too visually active, reduce background luminance or add a subtle non-stylized darkening treatment behind text.
- Do not use decorative outlines, glow, bevel, or novelty styling unless they are strictly required for legibility.
- Preserve clarity over stylization.

## Title Card Specifications

### Scene 1 - Quotation Card

- Content:
  - `"Faith is the substance of things hoped for, the evidence of things not seen."`
  - `Hebrews 11:1 (KJV)`
- Layout:
  - centered quote
  - centered reference below quote
- Background:
  - solid black
- Style:
  - quiet, reverent, minimal

### Scene 5 - Identity Card

- Content:
  - `BiblionOCR`
  - `Making systems visible.`
  - `Open source. In development.`
  - `github.com/preachermax/BiblionOCR`
- Layout:
  - title first
  - tagline second
  - footer lines beneath in smaller size
- Style:
  - minimal
  - confident
  - timeless

## Implementation Notes

- Keep all approved text exactly as written in the storyboard.
- Do not add subtitles, labels, callouts, captions, or extra UI text not already approved.
- Do not alter scene timing to make room for additional text treatment.
- If readability issues emerge, solve them through spacing, contrast, or scale adjustments rather than introducing new typographic elements.