# BiblionOCR - Quick Reference Guide

## Program Quick Functions

| Program | Purpose | Key Actions | Input | Output | Related UI |
|---------|---------|-------------|-------|--------|-----------|
| **MyBoxer** | Box editing & creation | Create/edit boxes for pages, lines, glyphs, words; deskew; crop | Images | Box coordinates | MyBoxerUI.py |
| **MyPixler** | Image processing | PDF→TIFF→PNG; format conversion; deskew; crop; adjust colors | PDF, TIFF, PNG | Processed images | MyPixlerUI.py |
| **MyGlypher** | Character extraction | Extract glyphs; character reference; line height control | Line images | Glyph boxes | MyGlypherUI.py |
| **MyGrounder** | Ground truth review | Validate boxes; review image-text pairs; establish training data | Images + text | Verified data | MyGrounderUI.py |
| **MyScanner** | Line scanning | Auto-crop images to lines; rename; organize by book | Page images | Line images | MyScannerUI.py |
| **MyReader** | OCR execution | Run Tesseract; display OCR results; compare with images | Images | OCR text | MyReaderUI.py |
| **MyTrainer** | Model training | Train Tesseract models; manage training sessions | Ground truth | Models | MyTrainerUI.py |
| **MyWriter** | Text editing | Create/edit corrected text; formatting; font control | Text files | Formatted text | MyWriterUI.py |
| **MyVersifier** | Verse verification | Compare OCR vs reference; record variants; navigate verses | OCR text + reference | Corrections | MyVersifierUI.py |
| **MyResolver** | Error resolution | Resolve variants; filter by error type; mark as resolved | Variant DB | Resolved variants | MyResolverUI.ui |
| **MyExplorer** | File browser | Navigate project structure; open files | File system | Opened files | MyExplorerUI.py |
| **MyServer** | Batch processing | Orchestrate pipeline; manage dialogs | Config files | Processed data | MyServerUI.py |

---

## Main Entry Points

### To Start The Project:
```
# Full OCR Pipeline
python3 Qt5BiblionOCR.py

# Individual Tools
python3 MyBoxer.py              # Box creation
python3 MyPixler.py             # Image processing
python3 MyGlypher.py            # Character extraction
python3 MyGrounder.py           # Ground truth review
python3 MyScanner.py            # Line scanning
python3 MyReader.py             # OCR reading
python3 MyTrainer.py            # Model training
python3 MyWriter.py             # Text editing
python3 MyVersifier.py          # Verse verification
python3 MyResolver.py           # Variant resolution
python3 MyExplorer.py           # File browser
```

---

## OCR Pipeline Sequence

```
1. PDF Input → MyPixler (Extract Pages)
2. Pages → MyPixler (PDF→TIFF→PNG)
3. Pages → MyPixler (Crop to Languages: Greek/Latin)
4. Pages → MyScanner (Crop to Lines)
5. Lines → MyGlypher (Extract Glyphs)
6. Glyphs → MyGrounder (Review & Validate)
7. Data → MyTrainer (Train Tesseract)
8. Images → MyReader (Run OCR)
9. OCR Text → MyVersifier (Verify/Correct)
10. Variants → MyResolver (Resolve Errors)
11. Final Text → MyWriter (Export)
```

---

## Current Project Contract

- Select or create the active project in `MyServer` first.
- `MyServer` now publishes the active project to shared session state for the rest of the runtime modules.
- Other tools should treat that shared selection as the current project instead of inferring project identity only from the last opened file.
- If a module shows `Project: none`, open or switch the project in `MyServer` and let the module refresh.

---

## Project Status and Milestones

- Main runtime modules now show a common status-bar surface with the current project, workflow status, overall progress, and a `Milestones` button.
- The `Milestones` button opens the shared milestone editor dialog for the currently selected project.
- Milestones are persisted per project in `Model/Project/Data/json/ProjectTracking.json`.
- Project selection is shared through `Model/Project/Data/json/Session.json`.
- The milestone editor is intended to be user-visible and manually editable, not only auto-derived from file artifacts.

Modules with the common project-status surface:

- `MyServer`
- `MyPixler`
- `MyScanner`
- `MyReader`
- `MyWriter`
- `MyGrounder`
- `MyVersifier`
- `MyTrainer`
- `MyGlypher`
- `MyBoxer`
- `MyLexer`
- `MyResolver`
- `MyExplorer`
- `MyLauncher`

---

## Shared Print And Exit Menu Support

- `MyServer` remains the source implementation for print flow behavior.
- `ViewController/0-MainUI/print_menu_support.py` now provides shared controller-side print wiring for `MyScanner`, `MyReader`, `MyGlypher`, `MyVersifier`, `MyWriter`, `MyPixler`, and `MyBoxer`.
- `actionPrint_Preview` now follows the active or first available print target for those modules instead of each module duplicating its own preview routing.
- `actionExit` is wired in the controller layer for `MyServer`, `MyGrounder`, `MyLauncher`, `MyLexer`, and `MyTrainer` when the matching UI action exists.
- `MyExplorer` and `MyResolver` are intentionally excluded from the `actionExit` rollout.
- See `PRINT_AND_EXIT_MENU_SUPPORT.md` for the full controller/UI contract.

