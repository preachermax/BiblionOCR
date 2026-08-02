"""
BiblionOCR Help System
======================
A comprehensive help system for all BiblionOCR programs.
Provides help dialogs with program descriptions, usage guides, and development notes.

Usage:
    from HelpSystem import HelpDialog, show_help
    
    # Show help for a specific program
    show_help(parent_window, program_name)
    
    # Or create a custom dialog
    dialog = HelpDialog(parent_window, program_name)
    dialog.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QTabWidget, QWidget, QLabel, QScrollArea
)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import os

# ============================================================================
# PROGRAM DOCUMENTATION DATABASE
# ============================================================================

PROGRAM_HELP = {
    'MyBoxer': {
        'title': 'Box Editor (MyBoxer)',
        'icon': '📦',
        'description': '''BiblionOCR Box Editor

The Box Editor is used for creating, editing, and managing character bounding boxes (boxes) 
from document images. These boxes are essential for training Tesseract OCR.

FEATURES:
• Load TIFF image stacks with multi-page support
• Draw and edit rectangular bounding boxes around characters
• Assign character values to boxes
• Validate box data for training
• Export box data in Tesseract format
• Support for Greek and Latin text

PRIMARY WORKFLOW:
1. Load a TIFF image stack (File > Open)
2. Navigate through pages using controls
3. Draw boxes around characters (click and drag)
4. Double-click box to edit character value
5. Save boxes to file (File > Save)
6. Use boxes for Tesseract training

KEY SHORTCUTS:
• Ctrl+O: Open image file
• Ctrl+S: Save boxes
• Delete: Remove selected box
• Double-click: Edit box value
• Scroll wheel: Navigate pages

TOOLBAR BUTTONS:
• Open File: Load TIFF image stack
• Save Boxes: Export to .box format
• Clear: Remove all boxes from current image
• Zoom controls: Adjust image scale
• Slider: Navigate between pages

TIPS FOR DEVELOPERS:
• Box format: image_name.box with tab-separated values
• Each line: character_value left top right bottom page
• Use MyGrounder for automated line generation
• Validate boxes before training in MyTrainer
• Check character encoding for Greek text

DATABASE INTEGRATION:
• Stores box coordinates in SQLite
• Links to original images via image_id
• Tracks validation status per image

See also: MyPixler, MyGrounder, MyTrainer
''',
        'usage': '''DETAILED USAGE GUIDE

OPENING IMAGES:
1. Click "Open" or Ctrl+O
2. Select a TIFF file or image stack
3. First image will load automatically

CREATING BOXES:
1. Position cursor over image
2. Click and drag to create box
3. Release mouse to finish
4. Box appears with selection handles

EDITING BOXES:
1. Click box to select (outline appears in blue)
2. Drag handles to resize
3. Drag center to move
4. Double-click to edit character value

NAVIGATING PAGES:
• Use page slider at bottom
• Use arrow buttons to go next/previous
• Click on image to focus
• Use Page Up/Page Down keys

MANAGING BOXES:
• Select all boxes: Ctrl+A
• Delete selected: Delete key
• Clear all: Edit menu > Clear All
• Undo: Ctrl+Z
• Redo: Ctrl+Y

SAVING AND EXPORTING:
1. Click Save or Ctrl+S
2. Choose format:
   - Tesseract .box files
   - SVG for visualization
   - JSON for database storage
3. Verify output path
4. Confirm save

VALIDATION:
• Boxes should not overlap
• Character values must be assigned
• Box coordinates must be within image bounds
• Font size should be consistent

PERFORMANCE TIPS:
• Work with one image at a time
• Use zoom to see details
• Close unused boxes dialogs
• Save frequently

TROUBLESHOOTING:
• Image won't load: Check file format (TIFF recommended)
• Boxes disappear: Save before closing
• Memory issues: Close other programs
• Character encoding: Ensure UTF-8 for Greek text
''',
        'development': '''DEVELOPMENT NOTES

SOURCE CODE STRUCTURE:
• MyBoxer.py: Main application class
• MyBoxerUI.py: UI definition from Qt Designer
• MyBoxer uses Qt5 graphics view for rendering

KEY CLASSES:
• class MyBoxer(MyBoxerUI.Ui_Boxer, QtWidgets.QMainWindow)
    - Main application window
    - Handles image loading and display
    - Manages box creation and editing

• Graphics scene items:
    - QGraphicsRectItem for boxes
    - Custom mouse handlers for interaction

ARCHITECTURE:
• MVC pattern with UI separate from logic
• QGraphicsView for efficient image display
• Threading for image loading (prevents UI freeze)
• SQLite backend for data persistence

KEY METHODS:
• loadImage(filepath): Load TIFF image
• createBox(x, y, w, h): Create new box
• saveBoxes(): Export to file
• updateDatabase(): Store to SQLite

DATABASE SCHEMA:
TABLE boxes:
  - box_id (PRIMARY KEY)
  - image_id (FOREIGN KEY)
  - left, top, right, bottom (INTEGER)
  - character (TEXT)
  - page_num (INTEGER)
  - validation_status (TEXT)

DEPENDENCIES:
• PyQt5.QtWidgets: UI components
• PyQt5.QtGui: Graphics rendering
• cv2 (OpenCV): Image processing
• tiffcapture: TIFF file handling
• sqlite3: Database

EXTENDING THE CODE:
1. Add new box properties: Modify database schema
2. Add new file formats: Extend saveBoxes()
3. Add OCR preview: Integrate pytesseract
4. Add batch processing: Create WorkerThread

INTEGRATION POINTS:
• Input: Raw TIFF images from scanner
• Output: .box files to MyTrainer
• Database: Stores all box data
• Workflow: Part of ground truth creation pipeline

PERFORMANCE CONSIDERATIONS:
• Large TIFF stacks require efficient loading
• Graphics scene optimization important
• Database indexing on image_id recommended
• Consider lazy loading for very large files

TESTING:
• Unit tests for box creation/editing
• Integration tests with MyTrainer
• Visual regression tests for rendering
• Performance benchmarks for large images

VERSION HISTORY:
v1.0: Initial box editor
v2.0: Added SQLite integration
v2.1: Improved Greek character support
v3.0: Added batch processing

See also: MyBoxerUI.py, MyGrounder.py, MyTrainer.py
'''
    },

    'MyPixler': {
        'title': 'Image Processing (MyPixler)',
        'icon': '🖼️',
        'description': '''Image Viewer and Processor

MyPixler is a general-purpose image viewer and processor for the BiblionOCR pipeline.
It provides image inspection, transformation, and analysis tools.

FEATURES:
• Display TIFF and standard image formats
• Multi-page TIFF stack navigation
• Image transformation tools (rotate, crop, scale)
• Histogram and analysis tools
• Color space conversions
• Real-time effects and filters

PRIMARY WORKFLOW:
1. Load image or TIFF stack
2. Navigate pages
3. Apply transformations as needed
4. Export processed images
5. Use for quality inspection

KEY SHORTCUTS:
• Ctrl+O: Open image
• Ctrl+E: Export
• Fit to window: F
• Actual size: 1
• Zoom in/out: +/-

TOOLBAR:
• Open/Save buttons
• Zoom controls
• Brightness/contrast sliders
• Rotation buttons
• Export button

USES IN PIPELINE:
• Preview OCR results
• Inspect document quality
• Validate image processing
• Check page alignment

See also: MyBoxer, MyGrounder
''',
        'usage': '''DETAILED USAGE GUIDE

LOADING IMAGES:
1. File > Open or Ctrl+O
2. Select image file
3. Navigate pages with slider/buttons

IMAGE VIEWING:
• Pan: Click and drag
• Zoom: Mouse wheel or buttons
• Fit window: Press F
• Full size: Press 1
• Zoom percentage: See status bar

ADJUSTING IMAGE:
• Brightness: Use brightness slider
• Contrast: Use contrast slider
• Gamma: Adjust mid-tones
• Saturation: Enhance colors

TRANSFORMATIONS:
1. Image > Transform menu
2. Choose operation:
   - Rotate (90°/180°/270°)
   - Flip (horizontal/vertical)
   - Crop (select region)
   - Scale (resize)

EXPORTING IMAGES:
1. File > Export or Ctrl+E
2. Choose format (TIFF, PNG, JPG)
3. Set quality if applicable
4. Confirm output location

ANALYSIS TOOLS:
• View > Histogram: Show pixel distribution
• View > Color Stats: RGB/grayscale analysis
• Measure tool: Measure distances

FILTERING:
• Effects > Grayscale: Convert to B&W
• Effects > Blur: Reduce noise
• Effects > Sharpen: Enhance edges
• Effects > Threshold: Create binary image

BATCH OPERATIONS:
• Process > Batch Convert: Multiple files
• Process > Resize All: Scale multiple images
• Process > Rotate All: Rotate batch

See detailed tutorials in Help > Tutorials
'''
    },

    'MyGlypher': {
        'title': 'Character Glyph Editor (MyGlypher)',
        'icon': '✏️',
        'description': '''Character Glyph Editor and Analyzer

MyGlypher is used for examining, editing, and optimizing individual character glyphs
from fonts and creating character databases for OCR recognition.

FEATURES:
• View individual character glyphs
• Edit glyph appearance
• Create character templates
• Analyze glyph properties
• Generate character libraries
• Compare similar glyphs

PRIMARY WORKFLOW:
1. Load font or character database
2. Select character to examine
3. Edit or optimize glyph
4. Save glyph data
5. Build character training set

KEY SHORTCUTS:
• Ctrl+N: New glyph
• Ctrl+S: Save glyph
• Ctrl+D: Duplicate glyph
• Delete: Remove selected glyph

TOOLBAR:
• New/Save/Delete buttons
• Glyph search
• Size adjustment
• Preview panel

USES IN PIPELINE:
• Create font character maps
• Generate training templates
• Optimize character recognition
• Build glyph databases

See also: MyTrainer, MyBoxer
''',
        'usage': '''USAGE GUIDE FOR GLYPH EDITOR

CREATING GLYPHS:
1. Glyph > New or Ctrl+N
2. Draw character shape
3. Name the glyph
4. Set properties (size, weight)
5. Save

EDITING GLYPHS:
1. Select glyph from library
2. Use drawing tools to modify
3. Adjust curves and angles
4. Preview changes
5. Save when satisfied

GLYPH PROPERTIES:
• Name: Character or identifier
• Category: Letter/Number/Symbol
• Font: Source font name
• Size: Point size
• Weight: Thin/Normal/Bold
• Encoding: Unicode value

ORGANIZING GLYPHS:
• Create categories (Greek, Latin, Numbers)
• Tag glyphs for quick search
• Maintain version history
• Export glyph sets

EXPORTING:
• Single glyph: Right-click > Export
• Full set: Glyph > Export Set
• As images: Format > PNG/SVG
• As data: Format > JSON

See detailed tutorials in Help > Tutorials
'''
    },

    'MyGrounder': {
        'title': 'Ground Truth Generator (MyGrounder)',
        'icon': '📝',
        'description': '''Ground Truth Creation Tool

MyGrounder automatically generates ground truth data (boxes and text) from document images.
It creates the training data needed for OCR model training.

FEATURES:
• Automatic text detection and extraction
• Automatic box generation around text
• Batch ground truth creation
• Validation of generated data
• Export in multiple formats

PRIMARY WORKFLOW:
1. Select source images
2. Configure detection parameters
3. Run ground truth generation
4. Review and validate results
5. Export for training

KEY PARAMETERS:
• Language: Greek, Latin, or mixed
• Minimum text size: pixels
• Maximum text size: pixels
• Overlap tolerance: percentage
• Confidence threshold: 0-100%

OUTPUT FORMATS:
• .box files for Tesseract
• .json for database
• .csv for analysis
• SVG for visualization

USES IN PIPELINE:
• Speeds up ground truth creation
• Reduces manual box editing
• Provides initial training data
• Enables batch processing

See also: MyBoxer, MyTrainer
''',
        'usage': '''USAGE GUIDE FOR GROUND TRUTH GENERATOR

BASIC WORKFLOW:
1. Select > Choose source image folder
2. Configure > Set detection parameters
3. Generate > Start ground truth creation
4. Review > Check generated boxes
5. Validate > Ensure quality
6. Export > Save in desired format

DETECTION PARAMETERS:
• Language selection (important!)
• Minimum text height: 8-20 pixels
• Maximum text height: 50-200 pixels
• Line overlap threshold: 0-50%
• Confidence score: 50-99%

BATCH PROCESSING:
1. Folder > Select batch folder
2. Set parameters for entire batch
3. Process > Start batch
4. Monitor progress bar
5. Review results when complete

VALIDATION BEFORE EXPORT:
• Preview generated boxes
• Check character assignments
• Verify no overlaps
• Ensure adequate coverage
• Check language detection

EXPORTING:
1. Choose export format
2. Set output directory
3. Configure export options
4. Start export process
5. Verify files created

TROUBLESHOOTING:
• Poor detection: Adjust language/parameters
• Missing text: Lower confidence threshold
• Too many boxes: Increase size thresholds
• Slow processing: Reduce image resolution

PERFORMANCE TIPS:
• Process large batches overnight
• Use SSD for faster I/O
• Close other applications
• Monitor system resources
'''
    },

    'MyScanner': {
        'title': 'Document Scanner (MyScanner)',
        'icon': '📸',
        'description': '''Document Scanner Interface

MyScanner manages acquisition from physical scanners for the BiblionOCR pipeline.
The current runtime path uses the shared Core scanner workflow rather than an
isolated device dialog.

FEATURES:
• Shared scan wizard and persisted scan settings
• Backend selection through Core Scanner services
• AirScan / eSCL, WIA, TWAIN, and SANE support surfaces
• Threaded scan execution with saved TIFF output
• ADF handoff from MyServer into MyScanner when needed
• Session-backed destination, backend, DPI, and mode restore

PRIMARY WORKFLOW:
1. Open the scan workflow
2. Choose backend, device, DPI, mode, and destination
3. Let device discovery complete
4. Acquire the scan through the selected backend
5. Review the saved TIFF result
6. Continue into OCR or image-processing workflows

KEY SETTINGS:
• Resolution: DPI (200-600 recommended)
• Color mode: Color, Grayscale, B&W
• Paper size: Standard sizes supported
• Brightness: Adjust for document
• Contrast: Improve text visibility

SCANNER SUPPORT:
• AirScan / eSCL for network-capable scanners
• WIA on Windows
• TWAIN where a compatible DSM/source is available
• SANE on Linux and compatible Unix-like systems

USES IN PIPELINE:
• Acquires original documents
• Ensures consistent image quality
• Organizes page sequence
• First step in OCR pipeline

CURRENT NOTES:
• AirScan is the preferred cross-platform path when supported.
• Scan settings are persisted through the session manager.
• MyServer redirects ADF-oriented workflows into MyScanner.

See also: MyServer, MyReader, MyPixler
''',
        'usage': '''SCANNER USAGE GUIDE

STARTING THE WORKFLOW:
1. Open MyScanner
2. Launch the scan action from the toolbar or menu
3. Wait for backend and device discovery to complete
4. Review any restored session settings before scanning

DEVICE SELECTION:
1. Choose the backend first
2. Select a discovered device, or provide an AirScan IP/URL when needed
3. Confirm DPI, mode, source, duplex, and destination folder
4. Continue only with backends reported as available

CONFIGURING SETTINGS:
1. Resolution: 300 DPI is the usual starting point
2. Color: Usually Color or Grayscale
3. Source: Flatbed or feeder depending on hardware
4. Duplex: Enable only when hardware and workflow require it
5. Destination: Confirm the folder where numbered TIFF output will be written

SINGLE SCAN:
1. Place document on scanner
2. Confirm settings in the scan workflow
3. Start the scan
4. Wait for scan completion
5. The saved TIFF appears in the image workflow
6. Continue with OCR or image editing as needed

BATCH SCANNING:
1. Use feeder/ADF-oriented scanning when the hardware supports it
2. Confirm the destination and numbering behavior
3. Acquire pages in sequence
4. Review the saved TIFF results before downstream processing

IMAGE QUALITY:
• Use a first scan as the quality check
• Adjust brightness if needed
• Use automatic color detection
• Ensure no skew
• Check focus quality

TROUBLESHOOTING:
• Scanner not detected: Check backend availability, drivers, and network reachability
• AirScan fallback needed: Provide direct device IP/URL when discovery is incomplete
• Poor quality: Adjust DPI, mode, brightness, or source placement
• TWAIN unavailable: Confirm a compatible DSM/source exists for the current Python/runtime architecture
• Linux SANE issues: Treat AirScan as the preferred path when native SANE remains incomplete
'''
    },

    'MyReader': {
        'title': 'Document Reader (MyReader)',
        'icon': '📖',
        'description': '''Document Reader and Page Navigator

MyReader provides reading and navigation of multi-page documents with
OCR integration for text extraction and search.

FEATURES:
• Multi-page document navigation
• Full-text search
• OCR text overlay
• Page annotations
• Bookmark management
• Export functionality

PRIMARY WORKFLOW:
1. Open document
2. Navigate pages
3. Search text
4. View OCR results
5. Export or annotate

KEY SHORTCUTS:
• Ctrl+F: Find text
• Page Up/Down: Navigate
• Ctrl+Home: First page
• Ctrl+End: Last page
• Ctrl+G: Go to page

TOOLBAR:
• Open/Save buttons
• Navigation controls
• Search bar
• Zoom controls
• Export button

USES IN PIPELINE:
• Review OCR results
• Validate document reading
• Search document content
• Extract text and data

See also: MyScanner, MyBoxer, MyTrainer
''',
        'usage': '''READER USAGE GUIDE

OPENING DOCUMENTS:
1. File > Open or Ctrl+O
2. Select document file
3. Document loads automatically
4. First page displays

NAVIGATION:
• Page slider: Drag to jump
• Next/Previous buttons: Single page
• Goto: Enter page number
• Bookmarks: Quick jump to marked pages

SEARCHING TEXT:
1. Ctrl+F to open search
2. Type search term
3. Press Enter or click Find
4. Results highlight in text
5. Use Next/Previous buttons
6. ESC to close search

OCR TEXT OVERLAY:
• View > Show OCR Text
• Transparent overlay shows recognized text
• Click text to view full OCR result
• Adjust transparency with slider

ANNOTATIONS:
1. Tools > Annotate
2. Select drawing tool
3. Draw on page
4. Save annotations with document

BOOKMARKS:
1. Page > Bookmark
2. Go to bookmarked pages via menu
3. Bookmark bar shows marked pages
4. Delete bookmarks as needed

EXPORTING:
1. File > Export
2. Choose export type:
   - Page image
   - OCR text
   - Entire document
3. Set options
4. Confirm export

TEXT SELECTION:
• Click and drag to select
• Ctrl+A for all text
• Ctrl+C to copy
• Paste into other apps

VIEWING OPTIONS:
• View > Zoom: Adjust size
• View > Fit Page: Full page view
• View > Fit Width: Text readable
• View > Continuous: Scroll through pages
'''
    },

    'MyTrainer': {
        'title': 'Tesseract Trainer (MyTrainer)',
        'icon': '🧠',
        'description': '''Tesseract OCR Model Trainer

MyTrainer manages the training of Tesseract OCR models using ground truth data.
It creates custom language models for optimized character recognition.

FEATURES:
• Training data validation
• Model compilation
• Accuracy evaluation
• Batch training
• Model export
• Performance metrics

PRIMARY WORKFLOW:
1. Validate ground truth data
2. Configure training parameters
3. Start training process
4. Monitor training progress
5. Evaluate results
6. Export trained model

KEY PARAMETERS:
• Learning rate: 0.0001-0.01
• Batch size: 32-256
• Epochs: 10-100
• Validation split: 10-20%
• Language: Greek, Latin, etc.

OUTPUT:
• Trained .traineddata file
• Performance metrics
• Confusion matrix
• Accuracy per character

USES IN PIPELINE:
• Creates custom OCR models
• Improves character recognition
• Adapts to specific fonts
• Enables language-specific optimization

See also: MyBoxer, MyGrounder
''',
        'usage': '''TRAINER USAGE GUIDE

PREPARATION:
1. Ensure ground truth data ready
2. Validate all .box files
3. Check image quality
4. Verify character coverage
5. Prepare test set

STARTING TRAINING:
1. File > Load Training Data
2. Select ground truth folder
3. Configure trainer settings
4. Click Train

TRAINER SETTINGS:
• Learning rate: Lower = slower but better
• Batch size: Larger = faster but needs more RAM
• Epochs: More = better accuracy but longer
• Validation: Reserve some data for testing
• Language: Select training language

MONITORING TRAINING:
• Progress bar shows completion
• Loss graph shows improvement
• Validation accuracy updates
• Time estimate shown
• Can pause/resume training

TRAINING BEST PRACTICES:
• Start with good ground truth data
• Balance character distribution
• Include enough samples (100+ per character)
• Test with validation set regularly
• Use GPU if available

EVALUATION:
1. Training > Evaluate Model
2. Select test image set
3. Run evaluation
4. Review results:
   - Overall accuracy
   - Per-character accuracy
   - Confusion matrix
   - Error analysis

EXPORTING MODEL:
1. Training > Export Model
2. Choose output location
3. Set model name
4. Export complete

TROUBLESHOOTING:
• Training too slow: Reduce image resolution
• Out of memory: Reduce batch size
• Poor accuracy: Improve ground truth data
• Stuck training: Check for corrupted data

PERFORMANCE OPTIMIZATION:
• Use GPU acceleration if available
• Reduce image size for faster training
• Increase batch size for parallelization
• Monitor RAM usage
'''
    },

    'MyWriter': {
        'title': 'Text Writer (MyWriter)',
        'icon': '✍️',
        'description': '''Text Document Writer and Editor

MyWriter is a specialized text editor for preparing, editing, and organizing
OCR output and training text data.

FEATURES:
• Full text editing
• Syntax highlighting
• Text validation
• Format conversion
• Spell checking
• Batch find/replace

PRIMARY WORKFLOW:
1. Create or open text document
2. Edit content
3. Validate text
4. Export in desired format
5. Archive or process further

KEY SHORTCUTS:
• Ctrl+N: New document
• Ctrl+O: Open file
• Ctrl+S: Save file
• Ctrl+H: Find & Replace
• Ctrl+Z: Undo
• Ctrl+Y: Redo

TOOLBAR:
• New/Open/Save buttons
• Text formatting
• Font selection
• Size adjustment

USES IN PIPELINE:
• Edit OCR output
• Prepare training text
• Format text data
• Validate text content

See also: MyLexer, MyVersifier
''',
        'usage': '''WRITER USAGE GUIDE

CREATING DOCUMENTS:
1. File > New or Ctrl+N
2. Start typing
3. Document auto-saves periodically

OPENING FILES:
1. File > Open or Ctrl+O
2. Select text file
3. File opens in editor

EDITING TEXT:
• Standard text editor commands
• Ctrl+A: Select all
• Ctrl+X: Cut
• Ctrl+C: Copy
• Ctrl+V: Paste
• Ctrl+Z: Undo
• Ctrl+Y: Redo

FINDING AND REPLACING:
1. Ctrl+H for Find & Replace
2. Enter search term
3. Enter replacement text
4. Choose Find or Replace All
5. Close dialog when done

FORMATTING:
• Select text to format
• Bold: Ctrl+B
• Italic: Ctrl+I
• Underline: Ctrl+U
• Font menu: Change typeface
• Size menu: Adjust size

TEXT VALIDATION:
1. Tools > Validate
2. Checks for:
   - Spelling errors
   - Format issues
   - Encoding problems
3. Fix errors as needed

SAVING:
1. Ctrl+S or File > Save
2. Choose save location
3. Select format:
   - Plain text (.txt)
   - Rich text (.rtf)
   - HTML (.html)
4. Confirm save

PRINTING:
1. Ctrl+P or File > Print
2. Configure printer
3. Set page ranges
4. Click Print

STATISTICS:
• Tools > Statistics
• Shows:
  - Character count
  - Word count
  - Line count
  - Average word length
'''
    },

    'MyVersifier': {
        'title': 'Text Versifier (MyVersifier)',
        'icon': '📄',
        'description': '''Verse and Section Verifier

MyVersifier manages verification and organization of text into proper verse structures,
chapters, and sections, particularly for biblical and classical texts.

FEATURES:
• Verse structure validation
• Chapter organization
• Reference resolution
• Cross-reference checking
• Verse numbering
• Format standardization

PRIMARY WORKFLOW:
1. Load text document
2. Parse verse structure
3. Validate references
4. Correct errors
5. Export verified text

KEY SHORTCUTS:
• Ctrl+V: Verify current verse
• Ctrl+N: Next verse
• Ctrl+P: Previous verse
• Ctrl+G: Go to verse

USES IN PIPELINE:
• Validates OCR output structure
• Ensures proper verse formatting
• Checks reference validity
• Organizes text hierarchically

See also: MyWriter, MyResolver
''',
        'usage': '''VERSIFIER USAGE GUIDE

LOADING TEXT:
1. File > Open or Ctrl+O
2. Select text document
3. Choose verse format (e.g., Greek Bible)
4. Parser analyzes structure

VERSE VALIDATION:
• Automatic detection of verse markers
• Verification of verse numbering
• Check for missing verses
• Identify duplicate verses

VIEWING VERSES:
1. Navigate with Next/Previous buttons
2. Current verse highlighted
3. Chapter and section shown
4. Reference path displayed

EDITING VERSES:
1. Select verse to edit
2. Modify verse number/content
3. Update references
4. Save changes

CROSS-REFERENCES:
1. Tools > Cross-Reference Check
2. Validates all internal references
3. Reports broken links
4. Fix automatically or manually

EXPORTING:
1. File > Export
2. Choose output format:
   - Structured JSON
   - CSV with verse data
   - XML for interchange
3. Set options
4. Export complete

TROUBLESHOOTING:
• Wrong verse format: Check parser settings
• Missing verses: Run validation
• Broken references: Use auto-fix
'''
    },

    'MyResolver': {
        'title': 'Variant Resolver (MyResolver)',
        'icon': '🔄',
        'description': '''Text Variant and Error Resolver

MyResolver handles identification, resolution, and correction of OCR errors,
variant spellings, and textual inconsistencies in recognized text.

FEATURES:
• Automatic error detection
• Variant grouping
• Similarity matching
• Batch correction
• Dictionary-based resolution
• Manual override capability

PRIMARY WORKFLOW:
1. Load OCR output text
2. Detect variants and errors
3. Group similar variants
4. Apply corrections
5. Export corrected text

KEY SHORTCUTS:
• Ctrl+F: Find variant
• Ctrl+R: Resolve variant
• Ctrl+A: Accept correction
• Ctrl+D: Dictionary lookup

USES IN PIPELINE:
• Fixes OCR recognition errors
• Resolves spelling variants
• Standardizes text format
• Final quality improvement step

See also: MyVersifier, MyWriter
''',
        'usage': '''RESOLVER USAGE GUIDE

LOADING TEXT:
1. File > Open OCR Output
2. Select text file
3. Choose language
4. Analysis begins automatically

VARIANT DETECTION:
• System identifies potential errors
• Lists similar word variants
• Suggests corrections
• Shows confidence scores

REVIEWING VARIANTS:
1. List shows all potential issues
2. Click variant to see details
3. Original text highlighted
4. Suggestions shown below

RESOLVING VARIANTS:
For each variant:
1. Accept suggestion (A)
2. Reject (R)
3. Choose different suggestion
4. Edit manually
5. Add to dictionary

BATCH CORRECTION:
1. Tools > Batch Resolve
2. Apply same resolution to all instances
3. Verify changes
4. Confirm corrections

DICTIONARY MANAGEMENT:
1. Tools > Manage Dictionary
2. Add known words/terms
3. Set custom corrections
4. Import/export dictionaries

EXPORTING RESULTS:
1. File > Export
2. Choose format
3. Select options:
   - Include correction history
   - Show confidence scores
   - Comparison view
4. Export complete

QUALITY ASSURANCE:
• Tools > Review Changes
• Shows all corrections applied
• Verify accuracy
• Revert if needed
'''
    },

    'MyExplorer': {
        'title': 'File Explorer (MyExplorer)',
        'icon': '📁',
        'description': '''Project File Browser and Manager

MyExplorer provides file and folder navigation for the BiblionOCR project,
with integrated project organization and batch operations.

FEATURES:
• Directory tree navigation
• File preview
• Batch file operations
• Search functionality
• Drag-and-drop support
• Project organization

PRIMARY WORKFLOW:
1. Browse project folders
2. Select files to process
3. Execute batch operations
4. Organize project structure
5. Archive or clean up

KEY SHORTCUTS:
• Ctrl+F: Find file
• F5: Refresh
• Delete: Delete file
• Ctrl+X: Cut
• Ctrl+C: Copy
• Ctrl+V: Paste

TOOLBAR:
• Navigation buttons
• Search bar
• View options
• New folder button

USES IN PIPELINE:
• File organization
• Batch processing launcher
• Project structure management
• Quick access to resources

See also: MyScanner, MyPixler
''',
        'usage': '''EXPLORER USAGE GUIDE

NAVIGATION:
1. Folder tree on left shows structure
2. Main panel shows folder contents
3. Double-click folder to open
4. Up button goes to parent

VIEWING FILES:
• List view: Detailed file info
• Icon view: Thumbnails
• Compact view: Minimal display
• Change via View menu

SEARCHING:
1. Ctrl+F opens search
2. Enter filename or pattern
3. Results show matching files
4. Click to open/select

SELECTING FILES:
• Click: Select single file
• Ctrl+Click: Multiple files
• Ctrl+A: Select all
• Shift+Click: Range select

BATCH OPERATIONS:
1. Select files to process
2. Right-click context menu
3. Choose operation:
   - Copy to folder
   - Move to folder
   - Delete files
   - Change permissions
   - Launch tool on files

DRAG AND DROP:
• Drag files between folders
• Drop on applications
• Drag to external tools

CREATING STRUCTURE:
1. Right-click in folder
2. New > Folder
3. Enter folder name
4. Create complete

ARCHIVING:
1. Select files/folders
2. Right-click > Archive
3. Choose format (zip, tar)
4. Set output location
5. Create archive

PROJECT TEMPLATES:
• Tools > Create Project Template
• Save folder structure
• Reuse for new projects
'''
    },

    'MyServer': {
        'title': 'OCR Processing Server (MyServer)',
        'icon': '🖥️',
        'description': '''OCR Processing Server and Batch Orchestration

    MyServer is the main runtime coordinator for BiblionOCR.
    It is not a network server or web API. It wires project creation, scanning,
    image loading, OCR-adjacent workflows, and developer-mode entry points.

FEATURES:
    • Project creation and project-opening workflows
    • Shared scanner workflow integration
    • PDF/TIFF extraction and conversion dialogs
    • Launch points into downstream modules such as MyPixler and MyScanner
    • Session-backed path and workflow restore
    • Developer menu entry for Runtime Inspector / Developer Services

PRIMARY WORKFLOW:
1. Open MyServer
    2. Create or open a project
    3. Load or acquire source material
    4. Route work into the appropriate module or dialog
    5. Continue through the OCR and review pipeline

KEY FUNCTIONS:
    • Create projects from the managed project structure
    • Open project folders rooted under the user Projects directory
    • Launch and coordinate scanner acquisition workflows
    • Open images directly into MyPixler when editing is required
    • Persist session state rather than rewriting ad hoc local settings

CONFIGURATION:
    • Active project path
    • Session-backed image and scanner state
    • Project creation inputs and provenance metadata
    • Shared workflow font and UI startup state
    • Developer-mode observation visibility

USES IN PIPELINE:
    • Main runtime entry point
    • Project creation and routing surface
    • Scan orchestration and preprocessing entry point
    • Developer-mode hosting surface

    CURRENT NOTES:
    • Project creation logic is moving into the Core engine rather than staying in UI code.
    • MyServer and MyScanner share the same scanner workflow services.
    • The Runtime Inspector is available through the Developer menu when enabled.
    • Current repo policy and contribution guidance live in CONTRIBUTING.md and CONTENT_POLICY.md.

    See also: MyScanner, MyPixler, MyWriter, Developer Services
''',
        'usage': '''APPLICATION USAGE

STARTING MYSERVER:
    1. Run MyServer.py from terminal or launch from the project UI
2. Open the MyServer interface
    3. Choose whether to create a project, open a project, scan, or load an image
    4. Configure the selected workflow
    5. Continue into the downstream module or dialog

    PROJECT CREATION:
    1. Start the new-project workflow
    2. Review the normalized project name and provenance fields
    3. Import RIS or other metadata only when useful
    4. Confirm project creation into the user Projects area

    SCANNING AND IMAGE INTAKE:
    1. Start the shared scan workflow when acquiring new images
    2. Use flatbed scanning locally in MyServer
    3. Allow feeder/ADF-oriented handoff into MyScanner when prompted
    4. Review the saved TIFF result and continue processing

    MODULE ROUTING:
    1. Use MyPixler for image editing and review
    2. Use MyScanner for scanner-focused acquisition sessions
    3. Use downstream OCR and text tools after acquisition/preprocessing is complete

    DEVELOPER MODE:
    1. Open the Developer menu when available
    2. Launch Runtime Inspector to observe module state and recent events
    3. Use documentation-first references for architecture and workflow context:
       - docs/README.md
       - docs/development/DEV_NOTEBOOK.md
       - docs/development/QUICK_REFERENCE.md
'''
    },

    'MyLexer': {
        'title': 'Lexicon and Dictionary Tool (MyLexer)',
        'icon': '📚',
        'description': '''Lexicon and Dictionary Management

MyLexer manages lexicon data, dictionary building, and vocabulary organization
for language-specific OCR processing and text analysis.

FEATURES:
• Dictionary creation and editing
• Word frequency analysis
• Vocabulary statistics
• Dictionary export/import
• Language-specific organization
• Custom entry management

PRIMARY WORKFLOW:
1. Load or create dictionary
2. Add/edit lexicon entries
3. Analyze word frequency
4. Export dictionary
5. Use in OCR pipeline

USES IN PIPELINE:
• Improves OCR accuracy
• Provides language context
• Enables spell checking
• Supports variant resolution

See also: MyWriter, MyResolver
''',
        'usage': '''LEXICON MANAGEMENT GUIDE

CREATING DICTIONARY:
1. File > New Dictionary
2. Choose language
3. Configure dictionary options
4. Save dictionary file

ADDING ENTRIES:
1. Click Add Entry
2. Enter word/phrase
3. Add definition/translation
4. Set frequency if known
5. Confirm entry

IMPORTING LISTS:
1. File > Import
2. Select word list file
3. Choose format (txt, csv)
4. Map columns if needed
5. Import words

FREQUENCY ANALYSIS:
1. Tools > Analyze Text
2. Select text file
3. Analyze creates frequency list
4. Most common words shown
5. Export results

DICTIONARY EXPORT:
1. File > Export
2. Choose format:
   - Plain text
   - CSV
   - JSON
3. Set output location
4. Export complete

DICTIONARY STATISTICS:
• Tools > Statistics
• Shows:
  - Total entries
  - Entry types
  - Frequency distribution
  - Language coverage

SEARCHING DICTIONARY:
1. Use search bar
2. Find entries by:
   - Word
   - Definition
   - Frequency
3. Click to view/edit

See full tutorial in Help > Tutorials
'''
    }
}

# ============================================================================
# HELP DIALOG IMPLEMENTATION
# ============================================================================

class HelpDialog(QDialog):
    """
    Main help dialog for displaying program documentation.
    
    Usage:
        dialog = HelpDialog(parent, program_name)
        dialog.exec_()
    """
    
    def __init__(self, parent=None, program_name='MyBoxer'):
        super().__init__(parent)
        self.program_name = program_name
        self.help_data = PROGRAM_HELP.get(program_name, {})
        
        self.setWindowTitle(f'{self.help_data.get("title", program_name)} - Help')
        self.setGeometry(100, 100, 900, 700)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.help_data.get('title', self.program_name))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Tabs for different sections
        tabs = QTabWidget()
        
        # Description tab
        desc_widget = QTextEdit()
        desc_widget.setText(self.help_data.get('description', 'No description available.'))
        desc_widget.setReadOnly(True)
        tabs.addTab(desc_widget, '📖 Overview')
        
        # Usage tab
        if 'usage' in self.help_data:
            usage_widget = QTextEdit()
            usage_widget.setText(self.help_data['usage'])
            usage_widget.setReadOnly(True)
            tabs.addTab(usage_widget, '🎯 Usage Guide')
        
        # Development tab
        if 'development' in self.help_data:
            dev_widget = QTextEdit()
            dev_widget.setText(self.help_data['development'])
            dev_widget.setReadOnly(True)
            tabs.addTab(dev_widget, '🔧 Development')
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def show_help(parent=None, program_name='MyBoxer'):
    """
    Show help dialog for a program.
    
    Usage:
        show_help(self, 'MyBoxer')
    """
    dialog = HelpDialog(parent, program_name)
    dialog.exec_()


def add_help_menu(window, program_name):
    """
    Add a Help menu to a window.
    
    Usage:
        add_help_menu(self, 'MyBoxer')
    """
    help_menu = window.menuBar().addMenu('Help')
    
    # Help action
    help_action = help_menu.addAction('Program Help')
    help_action.setShortcut('F1')
    help_action.triggered.connect(lambda: show_help(window, program_name))
    
    # About action
    about_action = help_menu.addAction('About')
    about_action.triggered.connect(lambda: show_about(window, program_name))
    
    return help_menu


def show_about(parent=None, program_name='MyBoxer'):
    """Show about dialog with program information."""
    help_data = PROGRAM_HELP.get(program_name, {})
    title = help_data.get('title', program_name)
    
    about_text = f"""
