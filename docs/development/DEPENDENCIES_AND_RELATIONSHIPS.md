# BiblionOCR - Program Dependencies & Relationships

## Dependency Graph

```
                           Qt5BiblionOCR.py (Main Entry)
                                    |
                  __________________|__________________
                 |                  |                  |
           MyPixler.py      MyScanner.py      MyGrounder.py
                 |                  |                  |
           [Images]          [Line Images]      [Validation]
                 |                  |                  |
                 └──────────┬───────┬──────────────────┘
                            |
                      MyBoxer.py (Boxes)
                            |
                    [Box Coordinates]
                            |
                      MyGlypher.py (Glyphs)
                            |
                    [Glyph Data]
                            |
                      MyTrainer.py (Training)
                            |
                    [Trained Models]
                            |
                      MyReader.py (OCR)
                            |
                    [Raw OCR Text]
                            |
                      MyVersifier.py (Verification)
                            |
                    [Verified Text]
                            |
                      MyResolver.py (Resolution)
                            |
                    [Resolved Variants]
                            |
                      MyWriter.py (Output)
                            |
                    [Final Text]
```

---

## Program Relationships & Dependencies

### 1. MyPixler (Image Processing Hub)
- **Depends On**:
  - PreProcess module (image operations)
  - PyQt5 (GUI)
  - OpenCV, PIL (image libraries)
  - Dialog modules (user input)
  
- **Used By**:
  - Qt5BiblionOCR (main pipeline)
  - MyScanner (line extraction)
  - MyBoxer (image display)
  
- **Provides To**:
  - Preprocessed images for all downstream tools

---

### 2. MyBoxer (Box Creation & Management)
- **Depends On**:
  - MyBoxerUI.py (UI definition)
  - Training module (box operations)
  - MyPixler (image display)
  - Dialogs for various tasks
  
- **Used By**:
  - Qt5BiblionOCR (menu access)
  - MyGrounder (for validation)
  - Manual box creation workflows
  
- **Provides To**:
  - Box coordinates for MyGrounder and MyTrainer

---

### 3. MyScanner (Line Scanning)
- **Depends On**:
  - MyScannerUI.py (UI)
  - Training module (line operations)
  - CropTif module
  - MyBoxer (box info)
  
- **Used By**:
  - Qt5BiblionOCR (pipeline)
  - Line extraction workflows
  
- **Provides To**:
  - Line images for MyGlypher

---

### 4. MyGlypher (Character Extraction)
- **Depends On**:
  - MyGlypherUI.py (UI)
  - ChrReference (character info)
  - Training module
  - MyPixler (image ops)
  
- **Used By**:
  - Character-level OCR workflows
  
- **Provides To**:
  - Glyph data for MyTrainer

---

### 5. MyGrounder (Ground Truth Review)
- **Depends On**:
  - MyGrounderUI.py (UI)
  - Training module
  - SqliteHelper (database)
  - MyVersifier, MyScanner, MyBoxer (cross-reference)
  
- **Used By**:
  - Ground truth validation workflows
  - Before MyTrainer
  
- **Provides To**:
  - Validated training data for MyTrainer

---

### 6. MyReader (OCR Execution)
- **Depends On**:
  - MyReaderUI.py (UI)
  - PyTesseract (OCR engine)
  - PreProcess module
  - MyPixler (image display)
  - ChrReference (character info)
  
- **Used By**:
  - After MyTrainer
  - Direct OCR workflows
  
- **Provides To**:
  - Raw OCR text for MyVersifier

---

### 7. MyTrainer (Model Training)
- **Depends On**:
  - MyTrainerUI.py (UI)
  - Training module
  - SqliteHelper (database)
  - Ground truth data from MyGrounder
  - Release font path refreshed by `update_fonts.py` before final compilation
  
- **Used By**:
  - Model development
  - Before MyReader
  - Final release packaging for the MyTrainer module
  
- **Provides To**:
  - Trained Tesseract models

- **Release Qualification**:
  - This module qualifies as release-facing because it consumes the current training font state and must be validated after each Tesseract font update

