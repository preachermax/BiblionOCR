# BiblionOCR Project Architecture

## Overview
BiblionOCR is a comprehensive Optical Character Recognition (OCR) system specifically designed for processing ancient text manuscripts, particularly supporting both Greek and Latin languages. The system manages the complete workflow from PDF source documents through image preprocessing, character training, OCR execution, and text correction/verification.

---

## 1. MAIN ENTRY POINTS

### Primary Entry Points
1. **MyServer.py** - Main OCR workflow manager
   - Central hub for the entire OCR pipeline
   - Manages image/text loading and display
   - Coordinates all preprocessing and OCR operations
   - Handles session settings and workflow configuration

2. **MyBoxer.py** - Main UI for box creation and editing
   - Standalone application that can launch from MyServer
   - Core tool for creating and editing character/word/line boxes

### Desktop Launch Files
- `BiblionBoxer.desktop` - Quick launcher for MyBoxer
- `βιϐλιον Boxer.desktop` - Greek language variant of launcher

---

## 2. MAJOR PROGRAM FUNCTIONS & WORKFLOWS

### **MyBoxer** - Box Editor & Manager
**Primary Function**: Create, edit, and manage bounding boxes for OCR training data

**Key Operations**:
- Manual/automatic cropping of pages into language sections
- Box creation for pages, lines, glyphs/characters, and words
- Deskew operations on images
- Integration with other tools via action menu
- Supports both Greek and Latin text
- UI components:
  - Image display and zoom controls
  - Line spacing adjustment
  - Box table management
  - Text editing capabilities

**Dependencies**: MyBoxerUI, Training module, Dialog dialogs

**Related UI File**: [MyBoxerUI.py](MyBoxerUI.py) - PyQt5 UI definition generated from QtDesigner

---

### **MyPixler** - Image Processing & Manipulation
**Primary Function**: Pixel-level image editing and preprocessing

**Key Operations**:
- PDF extraction to TIFF/PNG formats
- Image format conversions (PDF→TIFF→PNG, indexed/monochrome)
- Auto-cropping of language regions
- Deskewing of monochrome/indexed images
- Image resizing, rotation, flipping
- Brightness, contrast, and saturation adjustments
- Cartoon effects, sharpening, inversion
- Support for both Greek and Latin language workflows

**Key Classes**:
- `PixlerMain` - Main application window
- `Images` - Image processing wrapper
- `Brightness` - Brightness/contrast adjustment UI
- `Filter` - Filter application UI
- `Adjust` - Image transformation UI

**Related UI File**: [MyPixlerUI.py](MyPixlerUI.py)

---

### **MyGlypher** - Character/Glyph Extraction & Management
**Primary Function**: Extract, categorize, and manage individual character glyphs

**Key Operations**:
- Automatic glyph/character box creation from line images
- Character reference integration
- Line spacing controls
- Glyph numbering and organization
- UI components:
  - Glyph image display with zoom
  - Character reference viewer
  - Line height adjustment
  - Find and replace functionality

**Key Classes**:
- `MainWindow` - Main application UI (extends Ui_Glypher)

**Related UI File**: [MyGlypherUI.py](MyGlypherUI.py)

**Dependencies**: ChrReference module, Training, MyPixler

---

### **MyGrounder** - Ground Truth Establishment & Review
**Primary Function**: Validate and establish ground truth training data

**Key Operations**:
- Review page/line/glyph images with corresponding text
- Verify OCR-generated boxes against manual corrections
- Ground truth data validation
- Integration with Versifier for verse-level corrections
- Cross-reference management

**Key Classes**:
- `Ui_MainWindow` - Main ground truth review interface
- `pandasModel` - Table model for data display
- Custom exception classes for error handling

**Related UI File**: [MyGrounderUI.py](MyGrounderUI.py)

**Dependencies**: Training, MyVersifier, MyScanner, MyBoxer, MyExplorer

---

### **MyScanner** - Image Line Scanning & Cropping
**Primary Function**: Automatically scan and crop images into individual text lines

**Key Operations**:
- Auto-crop images to text lines with configurable parameters
- Rename line images for ground truth tracking
- Organize lines into directories by language/book
- Support for both Greek and Latin manuscripts
- Batch processing capabilities

**Key Classes**:
- `MainWindow` - Scanner application interface