<h2>{title}</h2>
<p>Part of the BiblionOCR Project</p>
<p>A comprehensive OCR system for document digitization and text extraction.</p>

<h3>Project Information:</h3>
<ul>
<li>Version: 1.0</li>
<li>License: See LICENSE file</li>
<li>Author: BiblionOCR Team</li>
<li>Architecture: See docs/architecture/PROJECT_ARCHITECTURE.md</li>
</ul>

<h3>Current Reference Surface:</h3>
<ul>
<li>Documentation root: docs/README.md</li>
<li>Developer notebook: docs/development/DEV_NOTEBOOK.md</li>
<li>Quick reference: docs/development/QUICK_REFERENCE.md</li>
<li>Contribution policy: CONTRIBUTING.md</li>
<li>Content rights policy: CONTENT_POLICY.md</li>
</ul>

<h3>Key Technologies:</h3>
<ul>
<li>PyQt5 - User Interface</li>
<li>Tesseract - OCR Engine</li>
<li>OpenCV - Image Processing</li>
<li>SQLite - Data Storage</li>
</ul>

<h3>Getting Help:</h3>
<p>Press F1 in any program for detailed help.
See docs/architecture/PROJECT_ARCHITECTURE.md for system overview.
See docs/development/QUICK_REFERENCE.md for quick lookup.</p>
"""
    
    from PyQt5.QtWidgets import QMessageBox
    QMessageBox.about(parent, f'About {title}', about_text)


def get_program_list():
    """Return list of all available programs with help."""
    return list(PROGRAM_HELP.keys())


def get_program_description(program_name):
    """Get brief description of a program."""
    return PROGRAM_HELP.get(program_name, {}).get('description', 'No description available.')


# ============================================================================
# INTEGRATION TEMPLATE
# ============================================================================

"""
To integrate help into your programs, add this to your main window class:

    def __init__(self, parent=None):
        super().__init__(parent)
        # ... your other initialization code ...
        
        # Add help menu (must be done after menuBar() is created)
        from HelpSystem import add_help_menu
        add_help_menu(self, 'MyBoxer')  # Replace 'MyBoxer' with your program name

Or manually add to existing Help menu:

    def show_help(self):
        from HelpSystem import show_help
        show_help(self, 'MyBoxer')  # Replace 'MyBoxer' with your program name

Then add a menu action:
    help_action = help_menu.addAction('Program Help')
    help_action.setShortcut('F1')
    help_action.triggered.connect(self.show_help)
"""

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Show help for MyBoxer as example
    show_help(None, 'MyBoxer')
    
    sys.exit(app.exec_())