---

### 8. MyVersifier (Verse Verification)
- **Depends On**:
  - MyVersifierUI.py (UI)
  - SqliteHelper (database queries)
  - ChrReference (character codes)
  - ext.versefind (verse navigation)
  - MyResolver (for complex issues)
  
- **Used By**:
  - Text correction workflows
  - After MyReader
  
- **Provides To**:
  - Verified verses for MyResolver

---

### 9. MyResolver (Variant Resolution)
- **Depends On**:
  - SqliteHelper (variant database)
  - UI_Icons (icon resources)
  - Variant database (FROMVS.db)
  
- **Used By**:
  - Error correction
  - After MyVersifier
  
- **Provides To**:
  - Resolved variants for MyWriter

---

### 10. MyWriter (Text Document Editing)
- **Depends On**:
  - MyWriterUI.py (UI)
  - ext modules (utilities)
  - Find/replace functionality
  
- **Used By**:
  - Final output stage
  - Manual text editing
  
- **Provides To**:
  - Final corrected text files

---

### 11. MyExplorer (File Browser)
- **Depends On**:
  - MyExplorerUI.py (UI)
  - PyQt5 file system model
  
- **Used By**:
  - Navigation to any tool
  - Opens with system default apps
  
- **Provides To**:
  - Quick access to project files

---

### 12. MyServer (Batch Processing)
- **Depends On**:
  - MyServerUI.py (UI)
  - PreProcess module
  - Training module
  - All dialog modules
  
- **Used By**:
  - Batch/automated workflows
  
- **Provides To**:
  - Orchestrated pipeline execution

---

## Shared Module Dependencies

### Training Module (Training.py)
Used by: MyBoxer, MyScanner, MyGlypher, MyGrounder, MyTrainer, MyReader

Functions provided:
- `sortcroplines()` - Crop and sort line images
- `renameimages()` - Rename images for ground truth
- `splittextlines()` - Split text into lines
- `text2groundtruth()` - Convert text to ground truth format

### PreProcess Module (PreProcess.py)
Used by: MyPixler, MyReader, MyServer

Functions provided:
- `pdfExtractPages()` - Extract PDF pages
- `pdf4tif()` - PDF to TIFF with 4-page layout
- `pdf2tif()` - PDF to TIFF conversion
- `tiff2tiffidx()` - TIFF to indexed (monochrome)
- `tiff2pngidx()` - TIFF to PNG indexed
- `deskewfiles()` - Deskew TIFF and PNG
- `deskewimage()` - Deskew single image
- `croplangs()` - Crop by language
- `resizepngs()` - Batch resize PNG

### SqliteHelper Module
Used by: MyTrainer, MyVersifier, MyResolver

Functions provided:
- `select()` - Query database
- `insert()` - Insert records
- `update()` - Update records

### ChrReference Module (ChrReference.py)
Used by: MyGlypher, MyReader, MyVersifier

Functions provided:
- Character code lookup
- Unicode mappings
- Reference displays

---

## Data Flow Paths

### Path 1: Complete OCR Pipeline
```
PDF File
    ↓
MyPixler.actionextract_pdf()
    ↓
Page Images (TIFF)
    ↓
MyPixler (convert/process)
    ↓
MyPixler.actionCrop_Languages()
    ↓
Greek/Latin Separated
    ↓
MyScanner.actionCrop_Greek_To_tiff_Lines()
    ↓
Line Images
    ↓
MyBoxer/MyGlypher (create boxes)
    ↓
Box Coordinates
    ↓
MyGrounder (review)
    ↓
Ground Truth Data
    ↓
MyTrainer (train)
    ↓
Trained Model
    ↓
MyReader (OCR)
    ↓
Raw OCR Text
    ↓
MyVersifier (verify)
    ↓
Verified Text
    ↓
MyResolver (resolve errors)
    ↓
Final Text
    ↓
MyWriter (output)
```