**Related UI File**: [MyScannerUI.py](MyScannerUI.py)

**Dependencies**: Training, MyVersifier, MyWriter, MyBoxer, MyPixler, MyExplorer

---

### **MyReader** - OCR Text Reading & Display
**Primary Function**: Execute OCR on images and display results

**Key Operations**:
- Load images and perform Tesseract OCR
- Display raw OCR output
- Text/image side-by-side comparison
- Verse correction workflows
- Line height and zoom controls

**Key Classes**:
- `MainWindow` - OCR reader interface

**Related UI File**: [MyReaderUI.py](MyReaderUI.py)

**Dependencies**: PreProcess, Training, ChrReference, MyPixler

---

### **MyTrainer** - Tesseract OCR Model Training
**Primary Function**: Train custom Tesseract models for improved OCR accuracy

**Key Operations**:
- Manage training data and parameters
- Track training sessions
- Load and save session settings
- Character reference integration

**Key Classes**:
- `Ui_MainWindow` - Trainer interface

**Related UI File**: [MyTrainerUI.py](MyTrainerUI.py)

**Dependencies**: SqliteHelper, ext modules

---

### **MyLexer** - Lexical Analysis
**Primary Function**: Analyze word/character patterns for linguistic processing

**Note**: Uses same UI structure as MyGlypher (MyGlypherUI.py)
**Key Dependencies**: Training, dialog modules

---

### **MyWriter** - Text Document Editing
**Primary Function**: Create and edit corrected OCR text with formatting

**Key Operations**:
- Text editing with Greek font support (FROMVS font)
- Document formatting (bold, italic, alignment)
- File import/export
- Find and replace functionality
- Font and font size selection
- Line spacing controls
- Word count and statistics

**Key Classes**:
- `Main` - Writer application window
- Session management from JSON config

**Related UI File**: [MyWriterUI.py](MyWriterUI.py)

**Dependencies**: ext modules, dialog utilities

---

### **MyVersifier** - Verse/Text Verification & Correction
**Primary Function**: Verify and correct OCR text against reference texts at verse level

**Key Operations**:
- Book/chapter/verse navigation
- Side-by-side verse comparison (OCR vs. reference)
- Variant recording and tracking
- Word-level corrections
- Line height adjustment
- OCR model selection
- Normalization of variant forms
- Integration with MyResolver for complex cases

**Key Classes**:
- `Ui_MainWindow` - Versifier interface with extensive signal connections

**Related UI File**: [MyVersifierUI.py](MyVersifierUI.py)

**Dependencies**: SqliteHelper, ChrReference, ext modules (versifiercount, versefind, reffind)

---

### **MyResolver** - Variant Resolution
**Primary Function**: Resolve OCR errors and text variants

**Key Operations**:
- Load variant/error database
- Filter by variant type (preserved, corrected, errors, unresolved)
- Display variant word information with Strong/RMAC/Lemma codes
- Update variant classifications
- Mark variants as resolved
- Batch operations on similar variants

**Key Classes**:
- Variant table management
- SQL operations on error database

**Related UI File**: MyResolverUI.ui (Qt Designer format)

**Dependencies**: SqliteHelper, UI_Icons

---

### **MyExplorer** - Project File Browser
**Primary Function**: Navigate and open project files and folders

**Key Operations**:
- Tree view of project structure starting at Model/Project/
- Drag and drop support
- Open files with system default applications
- Context menu operations

**Key Classes**:
- `MyFileBrowser` - File explorer window extending Ui_Explorer

**Related UI File**: [MyExplorerUI.py](MyExplorerUI.py)

---

### **MyServer** - OCR Processing Server
**Primary Function**: Server-based OCR processing (infrastructure for batch operations)

**Key Operations**:
- Manages various image transformation dialogs
- PDF extraction/conversion operations
- Image processing pipeline orchestration

**Supported Dialogs**:
- Extract PDF pages
- PDF to TIFF conversion
- TIFF to monochrome conversion
- Monochrome to PNG conversion
- Deskewing operations
- Language-specific processing (Greek/Latin)

**Dependencies**: PreProcess, Training, multiple dialog UI modules

---

## 3. WORKFLOW PIPELINE

### Primary OCR Workflow (from Qt5BiblionOCR.py)

