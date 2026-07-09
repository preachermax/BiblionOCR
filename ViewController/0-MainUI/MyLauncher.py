#print(len(locals()))

# Python imports
import sys
import os
import re
import shlex
import subprocess
#import glob
import shutil
import json

from gui_runtime_env import sanitize_current_process_and_reexec

script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sanitize_current_process_and_reexec()

from SessionManager import SessionManager
from project_status_controller import ProjectStatusController
#from subprocess import Popen, PIPE, CalledProcessError
import pytesseract
import tiffcapture
import qimage2ndarray
from queue import Queue
from ext import mainfind
from HelpSystem import add_help_menu
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QObject, QThread, pyqtSignal
# Custom imports
from MyLauncherUI import Ui_MainUI
from PreProcess import PreProcess as pp
from LocalFileDrop import LocalFileDropMixin

# Dialog Imports
from Dialogs.ExtractDialog import Ui_ExtractDialog
from Dialogs.pdf4tifDialog import Ui_pdf4tifDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.tif2monoDialog import Ui_tif2monoDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.mono2pngDialog import Ui_mono2pngDialog
from Dialogs.deskew_monoDialog import Ui_deskew_monoDialog

#import MyPixler as pixler
#import CropTif as croptif
#import QtCropImage as cropimg
#import Qt5SelectRegion
#from MultiPreProcess import MultiPreProcess as mpp
from Training import Train as tr
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

        # UI and slots code ends here.

        # Show the Main user interface
        self.ui.OCRDocument = qtg.QTextDocument(self.ui.OCRText)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(20)
        self.ui.OCRDocument.setDefaultFont(font)

        self.ui.OCRDocument.setDefaultFont(font)
        self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
        self.ui.OCRTextFormat = qtg.QTextFormat()
        self.ui.OCRCursor = qtg.QTextCursor(self.ui.OCRDocument)

        self.ui.OCRText.setDocument(self.ui.OCRDocument)

        # Restore Session settings
        self.get_session_settings()
        self.project_status_controller = ProjectStatusController(
            self,
            'MyLauncher',
            session_manager=self.session_manager,
        )

        self.show()

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
                self.ui.OCRText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.OCRText.insertPlainText(text)
                else:
                    self.ui.OCRText.setPlainText(text)

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
                self.ui.OCRText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.OCRText.insertPlainText(text)
                else:
                    self.ui.OCRText.setPlainText(text)
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
        module_path = os.path.join(script_dir, filename)
        subprocess.Popen(['python3', module_path])

    def OpenWithMyReader(self):
        self.run_child_module('MyReader.py')

    def OpenWithMyScanner(self):
        self.run_child_module('MyScanner.py')

    def OpenWithMyGlypher(self):
        self.run_child_module('MyGlypher.py')

    def OpenWithMyBoxer(self):
        self.run_child_module('MyBoxer.py')

    def OpenWithMyPixler(self):
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
        self.run_child_module('MyExplorer.py')

    def on_font_update(self):
        # update font to selection and size
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        #font = qtg.QFont(self.font)
        #font.setPointSize(int(self.fontsize))

        self.ui.OCRText.setFont(font)

    def on_lang_select(self):
        pass

# Only run this code if I am actually running this script
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