### Path 2: Manual Box Creation
```
Images
    ↓
MyPixler (preprocess)
    ↓
MyBoxer (create boxes)
    ↓
MyGrounder (review)
    ↓
Training Data → MyTrainer
```

### Path 3: Text Verification
```
OCR Output
    ↓
MyReader (display)
    ↓
MyVersifier (compare with reference)
    ↓
Variants
    ↓
MyResolver (resolve)
    ↓
Corrections
    ↓
MyWriter (finalize)
```

---

## Module Import Chain

```
Qt5BiblionOCR.py
├── MainUI (UI definition)
├── PreProcess
├── Training
├── MyPixler.py
│   ├── MyPixlerUI.py
│   ├── PreProcess
│   └── Dialog modules
├── Dialog modules (multiple)
├── CropTif
├── QtCropImage
├── Qt5SelectRegion
└── ext.mainfind

MyBoxer.py
├── MyBoxerUI.py
├── Training
├── PreProcess
├── Dialog modules
├── ext.mainfind
└── MySlidersUI.py

MyGrounder.py
├── MyGrounderUI.py
├── Training
├── SqliteHelper
├── MyVersifier
├── MyScanner
├── MyBoxer
├── MyExplorer
└── ChrReference

MyReader.py
├── MyReaderUI.py
├── PreProcess
├── MyPixler
├── CropTif
├── QtCropImage
├── Qt5SelectRegion
├── Training
└── ChrReference

MyVersifier.py
├── MyVersifierUI.py
├── SqliteHelper
├── ChrReference
├── ext.versefind
├── ext.reffind
└── ext.versifiercount

MyResolver.py
├── SqliteHelper
└── UI_Icons

MyWriter.py
├── MyWriterUI.py
└── ext modules
```

---

## Data Flow: Key Variables

### Session State (Session.json)
- Current book/chapter/verse
- Image and text file paths
- Font and display settings
- OCR language and model
- Line spacing
- All programs read/write this file

### Workflow Configuration (Workflow.json)
- Processing step definitions
- Default source/destination folders
- Referenced by MyServer and dialogs

### Database Connections
- FROMVS.db: Variants, Resolved tables
- TRiBibleWords.db: Reference words
- Accessed by MyVersifier, MyResolver, MyTrainer

---

## Execution Dependencies

### Before Running MyReader
✓ MyPixler (images preprocessed)
✓ MyTrainer (model trained)

### Before Running MyVersifier
✓ MyReader (OCR completed)

### Before Running MyResolver
✓ MyVersifier (variants identified)

### Before Running MyTrainer
✓ MyGrounder (ground truth validated)

---

## Communication Between Programs

### Via Session Files
- All programs share Session.json
- Changes in one program visible to all
- Persistent across sessions

### Via Command Line (os.system)
- Qt5BiblionOCR launches other programs as separate processes
- E.g., `python3 ViewController/0-MainUI/MyWriter.py`

### Via Database
- Shared SQLite databases
- MyVersifier and MyResolver coordinate through FROMVS.db
- Variant tables track changes across tools

### Via File System
- Images passed between tools
- Boxes stored in JSON or database
- Text files exchanged

---

## Key Integration Points

| Integration Type | Programs | Method |
|-----------------|----------|--------|
| Image Display | MyBoxer, MyPixler, MyReader | Shared display code |
| Database Queries | MyVersifier, MyResolver | SqliteHelper |
| Settings | All programs | Session.json |
| Training Data | MyGrounder, MyTrainer | File sharing |
| OCR Output | MyReader, MyVersifier | Text files |
| Variants | MyVersifier, MyResolver | FROMVS.db |

---

## Circular Dependencies (Cross-References)

- **MyGrounder** ↔ **MyVersifier**: Can access each other
- **MyVersifier** → **MyResolver**: One-way for resolution
- **MyBoxer** ↔ **MyPixler**: Share image operations
- **MyScanner** → **MyBoxer**: Uses box information
- **MyReader** → **MyPixler**: For image display

These are resolved through module imports and runtime instantiation rather than circular imports.

