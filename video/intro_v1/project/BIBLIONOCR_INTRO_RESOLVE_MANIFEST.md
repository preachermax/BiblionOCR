# BiblionOCR Intro Resolve Manifest

Source of truth: [Developer/StoryBoard/BIBLIONOCR_INTRO_STORYBOARD.md](Developer/StoryBoard/BIBLIONOCR_INTRO_STORYBOARD.md)

This manifest translates the approved storyboard into editor-facing scene blocks for timeline assembly.

## Project Specifications

- Runtime: `45 seconds`
- Frame rate: `24 fps`
- Resolution: `1920x1080 minimum (4K permitted)`
- Primary font: `FROMVS.ttf`
- Narration: AI generated

## Timeline Blocks

| Scene | Start | End | Duration | Frames @ 24 fps | Asset Category | Overlay Payload | Transition | Audio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Foundation | 0:00 | 0:05 | 5s | 120 | None specified | Quote plus `Hebrews 11:1 (KJV)` centered in `FROMVS.ttf` | Fade in, fade out | Very low ambient drone begins; no narration |
| Emergence | 0:05 | 0:12 | 7s | 168 | `A - Emergence` | None specified | Slow dissolve | Narration primary; ambient support only |
| System Formation | 0:12 | 0:25 | 13s | 312 | `B - Cognition`; `C - Systems` | None specified | Use approved fade or cross dissolve only | Narration primary; ambient support only |
| Architecture Reveal | 0:25 | 0:38 | 13s | 312 | `D - Architecture` | `MyServer -> EventBus -> OCR -> MyPixler`; `DeveloperServices -> Runtime Inspector -> Event Timeline` | Use approved fade or cross dissolve only | Narration primary; ambient support only |
| Identity | 0:38 | 0:45 | 7s | 168 | `E - Identity` | `BiblionOCR`; `Making systems visible.`; `Open source. In development.`; `github.com/preachermax/BiblionOCR` | Narration ends before fade to black; hold black approximately one second before video end | Narration primary, then restrained ambient into black |

## Visual Rules

- Use only storyboard-approved asset categories A-E.
- Category meanings:
  - `A - Emergence`
  - `B - Cognition`
  - `C - Systems`
  - `D - Architecture`
  - `E - Identity`
- The visual language should communicate clarity, structure, and intentional design.

## Transition Rules

- Allowed: Fade, cross dissolve
- Avoid: Glitch effects, rapid cuts, flash transitions, excessive camera motion

## Narration Reference

- Emergence: `Before systems are built... they are understood.`
- System Formation: `BiblionOCR is not a single tool... it is a system of interconnected intelligence.`
- Architecture Reveal: `Each action becomes observable. Each module becomes traceable. Each event becomes part of a living architecture.`
- Identity: `BiblionOCR - designed to make systems visible.`