# BiblionOCR Help System

## Overview

The BiblionOCR Help System provides comprehensive, integrated documentation for all programs in the BiblionOCR project. Users can access help through an easy-to-use menu system within each program.

## Files

- **HelpSystem.py** - Main help module with all program documentation
- **HELP_INTEGRATION_GUIDE.md** - Guide for adding help to programs
- **This README**

## Features

✅ **12 Programs Documented** - MyBoxer, MyPixler, MyGlypher, MyGrounder, MyScanner, MyReader, MyTrainer, MyWriter, MyVersifier, MyResolver, MyExplorer, MyServer

✅ **Three-Level Documentation**
- Overview: High-level program description and features
- Usage Guide: Detailed step-by-step instructions
- Development Notes: Technical information for developers

✅ **Easy Integration** - Just 2 lines of code to add help to any program

✅ **F1 Keyboard Shortcut** - Standard help access across all programs

✅ **About Dialog** - Program information and technology stack

✅ **Tabbed Interface** - Organized information in readable format

✅ **Release Workflow Coverage** - Documentation now reflects the cross-platform font refresh path used for release builds and Tesseract retraining updates

## Quick Start

### For End Users

1. **Open any BiblionOCR program**
2. **Press F1** or go to **Help > Program Help**
3. **Read the relevant tab:**
   - 📖 Overview - What the program does
   - 🎯 Usage Guide - How to use it
   - 🔧 Development - Technical details

### For Developers

To add help to your program:

```python
from HelpSystem import add_help_menu

class MyBoxer(MyBoxerUI.Ui_Boxer, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Add this ONE line:
        add_help_menu(self, 'MyBoxer')
```

That's it! Now your program has:
- Help menu with program help and about dialog
- F1 keyboard shortcut for instant help
- Full documentation for users and developers

## Documentation Structure

Each program has documentation organized in three sections:

### 📖 Overview
- Program title and icon
- Brief description
- Key features
- Primary workflow
- Uses in OCR pipeline

### 🎯 Usage Guide
- Step-by-step instructions
- Keyboard shortcuts
- Toolbar buttons explained
- Common tasks
- Troubleshooting
- Tips and best practices

### 🔧 Development
- Source code structure
- Key classes and methods
- Architecture patterns
- Database schema
- Dependencies
- Extension points
- Testing notes

## Program Reference

| Program | Purpose |
|---------|---------|
| **MyBoxer** | Create and edit character bounding boxes |
| **MyPixler** | View and process images |
| **MyGlypher** | Edit character glyphs |
| **MyGrounder** | Generate ground truth data |
| **MyScanner** | Integrate with document scanners |
| **MyReader** | Read and navigate documents |
| **MyTrainer** | Train Tesseract OCR models |
| **MyWriter** | Edit text documents |
| **MyVersifier** | Verify verse structure |
| **MyResolver** | Resolve text variants |
| **MyExplorer** | Browse project files |
| **MyServer** | Batch processing and OCR workflow orchestration |
| **MyLexer** | Manage dictionaries |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **F1** | Open program help |
| **Ctrl+H** | Find and replace (in help text) |
| **Ctrl+F** | Search help text |
| **Escape** | Close help dialog |

## Customization

### Adding Help for a New Program

1. Edit **HelpSystem.py**
2. Find the `PROGRAM_HELP` dictionary
3. Add your program:

```python
'MyNewProgram': {
    'title': 'Program Title',
    'icon': '🔧',
    'description': '''Overview of what program does...''',
    'usage': '''Step-by-step usage instructions...''',
    'development': '''Technical development notes...'''
}
```

4. In your program's `__init__`, add:
```python
add_help_menu(self, 'MyNewProgram')
```

### Customizing Help Dialog

Create a subclass of `HelpDialog` in HelpSystem.py:

```python
class MyCustomDialog(HelpDialog):
    def init_ui(self):
        super().init_ui()
        # Add custom UI elements
```

### Adding Help Button to Toolbar

Use the provided `setup_help_button()` function:

```python
from HelpSystem import setup_help_button

setup_help_button(self, self.toolbar, 'MyBoxer')
```

## Integration Methods

### Method 1: Full Integration (Recommended)
```python
from HelpSystem import add_help_menu

# In __init__, call:
add_help_menu(self, 'MyBoxer')
```
✅ Provides: Help menu, About dialog, F1 shortcut

### Method 2: Manual Menu
```python
from HelpSystem import show_help

# Create menu action manually
help_action = help_menu.addAction('Program Help')
help_action.setShortcut('F1')
help_action.triggered.connect(
    lambda: show_help(self, 'MyBoxer')
)
```

### Method 3: Button Only
```python
from HelpSystem import show_help
from PyQt5.QtWidgets import QPushButton

help_btn = QPushButton('Help')
help_btn.clicked.connect(lambda: show_help(self, 'MyBoxer'))
```

## Accessing Help Programmatically

```python
from HelpSystem import (
    get_program_list,           # Get all documented programs
    get_program_description,    # Get brief description
    show_help,                  # Show help dialog
    HelpDialog                  # Create custom dialog
)

# List all programs
programs = get_program_list()

# Get description
desc = get_program_description('MyBoxer')

# Show help
show_help(parent_window, 'MyBoxer')

# Create custom dialog
dialog = HelpDialog(parent_window, 'MyPixler')
dialog.exec_()
```

## Related Documentation

- **PROJECT_ARCHITECTURE.md** - Complete system architecture
- **DESIGN_SPECIFICATION.md** - Domain vocabulary and design boundaries
- **QUICK_REFERENCE.md** - Quick lookup for all programs
- **DEPENDENCIES_AND_RELATIONSHIPS.md** - Program dependencies
- **dev_notebook.md** - Current release workflow and stabilization notes

These files were created by the Explore agent and provide comprehensive project documentation.

## Workflow Integration

The help system fits into the user experience like this:

```
User opens program
    ↓
Sees Help menu in menu bar
    ↓
Can press F1 for instant help
    ↓
Help dialog opens with tabs
    ↓
User reads Overview/Usage/Development
    ↓
Learns how to use program
    ↓
Clicks "About" for program info
```

## Best Practices

1. **Press F1 First** - When stuck, F1 is fastest
2. **Check Usage Guide** - For step-by-step instructions
3. **Review Overview** - Before starting new task
4. **Consult Development** - When extending code
5. **Use Related Docs** - For system-wide perspective

## Support

If help text needs updating:

1. Edit HelpSystem.py
2. Find program in PROGRAM_HELP dictionary
3. Update 'description', 'usage', or 'development'
4. Save and test with F1

For release-related changes, also refresh the font installation path and keep MyTrainer aligned with the final compiled release workflow.

For major documentation, also update:
- PROJECT_ARCHITECTURE.md
- QUICK_REFERENCE.md
- DEPENDENCIES_AND_RELATIONSHIPS.md

## Testing

Test the help system:

```bash
# From terminal
python HelpSystem.py

# Or in your program:
# Press F1
# Verify all tabs load
# Check text displays properly
# Click About button
```

## Version

- **Help System Version**: 1.0
- **Programs Documented**: 12
- **Last Updated**: 2026-05-04

## Compatibility

- **Python**: 3.7+
- **PyQt5**: 5.12+
- **Required Modules**: PyQt5.QtWidgets, PyQt5.QtCore

## Authors

- BiblionOCR Development Team
- Help System: GitHub Copilot

## License

See LICENSE file in project root.

---

**Ready to use!** Just add `add_help_menu(self, 'ProgramName')` to any program.
