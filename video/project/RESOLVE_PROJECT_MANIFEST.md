# Resolve Project Manifest

Source documents:

- [Developer/StoryBoard/BIBLIONOCR_INTRO_STORYBOARD.md](Developer/StoryBoard/BIBLIONOCR_INTRO_STORYBOARD.md)
- [video/intro_v1/storyboards/BIBLIONOCR_INTRO_SHOT_LIST.md](video/intro_v1/storyboards/BIBLIONOCR_INTRO_SHOT_LIST.md)

This manifest describes the complete DaVinci Resolve project configuration for the BiblionOCR introduction video without generating proprietary Resolve project files.

## Project Settings

- Project name: `BiblionOCR Intro Video`
- Resolution: `1920x1080 minimum`
- Optional resolution: `3840x2160 (4K)`
- Frame rate: `24 fps`
- Audio sample rate: `48 kHz`
- Primary font reference: `FROMVS.ttf`
- Runtime: `45 seconds`

## Timeline Layout

- Single master timeline for the full `45 second` introduction video
- Timeline structure follows the approved five-scene sequence only
- Scene timing must remain fixed to the approved storyboard
- Fade and cross dissolve are the only allowed transition families

## Media Bins

### Assets

- Category A - Emergence imagery
- Category B - Cognition imagery
- Category C - Systems imagery
- Category D - Architecture imagery
- Category E - Identity imagery

### Audio

- Final narration file
- Ambient drone bed
- Any supporting ambient audio approved for the final mix

### Typography

- `FROMVS.ttf`
- Title and overlay text reference cards
- Verse and footer text reference cards

### Exports

- Master archival render
- YouTube upload render

## Track Layout

### Video Tracks

- `V1 Background`
- `V2 Visual overlays`
- `V3 Typography`

### Audio Tracks

- `A1 Narration`
- `A2 Ambient audio`

## Expected Imported Assets

- Scene 1 typography-only elements for the Hebrews 11:1 quotation and reference
- Category A imagery for Scene 2
- Category B imagery for Scene 3
- Category C imagery for Scene 3
- Category D imagery for Scene 4
- Category E imagery for Scene 5
- Narration audio matching the approved narration text
- Ambient drone and supporting ambient bed
- `FROMVS.ttf` for all approved typography

## Timeline Assembly Order

### Scene 1 - Foundation

- Time range: `0:00-0:05`
- Visual content: Solid black screen with no imagery and no animation
- Typography content:
  - "Faith is the substance of things hoped for, the evidence of things not seen."
  - `Hebrews 11:1 (KJV)`
- Track placement:
  - `V1 Background`: solid black
  - `V2 Visual overlays`: none
  - `V3 Typography`: centered quote and reference in `FROMVS.ttf`
  - `A1 Narration`: none
  - `A2 Ambient audio`: very low ambient drone begins
- Transition handling: fade in, then fade out

### Scene 2 - Emergence

- Time range: `0:05-0:12`
- Asset category: `A - Emergence`
- Visual content: light gradually emerges from darkness using abstract imagery only, with no user interface and no software imagery
- Narration: `Before systems are built... they are understood.`
- Track placement:
  - `V1 Background`: Category A imagery base
  - `V2 Visual overlays`: none specified
  - `V3 Typography`: none specified
  - `A1 Narration`: Scene 2 narration
  - `A2 Ambient audio`: supportive ambient bed
- Transition handling: slow dissolve

### Scene 3 - System Formation

- Time range: `0:12-0:25`
- Asset categories:
  - `B - Cognition`
  - `C - Systems`
- Visual content: ideas become organized systems through document processing, scanning, data flow, and subtle computational imagery
- Narration: `BiblionOCR is not a single tool... it is a system of interconnected intelligence.`
- Track placement:
  - `V1 Background`: Category B and Category C imagery in approved order
  - `V2 Visual overlays`: system-oriented visual overlays only if needed to support the approved scene intent
  - `V3 Typography`: none specified
  - `A1 Narration`: Scene 3 narration
  - `A2 Ambient audio`: supportive ambient bed
- Transition handling: use approved fade or cross dissolve only

### Scene 4 - Architecture Reveal

- Time range: `0:25-0:38`
- Asset category: `D - Architecture`
- Visual content: observable architecture, system diagrams, flow, relationships, and order
- Overlays:
  - `MyServer -> EventBus -> OCR -> MyPixler`
  - `DeveloperServices -> Runtime Inspector -> Event Timeline`
- Narration:
  - `Each action becomes observable.`
  - `Each module becomes traceable.`
  - `Each event becomes part of a living architecture.`
- Track placement:
  - `V1 Background`: Category D imagery base
  - `V2 Visual overlays`: architectural diagrams and approved flow overlays
  - `V3 Typography`: overlay text strings listed above
  - `A1 Narration`: Scene 4 narration
  - `A2 Ambient audio`: supportive ambient bed
- Transition handling: use approved fade or cross dissolve only

### Scene 5 - Identity

- Time range: `0:38-0:45`
- Asset category: `E - Identity`
- Visual content: minimal, confident, timeless identity presentation
- Typography content:
  - Title: `BiblionOCR`
  - Tagline: `Making systems visible.`
  - Footer: `Open source. In development.`
  - Footer: `github.com/preachermax/BiblionOCR`
- Narration: `BiblionOCR - designed to make systems visible.`
- Track placement:
  - `V1 Background`: Category E imagery base
  - `V2 Visual overlays`: none beyond identity composition support
  - `V3 Typography`: title, tagline, and footer stack
  - `A1 Narration`: Scene 5 narration
  - `A2 Ambient audio`: restrained ambient support into black
- Transition handling: narration concludes before fade to black, then hold black approximately one second before video end

## Export Presets

### Master Archival Render

- Purpose: high-quality retained master
- Resolution: `1920x1080 minimum`, with `3840x2160` permitted when the project is finished in 4K
- Frame rate: `24 fps`
- Audio sample rate: `48 kHz`
- Audio layout: full mix with narration on `A1` and ambient audio on `A2` represented in the final render
- Deliverable location: `Exports` bin and production export folder

### YouTube Upload Render

- Purpose: platform upload deliverable
- Resolution: `1920x1080` minimum
- Frame rate: `24 fps`
- Audio sample rate: `48 kHz`
- Audio layout: final mixed program audio suitable for direct upload
- Deliverable location: `Exports` bin and production export folder

## Restrictions

- Do not add scenes beyond the approved five-scene structure
- Do not modify narration text
- Do not modify storyboard timing
- Treat the storyboard and shot list as authoritative at all times