```
1. Source PDF Input
   ↓
2. PDF Page Extraction (actionextract_pdf)
   ↓
3. PDF to TIFF Conversion (actionpdf_to_tiff)
   ↓
4. TIFF Indexing/Monochrome (actiontiff_to_mono)
   ↓
5. Deskewing (actiondeskew_mono)
   ↓
6. PNG Conversion (actionmono_to_png)
   ↓
7. Language Cropping - Separate Greek/Latin (actionCrop_Languages)
   ↓
8. Format Conversion - Greek/Latin to PNG/TIFF (actionConvert_*_tiff_To_png)
   ↓
9. Deskew Language-Specific (actionDeskew_*_tiff)
   ↓
10. Resize PNG Pages (actionResize_*_png)
   ↓
11. Crop to Lines (actionCrop_*_To_tiff_Lines)
   ↓
12. Rename Lines (actionRename_*_tiff_Lines)
   ↓
13. Stage Lines (actionStage_*_tiff_Lines)
   ↓
14. Text Line Splitting (actionSplit_*_text_lines)
   ↓
15. Text Line Renaming (actionRename*_text_lines)
   ↓
16. Ground Truth Review (actionReview_Ground_Truth → MyGrounder)
   ↓
17. Train Tesseract Model (actionTrain_Tesseract)
   ↓
18. Conduct OCR & Correction (actionCorrect_OCR)
   ↓
19. Verse Verification (actionVerse_Correction → MyVersifier)
```

---

## 4. KEY CONFIGURATION FILES

### Session Management
- **Model/Project/Data/json/Session.json** - Current session state
  - OCR language and model selection
  - Current book/chapter/verse position
  - Font and display preferences
  - Line spacing settings
  - File paths and directories

### Workflow Configuration
- **Model/Data/json/Workflow.json** - Pipeline step definitions
  - Sequence identifiers (SP1-SP11, GP1-GP10, LP1-LP2)
  - Default source folders
  - Workflow and complete output paths

### Book Reference
- **Model/Data/json/BooksAbbrName.json** - Book abbreviations and names
- **Model/Data/json/BooksMarkDown.json** - Folder structure naming for each book

### Character References
- **ViewController/3-ConductOCR/FROMVS ChrReference.txt** - Character reference guide

---

## 5. DATABASE SCHEMA

### Main Databases
- **Model/Project/Data/SQLite/FROMVS.db** - Main OCR results and variants
  - `Variants` table - OCR errors and variants
  - `Resolved` table - Resolved variants
  - Book/chapter/verse/word organization

- **Model/Project/Data/SQLite/TRiBibleWords.db** - Reference word database
  - Word forms with Strong's and RMAC codes
  - Lemma information

---

## 6. UI FILE RELATIONSHIPS

| Program | UI File | Purpose |
|---------|---------|---------|
| MyBoxer | MyBoxerUI.py | Box editing interface |
| MyPixler | MyPixlerUI.py | Image manipulation |
| MyGlypher | MyGlypherUI.py | Glyph extraction |
| MyGrounder | MyGrounderUI.py | Ground truth review |
| MyScanner | MyScannerUI.py | Line scanning |
| MyReader | MyReaderUI.py | OCR reading |
| MyTrainer | MyTrainerUI.py | Model training |
| MyWriter | MyWriterUI.py | Text editing |
| MyVersifier | MyVersifierUI.py | Verse verification |
| MyExplorer | MyExplorerUI.py | File browsing |
| MyServer | MyServerUI.py | Server operations |

---

## 7. DIALOG COMPONENTS

Extensive dialog support for workflow steps:
- **Image Processing Dialogs**: PDF extraction, format conversion, deskewing
- **Cropping Dialogs**: Language separation, line extraction
- **Renaming Dialogs**: For ground truth file organization
- **Staging Dialogs**: For workflow transitions
- **Text Processing Dialogs**: Text splitting, verse pairing

Located in: `ViewController/0-MainUI/Dialogs/` directory

---

## 8. LANGUAGE SUPPORT

### Supported Languages
- **Greek**: Primary focus with comprehensive tooling
- **Latin**: Secondary support with parallel workflows
- **Source**: Common language for reference manuscripts