---

## Key Workflows

### Workflow 1: Complete OCR from PDF
MyPixler → MyScanner → MyGrounder → MyTrainer → MyReader → MyVersifier → MyResolver → MyWriter

### Workflow 2: Manual Box Creation
MyBoxer → MyGrounder → MyTrainer

### Workflow 3: Text Correction
MyReader + MyVersifier → MyResolver → MyWriter

### Workflow 4: Image Preprocessing
MyPixler → MyGlypher → MyGrounder

---

## Database Tables

### FROMVS.db (Main OCR Database)
- `Variants` - OCR errors and variants with Strong's/RMAC codes
- `Resolved` - Resolved variants

### TRiBibleWords.db (Reference Words)
- Word forms with linguistic codes

---

## Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| Session.json | Current state (book, font, paths) | Model/Project/Data/json/ |
| Workflow.json | Pipeline steps and folders | Model/Data/json/ |
| BooksAbbrName.json | Book names and abbreviations | Model/Data/json/ |
| BooksMarkDown.json | Folder naming conventions | Model/Data/json/ |

---

## File Organization

```
Model/Project/
├── Data/               # JSON configs, SQLite databases
├── Images/             # Image files by processing stage
│   ├── source/
│   ├── greek/
│   ├── latin/
│   └── (various processing stages)
├── Text/               # Text files and corrections
└── Training/           # Tesseract training data
```

---

## Key Fonts & Resources

| Resource | Location | Usage |
|----------|----------|-------|
| FROMVS Font | fonts/ | Greek text display |
| Icons | Icons/ | UI icons |
| Stylesheets | Stylesheets/ | Theme definitions |
| Character Reference | ../3-ConductOCR/FROMVS ChrReference.txt | Character codes |

### Release Font Update

- Use `update_fonts.py` before a final release or after retraining the Tesseract font assets
- The installer refreshes the project font path and then copies to the active user/system font locations when available

---

## Language Support

| Language | File Prefix | Processing | Model |
|----------|-----------|-----------|-------|
| Greek | greek_ | Full pipeline | feg (Tesseract) |
| Latin | latin_ | Full pipeline | lat (Tesseract) |
| Source | source_ | Reference | (comparison) |

---

## Common Menu Options

### Image Processing (MyPixler)
- Extract PDF → actionextract_pdf
- PDF to TIFF → actionpdf_to_tiff
- TIFF to Mono → actiontiff_to_mono
- Deskew → actiondeskew_mono
- Crop Languages → actionCrop_Languages

### Line Processing (MyScanner/MyBoxer)
- Crop to Lines → actionCrop_Greek_To_tiff_Lines
- Rename Lines → actionRename_Greek_tiff_Lines
- Stage Lines → actionStage_Greek_tiff_Lines

### Verification (MyVersifier)
- Navigate verses → BothPrevBookButton, BothNextBookButton, etc.
- Record variants → Recorderbutton
- Resolve issues → Resolvebutton
- Normalize text → NormcheckBox

---

## UI Integration Points

All applications use consistent patterns:
- Session loading/saving (JSON)
- Project path management
- Standardized dialogs
- Common preprocessing (PreProcess module)
- Unified database access (SqliteHelper)

---

## Extensions & Tools

| Tool | Location | Purpose |
|------|----------|---------|
| glyphtracer | external/local tool | Glyph tracing |
| potrace | external/local tool | Vector tracing |
| Version finder | ext/versefind.py | Locate verses |
| Scan finder | ext/scanfind.py | Locate scan regions |

---

## Typical User Actions

1. **Load PDF**: Qt5BiblionOCR → File menu
2. **Preprocess**: MyPixler → drag & drop or file dialog
3. **Create Ground Truth**: MyBoxer → draw boxes
4. **Review**: MyGrounder → validate data
5. **Train**: MyTrainer → select data, train
6. **OCR**: MyReader → load image, run OCR
7. **Correct**: MyVersifier → navigate verses, mark corrections
8. **Resolve**: MyResolver → filter variants, update
9. **Export**: MyWriter → save corrected text

10. **Release**: MyTrainer → refresh fonts with `update_fonts.py` before final compilation

---

## Debugging Tips

- Check Session.json for current settings
- Look in Model/Data/json/Workflow.json for path issues
- View console output for Tesseract errors
- Use MyExplorer to verify file organization
- Check SQLite databases for data integrity
- Verify fonts are installed (FROMVS)

---

## Performance Considerations

- Large PDFs: Process in sections using MyPixler
- Image operations: Higher resolution = longer processing
- OCR: Speed depends on Tesseract model and image quality
- Database: Optimize variant queries in MyResolver
- UI responsiveness: Long operations may block UI (consider threading)

