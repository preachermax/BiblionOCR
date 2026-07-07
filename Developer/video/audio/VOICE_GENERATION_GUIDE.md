# Voice Generation Guide

Source document:

- [NARRATION_PACKAGE.md](NARRATION_PACKAGE.md)

This guide is for AI voice generation and studio preparation only.

Do not rewrite narration.

Do not generate audio from this document alone.

Use the approved narration exactly as packaged in [NARRATION_PACKAGE.md](NARRATION_PACKAGE.md).

## AI Voice Preparation

- Use the approved narrator profile:
  - educated Southern American accent
  - warm baritone timbre
  - calm authority
  - measured pacing
  - restrained emotional expression
  - clear diction
  - no promotional delivery
  - no theatrical delivery
- Load the narration from [NARRATION_PACKAGE.md](NARRATION_PACKAGE.md) without paraphrase.
- Preserve all approved pauses, including ellipsis-driven pauses and end-of-line release timing.
- Keep Scene 1 unvoiced.
- Preserve pronunciation guidance for:
  - `BiblionOCR`
  - `MyServer`
  - `MyPixler`
  - `Developer Services`
  - `EventBus`
  - `Runtime Inspector`
- Use a clean, dry voice render when possible so mixing remains flexible in post.
- Avoid heavy compression, widening, artificial reverb, hype EQ, or dramatic emphasis during generation.

## Recommended Export Format

- File format: `WAV`
- Sample rate: `48 kHz`
- Bit depth: `24-bit PCM`
- Channel format: mono preferred for narration source delivery unless the voice system requires stereo output
- Peak management: leave conservative headroom for post-production mixing

## Suggested Generation Workflow

1. Open [NARRATION_PACKAGE.md](NARRATION_PACKAGE.md) and confirm the approved script, pause guidance, and pronunciation notes.
2. Configure the AI voice using the approved narrator profile.
3. Generate a first clean pass for each narrated scene only:
   - Scene 2
   - Scene 3
   - Scene 4
   - Scene 5
4. Review each pass for diction, pacing, pause fidelity, and tonal consistency.
5. Regenerate any scene that drifts into promotional, theatrical, rushed, or overly dramatic delivery.
6. When scene-level renders are approved, generate a final matched set using identical voice settings across all narrated scenes.
7. Export final approved narration files as `WAV`, `48 kHz`, `24-bit PCM`.
8. Deliver the final approved narration set into the production audio workflow for Resolve import.

## Naming Convention

Use a consistent scene-based naming pattern.

- Base pattern:
  - `BIBLIONOCR_INTRO_SCENE##_NARRATION_v01.wav`

Examples:

- `BIBLIONOCR_INTRO_SCENE02_NARRATION_v01.wav`
- `BIBLIONOCR_INTRO_SCENE03_NARRATION_v01.wav`
- `BIBLIONOCR_INTRO_SCENE04_NARRATION_v01.wav`
- `BIBLIONOCR_INTRO_SCENE05_NARRATION_v01.wav`

If a full continuous reference render is needed for review, use:

- `BIBLIONOCR_INTRO_FULL_NARRATION_REF_v01.wav`

Increment version numbers only when a new approved render supersedes the prior one.

## Quality Verification Checklist

- The narration text matches [NARRATION_PACKAGE.md](NARRATION_PACKAGE.md) exactly.
- Scene 1 contains no spoken narration.
- Pronunciations match the approved notes.
- Delivery sounds educated Southern American, warm baritone, calm, and restrained.
- Pacing is measured and not rushed.
- Ellipsis pauses are preserved as reflective pauses, not uncertainty.
- End-of-line release timing feels intentional and controlled.
- No promotional tone is present.
- No theatrical tone is present.
- Diction is clear across technical terms and project names.
- The render is free from clipping, distortion, and distracting artifacts.
- The file format is `WAV`.
- The sample rate is `48 kHz`.
- The bit depth is `24-bit PCM`.
- File naming follows the approved convention.
- Final files are ready for import into the Resolve timeline described in [../project/RESOLVE_PROJECT_MANIFEST.md](../project/RESOLVE_PROJECT_MANIFEST.md).