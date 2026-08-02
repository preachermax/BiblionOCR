# Timeline Assembly Guide

Source documents present in this workspace:

- [../storyboards/BIBLIONOCR_INTRO_STORYBOARD.md](../storyboards/BIBLIONOCR_INTRO_STORYBOARD.md)
- [../storyboards/BIBLIONOCR_INTRO_SHOT_LIST.md](../storyboards/BIBLIONOCR_INTRO_SHOT_LIST.md)
- [RESOLVE_PROJECT_MANIFEST.md](RESOLVE_PROJECT_MANIFEST.md)

This guide describes how to assemble the BiblionOCR introduction video timeline in DaVinci Resolve.

Do not alter approved production timing.

Do not modify approved narration.

## 1. Media Import Order

Import media in this order so the project structure stays aligned with the approved package.

1. Import typography dependencies:
   - `FROMVS.ttf`
   - verse text reference cards if used as design references
   - title and footer text reference cards if used as design references
2. Import narration assets:
   - final narration audio file
3. Import ambient audio assets:
   - ambient drone bed
   - any approved supporting ambient audio
4. Import visual assets by approved semantic category:
   - Category A imagery for Scene 2
   - Category B imagery for Scene 3
   - Category C imagery for Scene 3
   - Category D imagery for Scene 4
   - Category E imagery for Scene 5
5. Import any approved overlay graphics needed to support Scene 4 architectural flow presentation.

## 2. Bin Population

Create and populate these media bins exactly.

### Assets

- Add all approved visual assets grouped by scene-use category:
  - `A - Emergence`
  - `B - Cognition`
  - `C - Systems`
  - `D - Architecture`
  - `E - Identity`

### Audio

- Add the final narration file
- Add the ambient drone bed
- Add any approved supporting ambient audio used beneath narration

### Typography

- Add `FROMVS.ttf`
- Add any approved text reference materials for:
  - Hebrews 11:1 quotation and reference
  - Scene 4 overlay strings
  - Scene 5 title, tagline, and footer lines

### Exports

- Reserve this bin for generated outputs only:
  - master archival render
  - YouTube upload render

## 3. Timeline Creation

1. Create a new master timeline named for the BiblionOCR introduction video.
2. Set timeline resolution to `1920x1080 minimum`.
3. If the approved finishing plan is 4K, set the timeline to `3840x2160` while preserving the same scene timing.
4. Set timeline frame rate to `24 fps`.
5. Set audio sample rate to `48 kHz`.
6. Confirm total timeline runtime target remains `45 seconds`.

## 4. Track Assignment

Create tracks in this order.

### Video Tracks

- `V1 Background`
- `V2 Visual overlays`
- `V3 Typography`

### Audio Tracks

- `A1 Narration`
- `A2 Ambient audio`

## 5. Shot Placement

Assemble shots in approved sequence only.

### Scene 1 - Foundation

- Time range: `0:00-0:05`
- Place a solid black background on `V1 Background`
- Leave `V2 Visual overlays` empty
- Place the quotation and scripture reference on `V3 Typography`
- Leave `A1 Narration` empty
- Start the very low ambient drone on `A2 Ambient audio`

### Scene 2 - Emergence

- Time range: `0:05-0:12`
- Place Category A imagery on `V1 Background`
- Keep `V2 Visual overlays` empty unless an approved non-UI abstract support element is needed
- Leave `V3 Typography` empty unless separately approved
- Place the approved Scene 2 narration on `A1 Narration`
- Continue supportive ambient bed on `A2 Ambient audio`

### Scene 3 - System Formation

- Time range: `0:12-0:25`
- Place Category B and Category C imagery on `V1 Background` in the approved scene span
- Use `V2 Visual overlays` only for system-supportive overlays that do not introduce unauthorized concepts
- Leave `V3 Typography` empty unless separately approved
- Place the approved Scene 3 narration on `A1 Narration`
- Continue supportive ambient bed on `A2 Ambient audio`