### Language-Specific Workflows
- Separate processing pipelines for Greek and Latin
- Individual font support (FROMVS for Greek)
- Language-specific OCR models (feg, lat models in Tesseract)
- Separate database tables and file organization

---

## 9. KEY DEPENDENCIES & IMPORTS

### Python Libraries
- **PyQt5**: UI framework (QtWidgets, QtGui, QtCore)
- **OpenCV (cv2)**: Image processing
- **PIL/Pillow**: Image manipulation
- **NumPy**: Array operations
- **Pandas**: Data management
- **PyTesseract**: OCR integration
- **SQLAlchemy**: Database ORM
- **SQLite3**: Database backend

### Custom Modules
- **PreProcess (PreProcess.py)**: Image preprocessing utilities
- **Training (Training.py)**: Training data management
- **ChrReference**: Character reference data
- **SqliteHelper**: Database operations
- **ext/**: Extended utilities (versifiercount, versefind, reffind, scanfind)

---

## 10. EXECUTION & LAUNCHING

### Standalone Execution
Each program can run independently:
```bash
python3 ViewController/0-MainUI/MyBoxer.py
python3 ViewController/0-MainUI/MyPixler.py
python3 ViewController/0-MainUI/MyGlypher.py
python3 ViewController/0-MainUI/MyGrounder.py
python3 ViewController/0-MainUI/MyScanner.py
python3 ViewController/0-MainUI/MyReader.py
python3 ViewController/0-MainUI/MyWriter.py
python3 ViewController/0-MainUI/MyVersifier.py
```

### Main Entry Point
```bash
python3 ViewController/0-MainUI/Qt5BiblionOCR.py
```

### Desktop Launchers
- Double-click `.desktop` files for quick access

---

## 11. PROJECT STRUCTURE ORGANIZATION

```
BiblionOCR/
├── ViewController/
│   ├── 0-MainUI/           # Main UI and applications
│   ├── 1-PreProcess/       # Preprocessing tools
│   ├── 2-TrainTesseract/   # Training utilities
│   ├── 3-ConductOCR/       # OCR execution tools
│   └── 4-PostProcess/      # Post-processing tools
├── Model/
│   ├── Project/
│   │   ├── Data/           # Project data, JSON configs, SQLite DBs
│   │   ├── Images/         # Image files organized by stage
│   │   ├── Text/           # Text files and corrections
│   │   └── Training/       # Training data for Tesseract
│   ├── Developer/          # Development utilities and references
│   └── Backup Copies/      # Previous versions
```

---

## 12. TYPICAL USER WORKFLOWS

### Workflow A: Complete OCR from PDF
1. Launch Qt5BiblionOCR
2. Extract PDF pages
3. Convert to monochrome TIFF
4. Deskew images
5. Crop to languages
6. Crop to text lines
7. Review and stage ground truth (MyGrounder)
8. Train Tesseract model (MyTrainer)
9. Run OCR
10. Verify verses (MyVersifier)
11. Resolve variants (MyResolver)
12. Export corrected text (MyWriter)

### Workflow B: Manual Ground Truth Creation
1. Launch MyBoxer to create boxes
2. Use MyPixler to preprocess images
3. Use MyGlypher for character extraction
4. Use MyGrounder to review
5. Stage data for training

### Workflow C: Text Correction
1. Load OCR results in MyReader
2. Compare with reference in MyVersifier
3. Record variants
4. Resolve issues in MyResolver
5. Final editing in MyWriter

---

## 13. CONFIGURATION & CUSTOMIZATION

### Fonts
- FROMVS [MAXR]: Main display font (Greek-specific)
- Located in: `ViewController/0-MainUI/fonts/`
- Reinstall after each Tesseract font-training update with `ViewController/0-MainUI/update_fonts.py`
- The installer is cross-platform and copies the font into the current user's font locations on Windows, macOS, and Linux

### Stylesheets
- Located in: `ViewController/0-MainUI/Stylesheets/`
- Themes: Classic, Dark Blue, Dark Orange

### Icons
- Located in: `ViewController/0-MainUI/Icons/`
- Dynamic icon resource system (UI_Icons.py)

### Extensions
- `glyphtracer-master/`: Glyph tracing utilities
- `potrace-main/`: Vector tracing for character shapes
- Additional third-party integrations in `ext/` folder
