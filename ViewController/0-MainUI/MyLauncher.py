#print(len(locals()))

# Python imports
import importlib.util
import sys
import os
import subprocess
#import glob
import json
import re

script_dir = os.path.dirname(os.path.realpath(__file__))
helpers_dir = os.path.join(script_dir, "helpers")
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
viewcontroller_dir = os.path.join(project_root, "ViewController")
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if helpers_dir not in sys.path:
    sys.path.insert(0, helpers_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

RUNTIME_MODULE_PATHS = {
    "MyLauncher.py": os.path.join(script_dir, "MyLauncher.py"),
    "MyServer.py": os.path.join(script_dir, "MyServer.py"),
    "MyScanner.py": os.path.join(script_dir, "MyScanner.py"),
    "MyExplorer.py": os.path.join(script_dir, "MyExplorer.py"),
    "MyBoxer.py": os.path.join(viewcontroller_dir, "1-PreProcess", "MyBoxer.py"),
    "MyGlypher.py": os.path.join(viewcontroller_dir, "1-PreProcess", "MyGlypher.py"),
    "MyPixler.py": os.path.join(viewcontroller_dir, "1-PreProcess", "MyPixler.py"),
    "MyGrounder.py": os.path.join(viewcontroller_dir, "2-TrainTesseract", "MyGrounder.py"),
    "MyReader.py": os.path.join(viewcontroller_dir, "2-TrainTesseract", "MyReader.py"),
    "MyTrainer.py": os.path.join(viewcontroller_dir, "2-TrainTesseract", "MyTrainer.py"),
    "MyLexer.py": os.path.join(viewcontroller_dir, "3-Process", "MyLexer.py"),
    "MyResolver.py": os.path.join(viewcontroller_dir, "3-Process", "MyResolver.py"),
    "MyVersifier.py": os.path.join(viewcontroller_dir, "3-Process", "MyVersifier.py"),
    "MyWriter.py": os.path.join(viewcontroller_dir, "4-PostProcess", "MyWriter.py"),
}

from helpers.gui_runtime_env import sanitize_current_process_and_reexec

sanitize_current_process_and_reexec()

from helpers.SessionManager import SessionManager
from helpers.project_status_controller import ProjectStatusController
#from subprocess import Popen, PIPE, CalledProcessError
from helpers.HelpSystem import add_help_menu
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
# Custom imports
_UI_MODULE_PATH = os.path.join(script_dir, "MyLauncherUI.py")
_UI_SPEC = importlib.util.spec_from_file_location("biblion_launcher_ui", _UI_MODULE_PATH)
if _UI_SPEC is None or _UI_SPEC.loader is None:
    raise ImportError(f"Unable to load launcher UI module from {_UI_MODULE_PATH}")
_UI_MODULE = importlib.util.module_from_spec(_UI_SPEC)
_UI_SPEC.loader.exec_module(_UI_MODULE)
Ui_MainUI = _UI_MODULE.Ui_MainUI
from helpers.LocalFileDrop import LocalFileDropMixin
from helpers.workflow_stack_wizard_dialog import WorkflowStackWizardDialog
from Developer.Publisher.launcher_registry import (
    LauncherIntegrationController,
    build_default_launcher_registry,
)

_qt_previous_message_handler = None


def _qt_message_filter(msg_type, context, message):
    if message and message.strip() == "QSocketNotifier: Can only be used with threads started with QThread":
        return

    if _qt_previous_message_handler is not None:
        _qt_previous_message_handler(msg_type, context, message)
        return

    sys.stderr.write(f"{message}\n")


def install_qt_warning_filter():
    global _qt_previous_message_handler
    if os.environ.get("BIBLION_SUPPRESS_QSOCKETNOTIFIER_WARNING", "1") != "1":
        return
    _qt_previous_message_handler = qtc.qInstallMessageHandler(_qt_message_filter)

# Dialog Imports

#import MyPixler as pixler
#import CropTif as croptif
#import QtCropImage as cropimg
#import Qt5SelectRegion
#from MultiPreProcess import MultiPreProcess as mpp
#import Qt5GroundTruthReview as gtr
#import Qt5VersifyText as versify
#import MyWriter as writer
#import MyPixler as pixler
#import Qt5ResolveVariants as resolver

#print(len(locals()))

class MainWindow(LocalFileDropMixin, qtw.QMainWindow):

# Menu and Toolbar Action Methods

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_MainUI()
        self.ui.setupUi(self)
        if hasattr(self.ui, 'actionExit'):
            self.ui.actionExit.triggered.connect(self.close)
        self.session_manager = SessionManager()
        #Implement Co-pilot Help system
        add_help_menu(self, 'MyServer')
        # extended slots code
        #
        self.ui.actionMy_Reader.triggered.connect(self.OpenWithMyReader)
        self.ui.actionMy_Scanner.triggered.connect(self.OpenWithMyScanner)
        self.ui.actionMy_Glypher.triggered.connect(self.OpenWithMyGlypher)
        self.ui.actionMy_Pixler.triggered.connect(self.OpenWithMyPixler)
        self.ui.actionMy_Boxer.triggered.connect(self.OpenWithMyBoxer)
        self.ui.actionMy_Versifier.triggered.connect(self.OpenWithMyVersifier)
        self.ui.actionMy_Resolver.triggered.connect(self.OpenWithMyResolver)
        self.ui.actionMy_Lexer.triggered.connect(self.OpenWithMyLexer)
        self.ui.actionMy_Grounder.triggered.connect(self.OpenWithMyGrounder)
        self.ui.actionMy_Trainer.triggered.connect(self.OpenWithMyTrainer)
        self.ui.actionMy_Writer.triggered.connect(self.OpenWithMyWriter)
        self.ui.actionExplorer.triggered.connect(self.OpenWithMyExplorer)

        self.ui.actionUpdate_Wordlist_tb.triggered.connect(self.actionUpdate_Wordlist)
        self.ui.actionTrain_Tesseract_tb.triggered.connect(self.actionTrain_Tesseract)
        if hasattr(self.ui, 'actionProject_Workflow_Wizard'):
            self.ui.actionProject_Workflow_Wizard.triggered.connect(self.open_project_workflow_wizard)
        if hasattr(self.ui, 'actionPage_Workflow_Wizard'):
            self.ui.actionPage_Workflow_Wizard.triggered.connect(self.open_page_workflow_wizard)

        #self.ui.Gimpbutton.clicked.connect(self.actionGimpEdit)
        self.ui.MyReaderbutton.clicked.connect(self.OpenWithMyReader)
        self.ui.MyScannerbutton.clicked.connect(self.OpenWithMyScanner)
        self.ui.MyGlypherbutton.clicked.connect(self.OpenWithMyGlypher)
        self.ui.MyBoxerbutton.clicked.connect(self.OpenWithMyBoxer)
        self.ui.MyPixlerbutton.clicked.connect(self.OpenWithMyPixler)
        self.ui.MyVersifierbutton.clicked.connect(self.OpenWithMyVersifier)
        self.ui.MyResolverbutton.clicked.connect(self.OpenWithMyResolver)
        self.ui.MyLexerbutton.clicked.connect(self.OpenWithMyLexer)
        self.ui.MyGrounderbutton.clicked.connect(self.OpenWithMyGrounder)
        self.ui.MyTrainerbutton.clicked.connect(self.OpenWithMyTrainer)
        self.ui.MyWriterbutton.clicked.connect(self.OpenWithMyWriter)
        self.ui.MyExplorerbutton.clicked.connect(self.OpenWithMyExplorer)
        if hasattr(self.ui, 'MyServerbutton'):
            self.ui.MyServerbutton.clicked.connect(self.OpenWithMyServer)

        # UI and slots code ends here.

        # Show the Main user interface
        self.ui.OCRDocument = qtg.QTextDocument(self.ui.RightPanelwidget)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(20)
        self.ui.OCRDocument.setDefaultFont(font)

        self.ui.OCRDocument.setDefaultFont(font)
        self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
        self.ui.RightPanelwidgetFormat = qtg.QTextFormat()
        self.ui.OCRCursor = qtg.QTextCursor(self.ui.OCRDocument)

        self.ui.RightPanelwidget.setDocument(self.ui.OCRDocument)

        self.launcher_registry = build_default_launcher_registry()
        self.launch_controller = LauncherIntegrationController(
            self.launcher_registry,
            launch_callback=self.run_child_module,
            help_panel_callback=self._swap_help_panel_text,
        )

        # Restore Session settings
        self.get_session_settings()
        self.project_status_controller = ProjectStatusController(
            self,
            'MyLauncher',
            session_manager=self.session_manager,
        )

        self.show()

    def _viewcontroller_stage_names(self):
        stage_folders = []
        for entry in os.listdir(viewcontroller_dir):
            entry_path = os.path.join(viewcontroller_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            match = re.match(r'^(\d+)-', entry)
            if not match:
                continue
            stage_folders.append((int(match.group(1)), entry))
        stage_folders.sort(key=lambda item: item[0])
        return [name for _idx, name in stage_folders]

    def _workflow_stage_module_map(self):
        return {
            '0-MainUI': [
                {'module': 'MyServer', 'label': 'Project setup and workflow governance'},
                {'module': 'MyScanner', 'label': 'Source scanning and source acquisition'},
                {'module': 'MyExplorer', 'label': 'Project structure review'},
            ],
            '1-PreProcess': [
                {'module': 'MyPixler', 'label': 'Image cleanup and prep'},
                {'module': 'MyBoxer', 'label': 'Page/line/word box workflows'},
                {'module': 'MyGlypher', 'label': 'Glyph and project font workflows'},
            ],
            '2-TrainTesseract': [
                {'module': 'MyReader', 'label': 'Read and review OCR content'},
                {'module': 'MyGrounder', 'label': 'Ground truth preparation'},
                {'module': 'MyTrainer', 'label': 'Training workflow execution'},
            ],
            '3-Process': [
                {'module': 'MyLexer', 'label': 'Lexicon workflow pass'},
                {'module': 'MyResolver', 'label': 'Variant resolution workflows'},
                {'module': 'MyVersifier', 'label': 'Verse alignment workflows'},
            ],
            '4-PostProcess': [
                {'module': 'MyWriter', 'label': 'Export and publication workflows'},
            ],
        }

    def _build_stage_plan(self, mode='project'):
        stage_map = self._workflow_stage_module_map()
        ordered_stage_names = self._viewcontroller_stage_names()

        if mode == 'project':
            allowed_modules = {
                'MyServer', 'MyScanner', 'MyExplorer',
                'MyPixler', 'MyBoxer', 'MyGlypher',
                'MyReader', 'MyGrounder', 'MyTrainer',
                'MyLexer', 'MyResolver', 'MyVersifier', 'MyWriter',
            }
        else:
            allowed_modules = {
                'MyScanner',
                'MyPixler', 'MyBoxer', 'MyGlypher',
                'MyReader', 'MyGrounder', 'MyTrainer',
                'MyLexer', 'MyResolver', 'MyVersifier', 'MyWriter',
            }

        stage_plan = []
        for stage_name in ordered_stage_names:
            steps = [
                step for step in stage_map.get(stage_name, [])
                if step.get('module') in allowed_modules
            ]
            if not steps:
                continue
            stage_plan.append(
                {
                    'key': stage_name,
                    'title': stage_name,
                    'description': (
                        'Project-scoped workflow stage. Use this stage macro to launch relevant modules in order.'
                        if mode == 'project'
                        else 'Page-scoped workflow stage. Use this stage macro for page-level operations.'
                    ),
                    'steps': steps,
                }
            )
        return stage_plan

    def _run_stage_macro(self, stage_key, stage_plan):
        target_stage = next((stage for stage in stage_plan if stage.get('key') == stage_key), None)
        if target_stage is None:
            return
        for step in target_stage.get('steps', []):
            module_name = step.get('module', '').strip()
            if module_name:
                self._open_module_by_name(module_name)

    def _run_full_macro(self, stage_plan):
        for stage in stage_plan:
            self._run_stage_macro(stage.get('key', ''), stage_plan)

    def _open_module_by_name(self, module_name):
        dispatch = {
            'MyServer': self.OpenWithMyServer,
            'MyScanner': self.OpenWithMyScanner,
            'MyExplorer': self.OpenWithMyExplorer,
            'MyPixler': self.OpenWithMyPixler,
            'MyBoxer': self.OpenWithMyBoxer,
            'MyGlypher': self.OpenWithMyGlypher,
            'MyReader': self.OpenWithMyReader,
            'MyGrounder': self.OpenWithMyGrounder,
            'MyTrainer': self.OpenWithMyTrainer,
            'MyLexer': self.OpenWithMyLexer,
            'MyResolver': self.OpenWithMyResolver,
            'MyVersifier': self.OpenWithMyVersifier,
            'MyWriter': self.OpenWithMyWriter,
        }
        callback = dispatch.get(module_name)
        if callback is not None:
            callback()

    def open_project_workflow_wizard(self):
        stage_plan = self._build_stage_plan(mode='project')
        dialog = WorkflowStackWizardDialog(
            title='Project Workflow Wizard',
            intro_text=(
                'Run project workflow stages in ViewController numbered-folder order. '
                'This macro-oriented view helps reduce operator flow errors while keeping manual processes available.'
            ),
            stage_plan=stage_plan,
            run_stage_callback=lambda stage_key: self._run_stage_macro(stage_key, stage_plan),
            run_all_callback=lambda: self._run_full_macro(stage_plan),
            parent=self,
        )
        dialog.exec_()

    def open_page_workflow_wizard(self):
        stage_plan = self._build_stage_plan(mode='page')
        dialog = WorkflowStackWizardDialog(
            title='Page Workflow Wizard',
            intro_text=(
                'Run page-oriented stages in numbered ViewController order. '
                'Use this for page-specific progression while preserving global project administration in MyServer.'
            ),
            stage_plan=stage_plan,
            run_stage_callback=lambda stage_key: self._run_stage_macro(stage_key, stage_plan),
            run_all_callback=lambda: self._run_full_macro(stage_plan),
            parent=self,
        )
        dialog.exec_()

    def get_session_settings(self):
        # get session settings from shared manager
        print("loading session")
        active_project = SessionManager().get_active_project('Session.json')
        self.current_project_root = active_project.get('project_root', '')
        self.current_project_name = active_project.get('project_name', '')
        session = self.session_manager.values('Session.json')

        def get_setting(name: str, default=None):
            if default is None:
                default = getattr(self, name, None)
            return session.get(f'self.{name}', default)

        #self.ocrlang = get_setting('ocrlang', '')
        #self.ocrmodel = get_setting('ocrmodel', '')
        self.tessdatadir = get_setting('tessdatadir', '')
        self.tesseract = get_setting('tesseract', '')
        self.tesstrain = get_setting('tesstrain', '')
        self.font = get_setting('font', '')
        self.fontsize = get_setting('fontsize', '20')
        self.txtpath = get_setting('txtpath', '')
        self.txtdir = get_setting('txtdir', '')

    def get_workflow_settings(self):

        # Opening JSON file
        workflow_file = os.path.join(project_root, 'Model', 'SQLite', 'json', 'Workflow.json')
        with open(workflow_file, 'r') as f:
            data = json.load(f)

        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])

        # Closing file
        f.close()

    def toggleGreekToolbars(self):

        greekimgpagesstate = self.ui.GreekImagePagesToolBar.isVisible()
        greekimglinesstate = self.ui.GreekImageLinesToolBar.isVisible()
        greektxtlinesstate = self.ui.GreekTextLinesToolBar.isVisible()

        # Set the visibility to its inverse
        self.ui.GreekImagePagesToolBar.setVisible(not greekimgpagesstate)
        self.ui.GreekImageLinesToolBar.setVisible(not greekimglinesstate)
        self.ui.GreekTextLinesToolBar.setVisible(not greektxtlinesstate)

    '''def toggleLatinToolbars(self):

        latinimgpagesstate = self.ui.LatinImagePagesToolBar.isVisible()
        latinimglinesstate = self.ui.LatinImageLinesToolBar.isVisible()
        latintxtlinesstate = self.ui.LatinTextLinesToolBar.isVisible()

        # Set the visibility to its inverse
        self.ui.LatinImagePagesToolBar.setVisible(not latinimgpagesstate)
        self.ui.LatinImageLinesToolBar.setVisible(not latinimglinesstate)
        self.ui.LatinTextLinesToolBar.setVisible(not latintxtlinesstate)'''

    '''def actionPixler(self):

        self.PixlerWindow = qtw.QMainWindow()
        self.pixlerui = pixler.Ui_Pixler()
        self.pixlerui.setupUi(self.PixlerWindow)
        self.PixlerWindow.show()

        self.pixlerui.OpenRefImgbutton.clicked.connect(self.loadRefImg)
        self.pixlerui.ImportRefImgFilebutton.clicked.connect(self.importRefImg)
        self.pixlerui.OverwriteRefImgbutton.clicked.connect(self.OverwriteRefImg)
        self.pixlerui.ExportImageFilebutton.clicked.connect(self.ExportImage)
        self.pixlerui.SaveImagebutton.clicked.connect(self.SaveImage)
        self.pixlerui.SaveAsImagebutton.clicked.connect(self.SaveImageAs)
        #self.pixlerui.OpenImageFilebutton.clicked.connect(self.OpenPixlerFileDialog)
        #self.pixlerui.PixlerButton.clicked.connect(self.PixlerTif(self.pixlerui.Image))
        #self.pixlerui.SavePixlerpedImgAsbutton.clicked.connect(self.DestLatinDialog)
        #self.pixlerui.SaveImagebutton.clicked.connect(self.DestLatinDialog)
        #self.pixlerui.buttonBox.accepted.connect(accept)
        #self.pixlerui.buttonBox.rejected.connect(reject)




        rsp = self.PixlerWindow.exec_()'''

    def actionGimpEdit(self):
        #gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"
        #gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp "+self.imgpath+"--file-forwarding org.gimp.GIMP"
        gimp_cmd = "gimp " + self.imgpath
        '''if 'self.imgpath' in locals():
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --document-export =" + self.imgpath + "--command=gimp-2.10" + self.imgpath + "--file-forwarding org.gimp.GIMP"
            print(self.imgpath)
        else:
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"'''

        os.system(gimp_cmd)

    def actionUpdate_Wordlist(self):
        pass

    def actionTrain_Tesseract(self):
        pass

    def loadText(self):
        '''self.textpath = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if self.textpath:
            self.textfile = QtCore.QFile(self.textpath)
            self.txtfilename = os.path.basename(self.textpath)
            self.showText(MainWindow,self.txtfilename)'''

        self.open_non_modal_text_picker(
            'Open text file',
            self.txtdir,
            self.showText,
            '_text_open_dialog',
        )

    def OpenTextFileDialog(self, MainWindow):
        self.txtpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file',self.txtdir,
            'Text files (*.txt *.csv)')[0]

        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
            self.ui.TextLE.setText(filename)

            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.txtpath)
                self.ui.RightPanelwidget.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.RightPanelwidget.insertPlainText(text)
                else:
                    self.ui.RightPanelwidget.setPlainText(text)

                # update font to selection and size
                self.on_font_update()

                file.close()

        jsonfile = os.path.join(project_root, 'Model', 'Data', 'json', 'Session.json')

        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.txtpath"
            txtdir_key = r"self.txtdir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.txtpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:
                    Setting['CurrentValue'] = self.txtdir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

        #txtdirpath = self.txtdir
        self.txtfileList = []
        for t in os.listdir(self.txtdir):
            tpath = os.path.join(self.txtdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.txtfileList.append(tpath)
        self.sortTextFiles()

    def showText(self, txtfilename):
        #self.textfile = txtfilename
        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
            self.ui.TextLE.setText(filename)

            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.txtpath)
                self.ui.RightPanelwidget.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.RightPanelwidget.insertPlainText(text)
                else:
                    self.ui.RightPanelwidget.setPlainText(text)
            #textfile.close()
            #txtdirpath = os.path.dirname(self.textpath)

            # update font to selection and size
            self.on_font_update()

            # update line spacing
            self.SetLineSpacing()
            file.close()

        jsonfile = os.path.join(project_root, 'Model', 'Data', 'json', 'Session.json')

        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.txtpath"
            txtdir_key = r"self.txtdir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.txtpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:
                    Setting['CurrentValue'] = self.txtdir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

        self.txtfileList = []
        for t in os.listdir(self.txtdir):
            tpath = os.path.join(self.txtdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.txtfileList.append(tpath)

        self.sortTextFiles()

    def SaveRawTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Raw text file',self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.ui.OCRDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):

        #if self.txtdir:
            #defaultdir = self.txtdir
        #else:
            #defaultdir = r"/home/jetson/Projects/Python/EstablishTruth/Greek_txt_pages/"

        defaultdir = self.txtdir + r"/"
        defaultfile = self.ui.TextLE.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            print(path)
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)

        self.ui.TextLE.setText(filename)
        file.close()

    def run_child_module(self, filename):
        module_path = RUNTIME_MODULE_PATHS.get(filename, os.path.join(script_dir, filename))
        creationflags = 0
        if os.name == 'nt':
            creationflags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)
        subprocess.Popen([sys.executable, module_path], creationflags=creationflags)

    def OpenWithMyReader(self):
        self.run_child_module('MyReader.py')

    def OpenWithMyScanner(self):
        if not self.launch_controller.launch_module('MyScanner'):
            self.run_child_module('MyScanner.py')

    def OpenWithMyGlypher(self):
        self.run_child_module('MyGlypher.py')

    def OpenWithMyBoxer(self):
        self.run_child_module('MyBoxer.py')

    def OpenWithMyPixler(self):
        if not self.launch_controller.launch_module('MyPixler'):
            self.run_child_module('MyPixler.py')

    def OpenWithMyVersifier(self):
        self.run_child_module('MyVersifier.py')

    def OpenWithMyResolver(self):
        self.run_child_module('MyResolver.py')

    def OpenWithMyLexer(self):
        self.run_child_module('MyLexer.py')

    def OpenWithMyGrounder(self):
        self.run_child_module('MyGrounder.py')

    def OpenWithMyTrainer(self):
        self.run_child_module('MyTrainer.py')

    def OpenWithMyWriter(self):
        self.run_child_module('MyWriter.py')

    def OpenWithMyExplorer(self):
        if not self.launch_controller.launch_module('MyExplorer'):
            self.run_child_module('MyExplorer.py')

    def OpenWithMyServer(self):
        self._launch_registered_module('MyServer')

    def _launch_registered_module(self, module_id):
        if not self.launch_controller.launch_module(module_id):
            qtw.QMessageBox.warning(
                self,
                'Launch Not Registered',
                f'{module_id} is not registered as a launcher target.',
            )

    def _swap_help_panel_text(self, text):
        self.ui.RightPanelwidget.clear()
        self.ui.RightPanelwidget.setPlainText(text)
        self.on_font_update()

    def on_font_update(self):
        # update font to selection and size
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        #font = qtg.QFont(self.font)
        #font.setPointSize(int(self.fontsize))

        self.ui.RightPanelwidget.setFont(font)

    def on_lang_select(self):
        pass

# Only run this code if I am actually running this script
if __name__ == '__main__':
    install_qt_warning_filter()
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