### Scene 4 - Architecture Reveal

- Time range: `0:25-0:38`
- Place Category D imagery on `V1 Background`
- Place approved architectural and flow support elements on `V2 Visual overlays`
- Place these exact overlay strings on `V3 Typography`:
  - `MyServer -> EventBus -> OCR -> MyPixler`
  - `DeveloperServices -> Runtime Inspector -> Event Timeline`
- Place the approved Scene 4 narration on `A1 Narration`
- Continue supportive ambient bed on `A2 Ambient audio`

### Scene 5 - Identity

- Time range: `0:38-0:45`
- Place Category E imagery on `V1 Background`
- Keep `V2 Visual overlays` minimal and identity-supportive only
- Place the title, tagline, and footer stack on `V3 Typography`:
  - `BiblionOCR`
  - `Making systems visible.`
  - `Open source. In development.`
  - `github.com/preachermax/BiblionOCR`
- Place the approved Scene 5 narration on `A1 Narration`
- Continue restrained ambient bed on `A2 Ambient audio`
- End narration before fade to black and hold black for approximately one second before video end

## 6. Transition Placement

Apply transitions using the approved rules only.

1. Scene 1:
   - fade in on opening typography
   - fade out before Scene 2
2. Scene 2:
   - use a slow dissolve
3. Scene 3:
   - use fade or cross dissolve only where needed
4. Scene 4:
   - use fade or cross dissolve only where needed
5. Scene 5:
   - fade to black after the final narration line

Do not use:

- glitch effects
- rapid cuts
- flash transitions
- excessive camera motion

## 7. Typography Placement

Use `FROMVS.ttf` for all approved typography placements.

### Scene 1 Typography

- Center the quotation:
  - `"Faith is the substance of things hoped for, the evidence of things not seen."`
- Place the reference beneath it:
  - `Hebrews 11:1 (KJV)`

### Scene 4 Typography

- Place the two architecture overlay lines on `V3 Typography`
- Keep them readable and structurally clear
- Do not substitute different module names or wording

### Scene 5 Typography

- Place title first: `BiblionOCR`
- Place tagline next: `Making systems visible.`
- Place footer lines beneath:
  - `Open source. In development.`
  - `github.com/preachermax/BiblionOCR`

## 8. Audio Synchronization

1. Lock the approved narration text before syncing.
2. Align each narration segment to its approved scene window:
   - Scene 2 narration inside `0:05-0:12`
   - Scene 3 narration inside `0:12-0:25`
   - Scene 4 narration inside `0:25-0:38`
   - Scene 5 narration inside `0:38-0:45`
3. Keep Scene 1 free of narration.
4. Start the ambient drone in Scene 1 and carry ambient support underneath spoken sections.
5. Mix ambient audio low enough that narration remains primary at all times.
6. Ensure Scene 5 narration concludes before the final fade to black.

## 9. Timeline Verification Checklist

- Project resolution is `1920x1080 minimum` or approved `4K`
- Timeline frame rate is `24 fps`
- Audio sample rate is `48 kHz`
- Total runtime remains `45 seconds`
- The timeline contains exactly five scenes
- Scene timing matches the approved storyboard exactly:
  - `0:00-0:05`
  - `0:05-0:12`
  - `0:12-0:25`
  - `0:25-0:38`
  - `0:38-0:45`
- Scene 1 contains no imagery and no narration
- Scene 2 uses Category A imagery only
- Scene 3 uses Category B and Category C imagery
- Scene 4 uses Category D imagery and the exact approved overlay strings
- Scene 5 uses Category E imagery and the exact approved title, tagline, and footer text
- Narration wording is unchanged from the approved source
- Ambient audio supports but never competes with narration
- Only fade and cross dissolve transitions are used
- Final narration completes before the closing fade to black
- Black hold is present at the end of Scene 5