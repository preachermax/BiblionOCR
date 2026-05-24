"""
INTEGRATION GUIDE: Adding Help System to BiblionOCR Programs
=============================================================

This document shows how to integrate the HelpSystem.py help module into
your PyQt5 applications. Examples are provided for different scenarios.

"""

# ============================================================================
# EXAMPLE 1: Basic Integration (Add Help Menu to Existing Program)
# ============================================================================

"""
To add help to an existing program like MyBoxer.py:

STEP 1: Import the help system
"""

from HelpSystem import add_help_menu, show_help

"""
STEP 2: In your main window __init__, call add_help_menu:
"""

# Inside your MyBoxer.__init__() method, add this line AFTER setupUi():
# Example (in MyBoxer.py):

class MyBoxer(MyBoxerUI.Ui_Boxer, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        
        # ... your other initialization code ...
        
        # ADD THIS LINE to enable help system:
        add_help_menu(self, 'MyBoxer')
        
        # Now users can:
        # - Press F1 for help
        # - Use Help menu > Program Help
        # - Use Help menu > About


# ============================================================================
# EXAMPLE 2: Minimal Help Button Integration
# ============================================================================

"""
If you just want a help button without a full menu, use:
"""

from PyQt5.QtWidgets import QPushButton
from HelpSystem import show_help

class MyPixler(MyPixlerUI.Ui_Pixler, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        
        # Create help button in toolbar
        help_button = QPushButton('Help (F1)')
        help_button.clicked.connect(self.show_help)
        self.toolbar.addWidget(help_button)
        
    def show_help(self):
        show_help(self, 'MyPixler')


# ============================================================================
# EXAMPLE 3: Custom Help Button in Toolbar
# ============================================================================

"""
For a more polished look, add help button to your toolbar:
"""

def setup_help_button(self, toolbar, program_name):
    """
    Add a help button to the toolbar.
    
    Args:
        self: Your main window instance
        toolbar: QToolBar instance
        program_name: Program name (e.g., 'MyGlypher')
    """
    from HelpSystem import show_help
    from PyQt5.QtWidgets import QAction
    from PyQt5.QtGui import QIcon
    
    # Create help action
    help_action = QAction('Help', self)
    help_action.setShortcut('F1')
    help_action.setStatusTip('Show program help')
    help_action.triggered.connect(lambda: show_help(self, program_name))
    
    # Add to toolbar
    toolbar.addSeparator()
    toolbar.addAction(help_action)


# ============================================================================
# EXAMPLE 4: Keyboard Shortcut Only (No Menu)
# ============================================================================

"""
If you only want F1 to open help, without menu integration:
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from HelpSystem import show_help

class MyGrounder(MyGrounderUI.Ui_Grounder, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        
    def keyPressEvent(self, event):
        """Override to capture F1 key."""
        if event.key() == Qt.Key_F1:
            show_help(self, 'MyGrounder')
        else:
            super().keyPressEvent(event)


# ============================================================================
# EXAMPLE 5: Context-Sensitive Help
# ============================================================================

"""
For more advanced help, you can provide context-sensitive help
by modifying HelpSystem.py to include section markers:
"""

class MyScanner(MyScannerUI.Ui_Scanner, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        
        # Connect various buttons to contextual help
        self.connect_help_buttons()
        
    def connect_help_buttons(self):
        """Connect buttons to show relevant help sections."""
        from HelpSystem import show_help
        
        # Help buttons for specific features
        self.scan_button.setWhatsThis('Click to start scanning. See Help for scanner setup.')
        self.settings_button.setWhatsThis('Configure scanner settings here.')
        
        # Show help when "What's This?" is triggered
        self.scan_button.clicked.connect(
            lambda: self.show_contextual_help('Scanning')
        )
    
    def show_contextual_help(self, section):
        """Show help for specific section."""
        from HelpSystem import show_help
        dialog = show_help(self, 'MyScanner')
        # Could be enhanced to jump to specific section


# ============================================================================
# IMPLEMENTATION CHECKLIST
# ============================================================================

"""
To add help to any program, follow these steps:

□ Step 1: Import HelpSystem
  from HelpSystem import add_help_menu, show_help

□ Step 2: Call in __init__
  add_help_menu(self, 'ProgramName')  # Use your program name

□ Step 3: Test
  Run program and press F1 or click Help menu

□ Step 4: (Optional) Add help button to toolbar
  Use setup_help_button() or create custom button

□ Step 5: (Optional) Add program to HelpSystem.py if not already there

□ Step 6: Update documentation as needed


PROGRAMS TO ADD HELP TO:
□ MyBoxer
□ MyPixler
□ MyGlypher
□ MyGrounder
□ MyScanner
□ MyReader
□ MyTrainer
□ MyWriter
□ MyVersifier
□ MyResolver
□ MyExplorer
□ MyServer
□ MyLexer

"""


# ============================================================================
# QUICK COPY-PASTE INTEGRATION
# ============================================================================

"""
MINIMAL CODE TO ADD TO YOUR PROGRAM'S __init__:

    from HelpSystem import add_help_menu
    add_help_menu(self, 'MyBoxer')  # Replace 'MyBoxer' with your program name

That's it! Now F1 and Help menu will work.

"""


# ============================================================================
# EXTENDING HELP SYSTEM
# ============================================================================

"""
To add help for a NEW program not in HelpSystem.py:

1. Edit HelpSystem.py
2. Find the PROGRAM_HELP dictionary
3. Add your program entry:

    'MyNewProgram': {
        'title': 'Program Title',
        'icon': '🔧',
        'description': '''Brief description...''',
        'usage': '''Detailed usage guide...''',
        'development': '''Development notes...'''
    }

4. Save HelpSystem.py
5. Add help to your program using standard integration above

"""


# ============================================================================
# CUSTOMIZING HELP DIALOG
# ============================================================================

"""
If you want a custom help appearance, you can subclass HelpDialog:
"""

from HelpSystem import HelpDialog
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtGui import QFont

class CustomHelpDialog(HelpDialog):
    """Custom help dialog with additional features."""
    
    def init_ui(self):
        """Override to customize appearance."""
        super().init_ui()
        
        # Add custom footer
        footer = QLabel(
            'Need more help? See PROJECT_ARCHITECTURE.md in the project folder'
        )
        font = QFont()
        font.setItalic(True)
        footer.setFont(font)
        
        # Add to bottom
        self.layout().insertWidget(self.layout().count() - 1, footer)


# ============================================================================
# TESTING
# ============================================================================

"""
To test the help system:

1. From command line:
   python HelpSystem.py

2. In your program:
   - Press F1
   - Click Help menu
   - All tabs should load
   - Text should be readable

3. Verify for all programs:
   - Check all programs in PROGRAM_HELP dict
   - Run help dialog for each
   - Verify text displays correctly

"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
ISSUE: Help menu doesn't appear
SOLUTION: Ensure add_help_menu() is called AFTER setupUi()

ISSUE: F1 doesn't work
SOLUTION: Check that you called add_help_menu() with correct program name

ISSUE: Help text cut off
SOLUTION: Resize help dialog window or check text wrapping

ISSUE: Import error for HelpSystem
SOLUTION: Ensure HelpSystem.py is in same directory as your program,
          or add to PYTHONPATH

ISSUE: Program not in help database
SOLUTION: Add entry to PROGRAM_HELP dict in HelpSystem.py

"""

if __name__ == '__main__':
    print("This is an integration guide file.")
    print("See the examples above for how to add help to your programs.")
    print("\nQuick start:")
    print("  from HelpSystem import add_help_menu")
    print("  add_help_menu(self, 'MyBoxer')")
