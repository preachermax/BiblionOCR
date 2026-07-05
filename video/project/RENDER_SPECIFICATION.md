# Render Specification

Source document:

- [video/project/RESOLVE_PROJECT_MANIFEST.md](video/project/RESOLVE_PROJECT_MANIFEST.md)

This document defines recommended render settings for the BiblionOCR introduction video.

It does not generate proprietary Resolve project files.

## Global Render Requirements

- Runtime target: `45 seconds`
- Frame rate: `24 fps`
- Minimum resolution: `1920x1080`
- Optional finishing resolution: `3840x2160 (4K)`
- Audio sample rate: `48 kHz`
- All exports should preserve the approved scene timing and final fade-to-black behavior.

## Master Archive

### Purpose

- High-quality retained master for archive, re-export, and future distribution.

### Recommended Settings

- Container: `MOV`
- Recommended codec: `Apple ProRes 422 HQ` if available on the render platform
- Cross-platform alternative codec when ProRes is unavailable: `DNxHR HQX`
- Resolution: `1920x1080 minimum`, or `3840x2160` when the project is finished in 4K
- Frame rate: `24 fps`
- Recommended bitrate: codec-managed high-quality intraframe master; do not apply low-bitrate delivery constraints
- Audio encoding: `Linear PCM`
- Audio sample rate: `48 kHz`
- Audio bit depth: `24-bit`
- Color space: `Rec.709 Gamma 2.4`

### Naming Convention

- `BIBLIONOCR_INTRO_MASTER_v01.mov`
- If rendered at 4K, optionally include size marker:
  - `BIBLIONOCR_INTRO_MASTER_4K_v01.mov`

### Output Directory

- Recommended output directory: [video/intro_v1/exports/README.md](video/intro_v1/exports/README.md)
- Operational export path recommendation:
  - `video/intro_v1/exports/master/`

### Checksum Recommendation

- Generate a `SHA-256` checksum for each approved master file.
- Store the checksum in a sidecar text file using the same basename, for example:
  - `BIBLIONOCR_INTRO_MASTER_v01.sha256.txt`

## YouTube

### Purpose

- Distribution-ready upload render for YouTube publication.

### Recommended Settings

- Container: `MP4`
- Recommended codec: `H.264`
- Preferred alternative when workflow supports higher-quality upload source delivery: `H.265` only if upload and review workflow explicitly permits it
- Resolution: `1920x1080 minimum`
- Frame rate: `24 fps`
- Recommended bitrate:
  - `16-20 Mbps` for `1080p`
  - `35-45 Mbps` for optional `4K` upload master
- Audio encoding: `AAC`
- Audio sample rate: `48 kHz`
- Audio bitrate: `320 kbps`
- Color space: `Rec.709 Gamma 2.4`

### Naming Convention

- `BIBLIONOCR_INTRO_YOUTUBE_v01.mp4`
- If rendered at 4K, optionally include size marker:
  - `BIBLIONOCR_INTRO_YOUTUBE_4K_v01.mp4`

### Output Directory

- Recommended output directory: [video/intro_v1/exports/README.md](video/intro_v1/exports/README.md)
- Operational export path recommendation:
  - `video/intro_v1/exports/youtube/`

### Checksum Recommendation

- Generate a `SHA-256` checksum for the final upload file.
- Store the checksum in a sidecar text file using the same basename, for example:
  - `BIBLIONOCR_INTRO_YOUTUBE_v01.sha256.txt`

## Output Naming Rules

- Use all-caps project identifier: `BIBLIONOCR_INTRO`
- Include output class:
  - `MASTER`
  - `YOUTUBE`
- Include optional size marker only when necessary:
  - `4K`
- Include explicit version number:
  - `v01`, `v02`, `v03`

## Render Review Checklist

- Export uses the approved `24 fps` frame rate.
- Export preserves the approved `45 second` runtime.
- Export resolution matches the intended delivery target.
- Audio is rendered at `48 kHz`.
- Scene timing is unchanged from the approved package.
- Final narration completes before fade to black.
- Closing black hold is preserved.
- No visible typography clipping or unsafe-margin issues are present.
- Color output remains consistent with `Rec.709 Gamma 2.4` delivery intent.
- Final file name matches the approved naming convention.
- `SHA-256` checksum has been generated and stored with the export.