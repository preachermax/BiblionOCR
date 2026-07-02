# Python imports
import sys
import os
import re
import shutil
import json
import csv
import time
import platform
from HelpSystem import add_help_menu
import subprocess

# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

from ext import *
from ext import versifiercount, versefind, reffind
# Custom imports
from MyVersifierUI import Ui_Versifier
from SessionManager import SessionManager
from Dialogs.VariantRecorderDialog import Ui_RecorderDialog
from SqliteHelper import *
from LocalFileDrop import LocalFileDropMixin
import ChrReference as chrref
#import pytesseract


class Ui_MainWindow(LocalFileDropMixin, qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set Project Home
        self.mod_dirname = os.path.dirname(__file__)
        up_once = os.path.join(self.mod_dirname,"..")
        up_twice = os.path.join(up_once,"..")
        self.mod_rootdir = up_twice
        self.mod_realpath = os.path.realpath(self.mod_rootdir)
        self.mod_abspath = os.path.abspath(self.mod_realpath)
        self.mod_relpath = os.path.relpath(self.mod_abspath)
        self.projecthome = self.mod_abspath + os.sep
        print(f'OS Path dirname: {self.mod_dirname}')
        print(f'OS Path up one folder: {up_once}')
        #print(f'OS Path up two folders: {up_twice}')
        print(f'OS Path rootdir: {self.mod_rootdir}')
        print(f'OS Path realpath: {self.mod_realpath}')
        print(f'OS Path abspath: {self.mod_abspath}')
        print(f'OS Path relpath: {self.mod_dirname}')
        print(f'Project Home: {self.projecthome}')

        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Versifier()
        self.ui.setupUi(self)
        #Implement Co-pilot Help system
        add_help_menu(self, 'MyVersifier')
        self.ui.actionCharacter_Reference.triggered.connect(self.OpenChrReference)

        self.ui.BothPrevBookButton.clicked.connect(self.findPrevVerseBook)
        self.ui.BothPrevBookButton.clicked.connect(self.findPrevRefBook)
        self.ui.BothPrevBookButton.clicked.connect(self.updateBothVerse)
        self.ui.BothPrevChapterButton.clicked.connect(self.findPrevVerseChapter)
        self.ui.BothPrevChapterButton.clicked.connect(self.findPrevRefChapter)
        self.ui.BothPrevChapterButton.clicked.connect(self.updateBothVerse)
        self.ui.BothPrevVerseButton.clicked.connect(self.findPrevVerseVerse)
        self.ui.BothPrevVerseButton.clicked.connect(self.findPrevRefVerse)
        self.ui.BothPrevVerseButton.clicked.connect(self.updateBothVerse)
        self.ui.BothPrevWordButton.clicked.connect(self.findPrevVerseWord)
        self.ui.BothPrevWordButton.clicked.connect(self.findPrevRefWord)


        self.ui.BothNextBookButton.clicked.connect(self.findNextVerseBook)
        self.ui.BothNextBookButton.clicked.connect(self.findNextRefBook)
        self.ui.BothNextBookButton.clicked.connect(self.updateBothVerse)
        self.ui.BothNextChapterButton.clicked.connect(self.findNextVerseChapter)
        self.ui.BothNextChapterButton.clicked.connect(self.findNextRefChapter)
        self.ui.BothNextChapterButton.clicked.connect(self.updateBothVerse)
        self.ui.BothNextVerseButton.clicked.connect(self.findNextVerseVerse)
        self.ui.BothNextVerseButton.clicked.connect(self.findNextRefVerse)
        self.ui.BothNextVerseButton.clicked.connect(self.updateBothVerse)
        self.ui.BothNextWordButton.clicked.connect(self.findNextVerseWord)
        self.ui.BothNextWordButton.clicked.connect(self.findNextRefWord)

        self.ui.WordCountbutton.clicked.connect(self.wordCount)

        self.ui.OCRModelComboBox.currentTextChanged.connect(self.on_lang_select)
        self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)
        self.ui.bookComboBox.currentTextChanged.connect(self.loadChapterCombo)
        self.ui.chapterComboBox.currentTextChanged.connect(self.loadVerseCombo)
        self.ui.AnchorCkBox.stateChanged.connect(self.weighAnchor)
        self.ui.Anchorbutton.clicked.connect(self.dropAnchor)
        self.ui.AddVersebutton.clicked.connect(self.addVerse)
        self.ui.Synchronizebutton.clicked.connect(self.findBothVerse)
        self.ui.Recorderbutton.clicked.connect(self.VarianceRecorder)
        self.ui.Resolvebutton.clicked.connect(self.OpenResolver)
        self.ui.NormcheckBox.stateChanged.connect(self.bothNormCheckbox)

        self.ui.VersebookComboBox.currentTextChanged.connect(self.loadVerseChapterCombo)
        self.ui.VersechapterComboBox.currentTextChanged.connect(self.loadVerseVerseCombo)
        self.ui.VersechapterComboBox.currentTextChanged.connect(self.loadVerseLineCombo)
        self.ui.VerseverseComboBox.currentTextChanged.connect(self.updateVerseLineCombo)
        self.ui.VersefindPushButton.clicked.connect(self.findVerseVerse)

        self.ui.RefbookComboBox.currentTextChanged.connect(self.loadRefChapterCombo)
        self.ui.RefchapterComboBox.currentTextChanged.connect(self.loadRefVerseCombo)
        self.ui.RefchapterComboBox.currentTextChanged.connect(self.loadRefLineCombo)
        self.ui.RefverseComboBox.currentTextChanged.connect(self.updateRefLineCombo)
        self.ui.ReffindPushButton.clicked.connect(self.findRefVerse)

        #Setup Verse Text
        self.ui.VersePrevBookButton.clicked.connect(self.findPrevVerseBook)
        self.ui.VerseNextBookButton.clicked.connect(self.findNextVerseBook)
        self.ui.VersePrevChapterButton.clicked.connect(self.findPrevVerseChapter)
        self.ui.VerseNextChapterButton.clicked.connect(self.findNextVerseChapter)
        self.ui.PrevVerseButton.clicked.connect(self.findPrevVerseVerse)
        self.ui.NextVerseButton.clicked.connect(self.findNextVerseVerse)
        self.ui.PrevVerseWordButton.clicked.connect(self.findPrevVerseWord)
        self.ui.NextVerseWordButton.clicked.connect(self.findNextVerseWord)

        self.ui.VerseLHDialogtbutton.clicked.connect(self.GetVerseLineSpacing)
        self.ui.VerseLHslider.valueChanged.connect(self.SetVerseLineSpacing)
        self.ui.VerseLHslider.sliderReleased.connect(self.DisableVerseLHSlider)
        self.ui.VerseLHlineEdit.textChanged.connect(self.MoveVerseLHSlider)
        self.ui.VerseLHslider.hide()
        self.ui.VerseFindReplacebutton.clicked.connect(versefind.Find(self).show)
        self.ui.VerseNormcheckBox.stateChanged.connect(self.showVerseNormText)
        self.ui.VerseNormcheckBox.stateChanged.connect(self.showVerseText)
        self.ui.VerseNormButton.clicked.connect(self.VerseNormalize)
        self.ui.VerseTextbutton.clicked.connect(self.loadVerseText)
        self.ui.SaveAsVerseTextbutton.clicked.connect(self.SaveAsVerseTextDialog)
        self.ui.SaveVerseTextbutton.clicked.connect(self.SaveVerseTextDialog)
        self.ui.VerseMyWriterbutton.clicked.connect(self.OpenWithMyWriter)
        self.ui.reloadVerseTextbutton.clicked.connect(self.ReloadVerseText)
        self.ui.VersefontComboBox.currentFontChanged.connect(self.on_versefont_update)
        self.ui.VersefontSizeBox.valueChanged.connect(self.on_versefont_update)
        self.ui.VerseDocument = qtg.QTextDocument(self.ui.VerseText)
        font = SessionManager().build_workflow_font(
            "FROMVS",
            20,
            os.path.dirname(os.path.realpath(__file__)),
        )
        self.ui.VerseDocument.setDefaultFont(font)
        self.ui.VerseBlockFormat = qtg.QTextBlockFormat()
        self.ui.VerseTextFormat = qtg.QTextFormat()
        self.ui.VerseCursor = qtg.QTextCursor(self.ui.VerseDocument)
        self.ui.VerseText.setDocument(self.ui.VerseDocument)
        self.Versefont = self.ui.VerseText.font()
        self.VersefontMetrics = qtg.QFontMetricsF(self.Versefont)
        self.VersespaceWidth = self.VersefontMetrics.width(' ')
        self.ui.VerseText.setTabStopWidth(int(self.VersespaceWidth * 4))

        #Setup Reference Text
        self.ui.RefPrevBookButton.clicked.connect(self.findPrevRefBook)
        self.ui.RefNextBookButton.clicked.connect(self.findNextRefBook)
        self.ui.RefPrevChapterButton.clicked.connect(self.findPrevRefChapter)
        self.ui.RefNextChapterButton.clicked.connect(self.findNextRefChapter)
        self.ui.PrevRefVerseButton.clicked.connect(self.findPrevRefVerse)
        self.ui.NextRefVerseButton.clicked.connect(self.findNextRefVerse)
        self.ui.PrevRefWordButton.clicked.connect(self.findPrevRefWord)
        self.ui.NextRefWordButton.clicked.connect(self.findNextRefWord)
        self.ui.RefLHDialogtbutton.clicked.connect(self.GetRefLineSpacing)
        self.ui.RefLHslider.valueChanged.connect(self.SetRefLineSpacing)
        self.ui.RefLHslider.sliderReleased.connect(self.DisableRefLHSlider)
        self.ui.RefLHlineEdit.textChanged.connect(self.MoveRefLHSlider)
        self.ui.RefLHslider.hide()
        self.ui.RefFindReplacebutton.clicked.connect(reffind.Find(self).show)
        self.ui.RefNormcheckBox.stateChanged.connect(self.showRefNormText)
        self.ui.RefNormcheckBox.stateChanged.connect(self.showRefText)
        self.ui.RefNormButton.clicked.connect(self.RefNormalize)
        self.ui.RefTextbutton.clicked.connect(self.loadRefText)
        self.ui.reloadRefTextbutton.clicked.connect(self.ReloadRefText)
        self.ui.ReffontComboBox.currentFontChanged.connect(self.on_reffont_update)
        self.ui.ReffontSizeBox.valueChanged.connect(self.on_reffont_update)
        self.ui.ReferenceDocument = qtg.QTextDocument(self.ui.RefText)
        font = SessionManager().build_workflow_font(
            "FROMVS",
            20,
            os.path.dirname(os.path.realpath(__file__)),
        )
        self.ui.ReferenceDocument.setDefaultFont(font)
        self.ui.ReferenceBlockFormat = qtg.QTextBlockFormat()
        self.ui.ReferenceTextFormat = qtg.QTextFormat()
        self.ui.ReferenceCursor = qtg.QTextCursor(self.ui.ReferenceDocument)
        self.ui.RefText.setDocument(self.ui.ReferenceDocument)
        self.Reffont = self.ui.RefText.font()
        self.ReffontMetrics = qtg.QFontMetricsF(self.Reffont)
        self.RefspaceWidth = self.ReffontMetrics.width(' ')
        self.ui.RefText.setTabStopWidth(int(self.RefspaceWidth * 4))

        # Accept dropped local text files on the two text panes and load them
        # through the normal Versifier loaders instead of letting QTextEdit
        # insert a file URL as plain text.
        self.install_local_file_drop_target(self.ui.RefText, text_handler=self.getRefText)
        self.install_local_file_drop_target(self.ui.VerseText, text_handler=self.getVerseText)

        # Restore Session settings
        self.get_session_settings()
        #print(f'Reference File Path: {self.refpath}')
        #self.getRefText(self.refpath)
        # Startup
        self.getstarted()

    def _startup_progress(self, message, end='\n'):
        print(f'[Versifier startup] {message}', end=end, flush=True)

    @staticmethod
    def _format_size(byte_count):
        for unit in ('B', 'KB', 'MB', 'GB'):
            if byte_count < 1024 or unit == 'GB':
                return f'{byte_count:.1f} {unit}' if unit != 'B' else f'{int(byte_count)} {unit}'
            byte_count /= 1024

    def _read_text_file_with_progress(self, path, label):
        total_size = os.path.getsize(path)
        self._startup_progress(f'{label}: reading {os.path.basename(path)} ({self._format_size(total_size)})')

        chunk_size = 1024 * 1024
        bytes_read = 0
        chunks = []
        last_report = 0

        with open(path, 'rb') as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
                bytes_read += len(chunk)

                if total_size and (bytes_read == total_size or time.time() - last_report >= 0.25):
                    percent = min(100, int(bytes_read * 100 / total_size))
                    print(
                        f'\r[Versifier startup] {label}: read {percent:3d}% '
                        f'({self._format_size(bytes_read)} / {self._format_size(total_size)})',
                        end='',
                        flush=True,
                    )
                    last_report = time.time()

        if total_size:
            print('', flush=True)

        self._startup_progress(f'{label}: decoding text')
        return b''.join(chunks).decode('UTF-8')

    def _run_with_terminal_spinner(self, message, func):
        spinner_code = (
            "import sys,time; "
            f"message={message!r}; "
            "frames='|/-\\\\'; start=time.time(); i=0; "
            "\nwhile True:\n"
            "    elapsed=int(time.time()-start)\n"
            "    sys.stdout.write(f'\\r[Versifier startup] {message} {frames[i % len(frames)]} {elapsed}s elapsed')\n"
            "    sys.stdout.flush()\n"
            "    i += 1\n"
            "    time.sleep(0.5)\n"
        )
        spinner = subprocess.Popen([sys.executable, '-u', '-c', spinner_code])
        try:
            return func()
        finally:
            spinner.terminate()
            try:
                spinner.wait(timeout=1)
            except subprocess.TimeoutExpired:
                spinner.kill()
            print(f'\r[Versifier startup] {message} complete           ', flush=True)

    def _begin_visible_text_load(self, label, path):
        message = f'{label}: loading {os.path.basename(path)} -- please wait...'
        self._startup_progress(message)
        if hasattr(self, 'ui') and hasattr(self.ui, 'statusbar'):
            self.ui.statusbar.showMessage(message)
        qtw.QApplication.setOverrideCursor(qtc.Qt.WaitCursor)
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)

    def _end_visible_text_load(self, label):
        try:
            qtw.QApplication.restoreOverrideCursor()
        except Exception:
            pass
        message = f'{label}: load complete'
        self._startup_progress(message)
        if hasattr(self, 'ui') and hasattr(self.ui, 'statusbar'):
            self.ui.statusbar.showMessage(message, 5000)
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)

    def get_session_settings(self):
        # get session settings
        self._startup_progress("loading session settings")
        session = SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).values('VersifierSession.json')

        def get_setting(name: str, default=None):
            if default is None:
                default = getattr(self, name, None)
            return session.get(f'self.{name}', default)

        def abs_project_path(name: str, default=''):
            value = session.get(f'self.{name}')
            if value:
                return os.path.join(self.projecthome, value.lstrip('/'))
            return getattr(self, name, default)

        def data_path(name: str, default=''):
            value = session.get(f'self.{name}')
            if value:
                return os.path.join(self.projecthome, self.jsondir.lstrip('/'), value.lstrip('/'))
            return getattr(self, name, default)

        self.jsondir = get_setting('jsondir', '')
        self.session = data_path('session')
        self.workflow = data_path('workflow')
        self.crossref = data_path('crossref')
        self.booksmarkdown = data_path('booksmarkdown')
        self.bookchapter = data_path('bookchapter')
        self.bookchapterverse = data_path('bookchapterverse')
        self.linebookchapterverse = data_path('linebookchapterverse')
        self.booksabbrnamenumindex = data_path('booksabbrnamenumindex')
        self.projectsdir = get_setting('projectsdir', '')
        self.projectname = get_setting('projectname', '')
        self.ocrlang = get_setting('ocrlang', '')
        self.ocrmodel = get_setting('ocrmodel', '')
        self.sqldir = abs_project_path('sqldir')
        self.bothbookabbr = get_setting('bothbookabbr', '')
        self.bothchapter = get_setting('bothchapter', '')
        self.bothverse = get_setting('bothverse', '')
        self.anchorbook = get_setting('anchorbook', '')
        self.anchorchapter = get_setting('anchorchapter', '')
        self.anchorverse = get_setting('anchorverse', '')
        self.anchorline = get_setting('anchorline', '')
        self.versebookabbr = get_setting('versebookabbr', '')
        self.versechapter = get_setting('versechapter', '')
        self.verseverse = get_setting('verseverse', '')
        self.verseline = get_setting('verseline', '')
        self.verselastbook = get_setting('verselastbook', '')
        self.verselastchapter = get_setting('verselastchapter', '')
        self.verselastverse = get_setting('verselastverse', '')
        self.verselastline = get_setting('verselastline', '')
        self.refbookabbr = get_setting('refbookabbr', '')
        self.refchapter = get_setting('refchapter', '')
        self.refverse = get_setting('refverse', '')
        self.refline = get_setting('refline', '')
        self.sourcebookmarkdown = get_setting('sourcebookmarkdown', '')
        self.greekbookmarkdown = get_setting('greekbookmarkdown', '')
        self.latinbookmarkdown = get_setting('latinbookmarkdown', '')
        self.variantdb = abs_project_path('variantdb')
        self.variantcorrected = get_setting('variantcorrected', '')
        self.variantpreserved = get_setting('variantpreserved', '')
        self.variantkey = get_setting('variantkey', '')
        self.versedbpath = abs_project_path('versedbpath')
        self.versetable = get_setting('versetable', '')
        self.versepath = abs_project_path('versepath')
        self.versedir = abs_project_path('versedir')
        self.versenormpathsel = get_setting('versenormpathsel', '')
        self.versenormpath = abs_project_path('versenormpath')
        self.versenormdir = abs_project_path('versenormdir')
        self.versefont = get_setting('versefont', '')
        self.versefontsize = get_setting('versefontsize', '')
        self.versewordnumber = get_setting('versewordnumber', '')
        self.verseword = get_setting('verseword', '')
        self.selverseword = get_setting('selverseword', '')
        self.verselineheight = get_setting('verselineheight', '')
        self.refdbpath = abs_project_path('refdbpath')
        self.reftable = get_setting('reftable', '')
        self.refpath = abs_project_path('refpath')
        self.refdir = abs_project_path('refdir')
        self.refnormpathsel = get_setting('refnormpathsel', '')
        self.refnormpath = abs_project_path('refnormpath')
        self.refnormdir = abs_project_path('refnormdir')
        self.reffont = get_setting('reffont', '')
        self.reffontsize = get_setting('reffontsize', '')
        self.refwordnumber = get_setting('refwordnumber', '')
        self.refword = get_setting('refword', '')
        self.selrefword = get_setting('selrefword', '')
        self.reflineheight = get_setting('reflineheight', '')

        if hasattr(self, 'ui'):
            self.ui.OCRlangComboBox.setCurrentText(self.ocrlang)
            self.ui.OCRModelComboBox.setCurrentText(self.ocrmodel)
            self.ui.bookComboBox.setCurrentText(self.bothbookabbr)
            self.ui.chapterComboBox.setCurrentText(self.bothchapter)
            self.ui.verseComboBox.setCurrentText(self.bothverse)
            self.ui.VersebookComboBox.setCurrentText(self.versebookabbr)
            self.ui.VersechapterComboBox.setCurrentText(self.versechapter)
            self.ui.VerseverseComboBox.setCurrentText(self.verseverse)
            self.ui.VerselineComboBox.setCurrentText(self.verseline)
            self.ui.RefbookComboBox.setCurrentText(self.refbookabbr)
            self.ui.RefchapterComboBox.setCurrentText(self.refchapter)
            self.ui.RefverseComboBox.setCurrentText(self.refverse)
            self.ui.ReflineComboBox.setCurrentText(self.refline)
            self.ui.VerseTextLE.setText(os.path.basename(self.versepath))
            self.ui.RefTextLE.setText(os.path.basename(self.refpath))

    def getstarted(self):
        self._startup_progress('starting initial text load')
        self._startup_progress(f'Reference File Path: {self.refpath}')
        self._startup_progress(f'Verse File Path: {self.versepath}')
        self.getRefText(self.refpath)
        self.getVerseText(self.versepath)
        self._startup_progress('locating current verse')
        self.findBothVerse()

        self.ui.bookComboBox.setCurrentText(self.bothbookabbr)
        self.ui.chapterComboBox.setCurrentText(self.bothchapter)
        self.ui.verseComboBox.setCurrentText(self.bothverse)
        print(f'Book: {self.bothbookabbr} Chapter: {self.bothchapter} Verse: {self.bothverse}')

        self.ui.VersebookComboBox.setCurrentText(self.versebookabbr)
        self.ui.VersechapterComboBox.setCurrentText(self.versechapter)
        self.ui.VerseverseComboBox.setCurrentText(self.verseverse)
        self.ui.VerselineComboBox.setCurrentText(self.verseline)
        print(f'Book: {self.versebookabbr} Chapter: {self.versechapter} Verse: {self.verseverse} Line: {self.verseline}')

        self.ui.RefbookComboBox.setCurrentText(self.refbookabbr)
        self.ui.RefchapterComboBox.setCurrentText(self.refchapter)
        self.ui.RefverseComboBox.setCurrentText(self.refverse)
        self.ui.ReflineComboBox.setCurrentText(self.refline)

        print(f'Book: {self.refbookabbr} Chapter: {self.refchapter} Verse: {self.refverse} Line: {self.refline}')
        self._startup_progress('ready')
        self.verseverse = self.ui.verseComboBox.currentText()
        #self.verseline = self.ui.lineComboBox..currentText()
        self.refverse = self.ui.verseComboBox.currentText()
        #self.refline = self.ui.lineComboBox.currentText()
        self.verseversenum = int(self.verseverse)
        self.refversenum = int(self.refverse)

        self.verseversecount = self.ui.verseComboBox.count()
        self.refversecount = self.ui.verseComboBox.count()

        self.nexttextversenum = int(self.ui.verseComboBox.currentText()) + 1
        self.nextrefversenum = int(self.ui.verseComboBox.currentText()) + 1

        self.prevtextversenum = int(self.ui.verseComboBox.currentText()) - 1
        self.prevrefversenum = int(self.ui.verseComboBox.currentText()) - 1

        self.versebook = self.ui.bookComboBox.currentText()
        self.versebookindex = self.ui.bookComboBox.currentIndex()
        self.versebooknum = self.versebookindex + 40
        self.versebookcount = self.ui.bookComboBox.count()

        self.refbook = self.ui.bookComboBox.currentText()
        self.refbookindex = self.ui.bookComboBox.currentIndex()
        self.refbooknum = self.refbookindex + 40
        self.refbookcount = self.ui.bookComboBox.count()

        print(f'self.verseverse = {self.verseverse}')
        print(f'self.verseversenum = {self.verseversenum}')
        print(f'self.verseversecount = {self.verseversecount}')
        print(f'self.prevtextversenum = {self.prevtextversenum}')
        print(f'self.nexttextversenum = {self.nexttextversenum}')

        #ChrRefText = open(self.projecthome + 'ViewController/3-ConductOCR/FROMVS ChrReference.txt', encoding = 'UTF-8').read()
        #self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        self.OpenChrReference()

    def OpenChrReference(self):
        self.chrrefmain = chrref.CharacterReference()
        self.chrrefmain.show()

    def dropAnchor(self):
        print("Drop Anchor!")
        self.ui.AnchorCkBox.setChecked(True)
        self.findBothVerse()
        print("Anchor's Fast!")

    def weighAnchor(self):
        if self.ui.AnchorCkBox.isChecked():
            self.anchorbook = self.ui.bookComboBox.currentText()
            self.anchorchapter = self.ui.chapterComboBox.currentText()
            self.anchorverse =  self.ui.verseComboBox.currentText()
            self.ui.AnchorCkBox.setChecked(False)
            self.dropAnchor()
        else:
            print("Anchor's Aweigh!")
            self.getSessionLastVerse()
            self.anchorbook = self.verselastbook
            self.anchorchapter = self.verselastchapter
            self.anchorverse = self.verselastverse
        self.updateSessionAnchor()

    def getSessionAnchor(self):
        print(f'Getting the anchor session settings')

        # Opening JSON file
        with open(self.session) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
            anchorbook_key = r"self.anchorbook"
            anchorchapter_key = r"self.anchorchapter"
            anchorverse_key = r"self.anchorverse"
            anchorline_key = r"self.anchorline"
            for Setting in data:
                    if Setting['Setting'] == anchorbook_key:
                        self.anchorbook = Setting['CurrentValue']
                        self.ui.VersebookComboBox.setCurrentText(self.anchorbook)
                    elif Setting['Setting'] == anchorchapter_key:
                        self.anchorchapter = Setting['CurrentValue']
                        self.ui.VersechapterComboBox.setCurrentText(self.anchorchapter)
                    elif Setting['Setting'] == anchorverse_key:
                        self.anchorverse = Setting['CurrentValue']
                        self.ui.VerseverseComboBox.setCurrentText(self.anchorverse)
                    elif Setting['Setting'] == anchorline_key:
                        self.anchorline = Setting['CurrentValue']
                        self.ui.VerselineComboBox.setCurrentText(self.anchorline)
        f.close()
        self.anchor = f'{self.anchorbook} {self.anchorchapter}:{self.anchorverse}'

    def updateSessionAnchor(self):
        print(f'Updating the anchor session setting')
        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.anchorbook': self.ui.VersebookComboBox.currentText(),
            'self.anchorchapter': self.ui.VersechapterComboBox.currentText(),
            'self.anchorverse': self.ui.VerseverseComboBox.currentText(),
            'self.anchorline': self.ui.VerselineComboBox.currentText(),
        })

    def addVerse(self):
        if self.ui.VerseNormcheckBox.isChecked():
            print("New verses cannot be added in Normalized text view.")
        else:

            print(f'Adding new verse:')
            self.getSessionLastVerse()
            addversenum = int(self.ui.VerseverseComboBox.currentText()) + 1
            addchapternum = int(self.ui.VersechapterComboBox.currentText())
            #addbookindex = self.ui.VersebookComboBox.currentIndex()
            addbooktext = self.ui.VersebookComboBox.currentText()
            print(f'addbooktext 1: {addbooktext}')
            if self.verselastverse:
                #self.findVerseVerse()
                cursor = self.ui.VerseText.textCursor()
                self.currentpos = cursor.position()
                self.ui.VerseText.find(self.lastverse)
                cursor.movePosition(cursor.EndOfBlock, cursor.MoveAnchor)
                cursor.insertBlock()
                #print(f'addbooktext 1: {addbooktext}')
                if addversenum > self.ui.VerseverseComboBox.count():
                    addversenum = 1
                    addchapternum += 1
                    if addchapternum > self.ui.VersechapterComboBox.count():
                        addchapternum += 1
                        #addbookindex += 1
                        addbooktext = self.ui.VersebookComboBox.itemText(self.ui.VersebookComboBox.currentIndex() + 1)
                        print(f'addbooktext +1: {addbooktext}')

                self.ui.VersebookComboBox.setCurrentText(addbooktext)
                self.ui.VersechapterComboBox.setCurrentText(str(addchapternum))
                self.ui.VerseverseComboBox.setCurrentText(str(addversenum))

                addbooktext = self.ui.VersebookComboBox.currentText()
                addchaptertext = self.ui.VersechapterComboBox.currentText()
                addversetext = self.ui.VerseverseComboBox.currentText()

                self.verselastbook = addbooktext
                self.verselastchapter = addchaptertext
                self.verselastverse = addversetext
                #self.verselastline = str(addlinenum)
                self.lastverse = self.verselastbook + " " + self.verselastchapter + ":" + self.verselastverse
                #self.ui.radioButtonVerses.setChecked(True)
                self.ui.bookComboBox.setCurrentText(self.verselastbook)
                self.ui.chapterComboBox.setCurrentText(self.verselastchapter)
                self.ui.verseComboBox.setCurrentText(self.verselastverse)

                #self.ui.AnchorCkBox.setChecked(True)
                cursor.insertText(self.lastverse + " ")
                self.findBothVerse()
                self.updateSessionLastVerse()

    def getSessionLastVerse(self):
        print(f'Getting the last verse session setting')

        # Opening JSON file
        with open(self.session) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
            verselastbook_key = r"self.verselastbook"
            verselastchapter_key = r"self.verselastchapter"
            verselastverse_key = r"self.verselastverse"
            verselastline_key = r"self.verselastline"
            for Setting in data:
                    if Setting['Setting'] == verselastbook_key:
                        self.verselastbook = Setting['CurrentValue']
                        self.ui.VersebookComboBox.setCurrentText(self.verselastbook)
                    elif Setting['Setting'] == verselastchapter_key:
                        self.verselastchapter = Setting['CurrentValue']
                        self.ui.VersechapterComboBox.setCurrentText(self.verselastchapter)
                    elif Setting['Setting'] == verselastverse_key:
                        self.verselastverse = Setting['CurrentValue']
                        self.ui.VerseverseComboBox.setCurrentText(self.verselastverse)
                    elif Setting['Setting'] == verselastline_key:
                        self.verselastline = Setting['CurrentValue']
                        self.ui.VerselineComboBox.setCurrentText(self.verselastline)
        f.close()
        self.lastverse = f'{self.verselastbook} {self.verselastchapter}:{self.verselastverse}'

    def updateSessionLastVerse(self):
        print(f'Updating the last verse session setting')
        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.verselastbook': self.verselastbook,
            'self.verselastchapter': self.verselastchapter,
            'self.verselastverse': self.verselastverse,
            'self.verselastline': self.ui.VerselineComboBox.currentText(),
        })

    '''def getLastVerse(self):
        print(f'Finding the last verse:')
        versecount = self.ui.VerseDocument.blockCount()

        cursor3 = self.ui.VerseText.textCursor()
        cursor3.setPosition(cursor3.End)
        #cursor3.movePosition(cursor3.PreviousBlock, cursor3.MoveAnchor)
        #loopcount = versecount
        loopcount = 1470
        # perform checks

        # Opening JSON file
        with open(self.projecthome +  'Model/Project/Data/json/LineBookChapterVerse.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
        while loopcount > 0:
            loopcount -= 1
            print(f"Loop Count: {str(loopcount)}")
            print(f"Combo Book: {self.ui.VersebookComboBox.currentText()} Combo Chapter: {str(self.ui.VersechapterComboBox.currentText())} Combo Verse: {self.ui.VerseverseComboBox.currentText()}")
            cursor3.movePosition(cursor3.PreviousBlock, cursor3.MoveAnchor)

            for Verse in data:
                if loopcount == 0:
                    pass
                elif Verse['Book'] == self.ui.VersebookComboBox.currentText() and str(Verse['Chapter']) == str(self.ui.VersechapterComboBox.currentText()) and str(Verse['Verse']) == str(self.ui.VerseverseComboBox.currentText()):
                    cursor3.movePosition(cursor3.StartOfBlock, cursor3.MoveAnchor)
                    #cursor3.movePosition(cursor3.NextWord, cursor3.MoveAnchor)
                    cursor3.movePosition(cursor3.StartOfWord, cursor3.MoveAnchor)
                    #cursor3.movePosition(cursor3.EndOfWord, cursor3.KeepAnchor)
                    cursor3.movePosition(cursor3.NextWord, cursor3.KeepAnchor,3)
                    cursor3.movePosition(cursor3.StartOfWord, cursor3.KeepAnchor)
                    cursor3.movePosition(cursor3.EndOfWord, cursor3.KeepAnchor)
                    self.lastversepos = cursor3.position()
                    bcv = cursor3.selectedText()
                    print(f"Selected First Word: {bcv}")
                    self.lastversebook = Verse['Book']
                    self.lastversechapter = str(Verse['Chapter'])
                    self.lastverseverse = str(Verse['Verse'])
                    #self.lastverseline = str(Verse['Line'])
                    if bcv == f"{self.lastversebook} {self.lastversechapter}:{self.lastverseverse}":
                        self.lastverse = self.lastversebook + " " + self.lastversechapter + ":" + self.lastverseverse
                        print(f"Book: {Verse['Book']} Chapter: {str(Verse['Chapter'])} Verse: {str(Verse['Verse'])}")
                    loopcount = 0
                #else:
                    #print("unable to identify previous block")

        f.close()'''

    def selectBookCombo(self):
        oldbookabbr = self.bothbookabbr
        self.bothbookabbr = self.ui.bookComboBox.currentText()

        if self.ui.bookComboBox.currentText() != oldbookabbr:

            jsonfile = self.booksmarkdown

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == self.bothbookabbr:
                        bookmarkdown = BookAbbr['BookMarkdown']
                        self.sourcebookmarkdown = 'source'+bookmarkdown
                        self.greekbookmarkdown = 'greek'+bookmarkdown
                        self.latinbookmarkdown = 'latin'+bookmarkdown
                        print(bookmarkdown,self.sourcebookmarkdown,self.greekbookmarkdown,self.latinbookmarkdown)
            f.close()

            '''jsonfile = self.projecthome +  'Model/Project/Data/json/Session.json'

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                bothbookabbr_key = r"self.bothbookabbr"
                source_book_markdown_key = r"self.sourcebookmarkdown"
                greek_book_markdown_key = r"self.greekbookmarkdown"
                latin_book_markdown_key = r"self.latinbookmarkdown"

                for Setting in data:
                    if Setting['Setting'] == bothbookabbr_key:
                        Setting['CurrentValue'] = self.bookabbr
                    elif Setting['Setting'] == source_book_markdown_key:
                        Setting['CurrentValue'] = self.sourcebookmarkdown
                    elif Setting['Setting'] == greek_book_markdown_key:
                        Setting['CurrentValue'] = self.greekbookmarkdown
                    elif Setting['Setting'] == latin_book_markdown_key:
                        Setting['CurrentValue'] = self.latinbookmarkdown
                    print(Setting['CurrentValue'])
            f.close()'''

            os.remove(jsonfile)
            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()

            # Opening JSON file
            '''with open(self.booksabbr) as f:
                # returns JSON object as
                    # a dictionary
                data = json.load(f)'''

            #self.ui.bookComboBox.clear()

            # Iterating through the json
            # list
            '''for booknumber in data:
                print(booknumber['bookabbr'])
                self.ui.bookComboBox.addItem(booknumber['bookabbr'])

            # Closing file
            f.close()'''

        self.ui.bookComboBox.setCurrentText(self.bothbookabbr)
        self.refbookabbr = self.ui.bookComboBox.currentText()
        self.refbooknum = self.ui.bookComboBox.currentIndex() + 40
        self.refbookindex = self.ui.bookComboBox.currentIndex()
        self.refbookcount = self.ui.bookComboBox.count()

        self.versebookabbr = self.ui.bookComboBox.currentText()
        self.versebookindex = self.ui.bookComboBox.currentIndex()
        self.versebooknum = self.refbookindex + 40
        self.versebookcount = self.ui.bookComboBox.count()

    def loadChapterCombo(self):
        self.ui.chapterComboBox.clear()
        # Opening JSON file
        with open(self.bookchapter) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
        for Chapter in data:
            if Chapter['Book'] == self.ui.bookComboBox.currentText():
                self.ui.chapterComboBox.addItem(str(Chapter['Chapter']))
        # Closing file
        f.close()

        #self.ui.bookComboBox.setEditText(self.bookabbr)
        self.refchapter = self.ui.chapterComboBox.currentText()
        self.refchapternum = int(self.refchapter)
        self.refchaptercount = self.ui.chapterComboBox.count()

        self.versechapter = self.ui.chapterComboBox.currentText()
        self.versechapternum = int(self.versechapter)
        self.versechaptercount = self.ui.chapterComboBox.count()

    def loadVerseCombo(self):
        self.ui.verseComboBox.clear()

        # Opening JSON file
        with open(self.bookchapterverse) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for Verse in data:
            if Verse['Book'] == self.ui.bookComboBox.currentText() and str(Verse['Chapter']) == self.ui.chapterComboBox.currentText():
                self.ui.verseComboBox.addItem(str(Verse["Verse"]))
        # Closing file
        f.close()
        #self.loadLineCombo()

    def resolvercount(self):
            # Get the text currently in selection
            self.selected_verseverse = self.ui.VerseText.textCursor().selectedText()
            self.selected_refverse = self.ui.RefText.textCursor().selectedText()


            # Split the text to get the word count
            self.verseverse_words = len(self.selected_verseverse.split())
            self.refverse_words = len(self.selected_refverse.split())

            # And just get the length of the text for the symbols
            # count
            self.verseverse_symbols = len(self.selected_verseverse)
            self.refverse_symbols = len(self.selected_refverse)

            # For the total count, same thing as above but for the
            # total text
            versetext = self.VerseText.toPlainText()
            reftext = self.parent.ui.RefText.toPlainText()

            self.versewords = len(versetext.split())
            self.refwords = len(reftext.split())

            self.versesymbols = len(versetext)
            self.refsymbols = len(reftext)

    def OpenResolver(self):
        print("Starting up QT5ResolveVariants")
        script = os.path.join(self.mod_abspath, "ViewController", "0-MainUI", "Qt5ResolveVariants.py")
        print(f'Launching: {sys.executable} {script}')
        try:
            subprocess.Popen([sys.executable, script], close_fds=True)
        except Exception as e:
            qtw.QMessageBox.warning(self, "Launch failed", f"Failed to launch resolver: {e}")

    '''def popupbox(self):

        popup = qtw.QMessageBox(self)
        popup.setIcon(qtw.QMessageBox.Warning)
        popup.setText(f"Resolving current word {word}")
        #popup.setInformativeText("Do you want to preserve this record?")
        #popup.setStandardButtons(qtw.QMessageBox.Save   |
                                #qtw.QMessageBox.Cancel |
                                #qtw.QMessageBox.Discard)
        #popup.setDefaultButton(qtw.QMessageBox.Save)
        popup.exec_()
        answer = popup.exec_()
        if answer == qtw.QMessageBox.Save:
            #self.save()
            print("check preserved check box and add unresolved variant to database")
        elif answer == qtw.QMessageBox.Discard:
            #event.accept()
            print("Select replacement word and replace, or type over word")
            print("Uncheck preserved check box")
        else:
            print("Nevermind. Moving on")
            stopresolver = True
            break'''

    def loadVarWordCombo(self):
        #helper = SqliteHelper("~/Projects/Python/SQLite/TRBibleWords.db")
        helper = SqliteHelper(self.projecthome + self.sqldir + "/TRiBibleWords.db")
        varwords = helper.select("SELECT DISTINCT NoDiaWord FROM Bible ORDER BY NoDiaWord")
        #print(varwords)

        for varword in varwords:
            self.varrecorder_ui.VarWordSelCombo.addItem(varword[0])

        self.selectVarWordCombo()

    def selectVarWordCombo(self):

        selvarword = self.varrecorder_ui.VarWordSelCombo.currentText()
        #helper = SqliteHelper("~/Projects/Python/SQLite/TRBibleWords.db")
        helper = SqliteHelper(self.projecthome + self.sqldir + "/TRiBibleWords.db")
        varwords = helper.select("SELECT DISTINCT NoDiaWord,Strong,RMAC,Lemma FROM Bible WHERE NoDiaWord =" + "'" + selvarword + "'")

        # This is only a partial solution.  It locks onto the first match only.

        varfields = varwords[0]

        print(varfields[0])

    def loadReplaceWordCombo(self):
        #helper = SqliteHelper("~/Projects/Python/SQLite/TRBibleWords.db")
        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        replacewords = helper.select("SELECT DISTINCT Word FROM Bible UNION SELECT DISTINCT Word FROM IntBibleWords ORDER BY Word ASC")
        #print(varwords)

        for repword in replacewords:
            self.varrecorder_ui.ReplaceWordSelCombo.addItem(repword[0])

        self.selectReplaceWordCombo()

    def selectReplaceWordCombo(self):

        selrepword = self.varrecorder_ui.ReplaceWordSelCombo.currentText()
        #helper = SqliteHelper("c:/users/max/Projects/Python/SQLite/TRBibleWords.db")
        helper = SqliteHelper(self.projecthome + self.sqldir + "/TRiBibleWords.db")
        repwords = helper.select("SELECT DISTINCT NoDiaWord,Strong,RMAC,Lemma FROM Bible WHERE Word =" + "'" + selrepword + "'")

        # This is only a partial solution.  It locks onto the first match only.

        #repfields = repwords[0]
        #print(repfields[0])

    def findResolverVariant(self,line,wordnum):
        if self.stoprecorder == True:
            return

        print("Check if variant already exists in Resolver. If found, populate dialog.")
        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        query = """SELECT Line, WordNum, Word, VarWord, ErrorCode, Preserved, Corrected FROM Variants
                WHERE Line = ? and WordNum = ?"""
        data = (line,wordnum)
        variant = helper.selectone(query,data)
        if not variant:
            self.varrecorder_ui.NewradioButton.setChecked(True)
        else:
            self.varrecorder_ui.ExistingradioButton.setChecked(True)
            print(f'Variant: {variant}')

            self.resline = variant[0]
            self.reswordnum = variant[1]
            resword = variant[2]
            resvarword = variant[3]
            reserrorcode = variant[4]
            respreserved = variant[5]
            rescorrected = variant[6]
            self.varrecorder_ui.VarWordSelCombo.setCurrentText(resvarword)
            self.varrecorder_ui.ReplaceWordSelCombo.setCurrentText(resword)
            self.varrecorder_ui.VariantCodeCombo.setCurrentText(reserrorcode)
            if respreserved == 1:
                self.varrecorder_ui.PreservedcheckBox.setChecked(True)
            if rescorrected == 1:
                self.varrecorder_ui.CorrectedcheckBox.setChecked(True)

    def insertResolverVariant(self,line,wordnum):
        varline = self.varrecorder_ui.VerseLinelineEdit.text()
        varbook = self.varrecorder_ui.VerseBooklineEdit.text()
        varchapter = self.varrecorder_ui.VerseChapterlineEdit.text()
        varverse = self.varrecorder_ui.VerseVerselineEdit.text()
        varwordnum = self.varrecorder_ui.VerseWordNumlineEdit.text()
        varnormword = self.varrecorder_ui.VerseNormWordlineEdit.text()
        refline = self.varrecorder_ui.RefLinelineEdit.text()
        refwordnum = self.varrecorder_ui.RefWordNumlineEdit.text()
        refvarnormword = self.varrecorder_ui.VerseNormWordlineEdit.text()
        if self.stoprecorder == True:
            return
        print(f'Inserting new variant for line: {line} and word number: {wordnum}')
        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        query = """SELECT Line, WordNum, Word FROM Bible
                WHERE Line = ? and WordNum = ?"""
        data = (varline,varwordnum)
        variant = helper.selectone(query,data)
        print(f'Variant: {variant}')
        verseline = variant[0]
        versewordnum = variant[1]
        verseword = variant[2]

        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        query = """SELECT Line, WordNum, Word, Strong, RMAC, Lemma FROM IntBibleWords
                WHERE Line = ? and WordNum = ?"""
        data = (refline,refwordnum)
        variant = helper.selectone(query,data)
        print(f'Variant: {variant}')

        refline = variant[0]
        refwordnum = variant[1]
        refword = variant[2]
        refstrong = variant[3]
        refrmac = variant[4]
        reflemma = variant[5]

        errorcode = self.varrecorder_ui.VariantCodeCombo.currentText()
        preserved = 0
        Corrected = 0
        if self.varrecorder_ui.PreservedcheckBox.isChecked():
            preserved = 1
        if self.varrecorder_ui.CorrectedcheckBox.isChecked():
            Corrected = 1
        varword = self.varrecorder_ui.VarWordSelCombo.currentText()
        verseword = self.varrecorder_ui.ReplaceWordSelCombo.currentText()

        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        query = """INSERT INTO Variants (Line, Book, Chapter, Verse, WordNum, Word, NoDiaWord, VarWord, Strong, RMAC, Lemma, ErrorCode, Preserved, Corrected) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        data = (varline,varbook,varchapter,varverse,varwordnum,verseword,varnormword,varword,refstrong,refrmac,reflemma,errorcode,preserved,Corrected)
        #startProgressBar()
        helper.insert(query,data)

    def updateResolverVariant(self,line,wordnum):
        if self.stoprecorder == True:
            return
        print('Updating existing variant')
        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        query = """SELECT Line, WordNum, Word, VarWord, ErrorCode, Preserved, Corrected FROM Variants
                WHERE Line = ? and WordNum = ?"""
        data = (line,wordnum)
        variant = helper.selectone(query,data)
        print(f'Variant: {variant}')

        resline = variant[0]
        reswordnum = variant[1]
        resword = variant[2]
        resvarword = variant[3]
        reserrorcode = variant[4]
        respreserved = variant[5]
        rescorrected = variant[6]
        pckvar = ""
        cckvar = ""
        preserved = 0
        Corrected= 0
        if respreserved == 1:
            resword = self.varrecorder_ui.VerseWordlineEdit.text()
            if self.varrecorder_ui.PreservedcheckBox.isChecked():
                preserved = 1
                pckvar="P"
            else:
                preserved = 0
                pckvar = ""
        if rescorrected == 1:
            resword = self.varrecorder_ui.ReplaceWordSelCombo.currentText()
            if self.varrecorder_ui.CorrectedcheckBox.isChecked():
                Corrected = 1
                cckvar = "C"
            else:
                Corrected= 0
                cckvar = ""
        resvarword = self.varrecorder_ui.VarWordSelCombo.currentText()
        varform = pckvar + cckvar
        query = """UPDATE Variants SET Word = ?, VarWord = ?, ErrorCode = ?, Preserved = ?, Corrected = ?
                WHERE Line = ? and WordNum = ?"""
        data = (resword,resvarword,reserrorcode,preserved,Corrected,resline,reswordnum)
        #startProgressBar()
        helper.update(query,data)

    def VarianceRecorderDialog(self):
        self.stoprecorder = False
        def accept():
            print("VARIANT ACCEPTED!!!!!!")
            if self.varrecorder_ui.ExistingradioButton.isChecked():
                print("Updating existing variant in Resolver")
                self.updateResolverVariant(self.resline,self.reswordnum)
            elif self.varrecorder_ui.NewradioButton.isChecked():
                print("Adding new variant to Resolver")
                self.insertResolverVariant(self.resline,self.reswordnum)

        '''def add():
            if self.varrecorder_ui.NewradioButton.isChecked():
                print("Adding new variant to Resolver")
                self.insertResolverVariant(self.resline,self.reswordnum)'''

        def close():
            print("Closing Resolver")
            self.stoprecorder = True
            self.VariantRecorderDialog.close()
            reject()

        def reject():
            print("Moving on")
            #self.contresolver = True

        '''def update():
            print("VARIANT ACCEPTED!!!!!!")
            if self.varrecorder_ui.ExistingradioButton.isChecked():
                self.updateResolverVariant(self.resline,self.reswordnum)'''

        self.VariantRecorderDialog = qtw.QDialog()
        self.varrecorder_ui = Ui_RecorderDialog()
        self.varrecorder_ui.setupUi(self.VariantRecorderDialog)
        self.VariantRecorderDialog.show()
        self.varrecorder_ui.buttonBox.accepted.connect(accept)
        self.varrecorder_ui.buttonBox.rejected.connect(reject)
        self.varrecorder_ui.ClosepushButton.clicked.connect(close)
        self.varrecorder_ui.RefLinelineEdit.setText(self.ui.ReflineComboBox.currentText())
        self.varrecorder_ui.RefBooklineEdit.setText(self.ui.RefbookComboBox.currentText())
        self.varrecorder_ui.RefChapterlineEdit.setText(self.ui.RefchapterComboBox.currentText())
        self.varrecorder_ui.RefVerselineEdit.setText(self.ui.RefverseComboBox.currentText())
        self.varrecorder_ui.RefWordNumlineEdit.setText(self.ui.RefWordNumlineEdit.text())
        self.varrecorder_ui.RefNormWordlineEdit.setText(self.ui.RefText.textCursor().selectedText())
        self.loadVarWordCombo()
        helper = SqliteHelper(self.projecthome + self.sqldir + "/TRiBibleWords.db")
        refwords = helper.select("SELECT Line, Book, Chapter, Verse, WordNum, Word FROM Bible")
        for word in refwords:
            refline = word[0]
            refbook = word[1]
            refchapter = word[2]
            refverse = word[3]
            refwordnum = word[4]
            refword = word[5]
            if str(refline) == self.varrecorder_ui.RefLinelineEdit.text() and str(refwordnum) == self.varrecorder_ui.RefWordNumlineEdit.text():
                self.varrecorder_ui.RefWordlineEdit.setText(refword)
                self.varrecorder_ui.VarWordSelCombo.setCurrentText(refword)
        self.varrecorder_ui.VerseLinelineEdit.setText(self.ui.VerselineComboBox.currentText())
        self.varrecorder_ui.VerseBooklineEdit.setText(self.ui.VersebookComboBox.currentText())
        self.varrecorder_ui.VerseChapterlineEdit.setText(self.ui.VersechapterComboBox.currentText())
        self.varrecorder_ui.VerseVerselineEdit.setText(self.ui.VerseverseComboBox.currentText())
        self.varrecorder_ui.VerseWordNumlineEdit.setText(self.ui.VerseWordNumlineEdit.text())
        self.varrecorder_ui.VerseNormWordlineEdit.setText(self.ui.VerseText.textCursor().selectedText())

        self.loadReplaceWordCombo()
        #helper = SqliteHelper("c:/users/max/Projects/Python/SQLite/TRBibleWords.db")
        helper = SqliteHelper(self.projecthome + self.sqldir + "/FROMVS.db")
        versewords = helper.select("SELECT Line, Book, Chapter, Verse, WordNum, Word FROM Bible")
        for word in versewords:
            self.verseline = word[0]
            versebook = word[1]
            versechapter = word[2]
            verseverse = word[3]
            self.versewordnum = word[4]
            verseword = word[5]
            self.varrecorder_ui.ReplaceWordSelCombo.setCurrentText(verseword)
            if str(self.verseline) == self.varrecorder_ui.VerseLinelineEdit.text() and str(self.versewordnum) == self.varrecorder_ui.VerseWordNumlineEdit.text():
                self.varrecorder_ui.VerseWordlineEdit.setText(verseword)
                self.findResolverVariant(self.verseline,self.versewordnum)
                self.VariantRecorderDialog.exec()
                #print(str(f'Next Verse Num: {self.nextverseversenum}'))

    def VarianceRecorder(self):
        self.stoprecorder = False

        if not self.ui.VerseNormcheckBox.isChecked():
            print("Normalized verse text is required for variant resolution")

        if not self.ui.RefNormcheckBox.isChecked():
            print("Normalized reference text is required for variant resolution")

        elif self.ui.VerseNormcheckBox.isChecked():
            self.ui.bookComboBox.setCurrentText("Mat")
            self.ui.chapterComboBox.setCurrentText("1")
            self.ui.verseComboBox.setCurrentText("1")
            self.findBothVerse()

        self.verseversecount = self.ui.VerseDocument.blockCount()
        self.refversecount = self.ui.ReferenceDocument.blockCount()

        if self.refversecount >= self.verseversecount:
            self.versecount = self.verseversecount
        elif self.refversecount < self.verseversecount:
            self.versecount = self.refversecount

        versecursor = self.ui.VerseText.textCursor()
        refcursor = self.ui.RefText.textCursor()
        self.initverse = True
        self.stoprecorder = False

        for x in range(self.versecount):
            if self.initverse == True:
                versecursor.setPosition(0)
                versecursor.setPosition(versecursor.Start)
            elif self.initverse == False:
                versecursor.movePosition(versecursor.NextBlock, versecursor.MoveAnchor)
            versecursor.movePosition(versecursor.StartOfBlock,versecursor.MoveAnchor)
            versecursor.movePosition(versecursor.NextWord, versecursor.MoveAnchor)
            versecursor.movePosition(versecursor.EndOfBlock, versecursor.KeepAnchor)
            self.ui.VerseText.setTextCursor(versecursor)
            self.selected_verseverse = versecursor.selectedText()
            print(f'Selected Verse verse: {self.selected_verseverse}')
            self.versewords = []
            self.versewords = self.selected_verseverse.split()
            self.versewordcount = len(self.versewords)
            print(f'Verse verse words: {self.versewords} Verse verse word count: {str(self.versewordcount)}')
            versecursor.movePosition(versecursor.StartOfBlock,versecursor.MoveAnchor)
            #print(f'Verse versecursor start of first Verse verse position: {str(versecursor.position())}')
            versecursor.movePosition(versecursor.NextWord, versecursor.MoveAnchor)
            versecursor.movePosition(versecursor.StartOfWord, versecursor.MoveAnchor)
            versecursor.movePosition(versecursor.EndOfWord, versecursor.KeepAnchor)
            self.ui.VerseText.setTextCursor(versecursor)
            #print(f'Verse versecursor start of first verse word position: {str(versecursor.position())}')
            self.versewordnum = 1
            self.ui.VerseWordNumlineEdit.setText(str(self.versewordnum))


            if self.initverse == True:
                refcursor.setPosition(0)
                refcursor.setPosition(refcursor.Start)
            elif self.initverse == False:
                refcursor.movePosition(refcursor.NextBlock, refcursor.MoveAnchor)
            refcursor.movePosition(refcursor.StartOfBlock,refcursor.MoveAnchor)
            refcursor.movePosition(refcursor.NextWord, refcursor.MoveAnchor)
            refcursor.movePosition(refcursor.EndOfBlock, refcursor.KeepAnchor)
            self.ui.RefText.setTextCursor(refcursor)
            self.selected_refverse = refcursor.selectedText()
            print(f'Selected Reference verse: {self.selected_refverse}')
            self.refwords = []
            self.refwords = self.selected_refverse.split()
            self.refwordcount = len(self.refwords)
            print(f'Reference ref words: {self.refwords} Reference ref word count: {str(self.refwordcount)}')
            refcursor.movePosition(refcursor.StartOfBlock,refcursor.MoveAnchor)
            #print(f'Reference refcursor start of first ref verse position: {str(refcursor.position())}')
            refcursor.movePosition(refcursor.NextWord, refcursor.MoveAnchor)
            refcursor.movePosition(refcursor.StartOfWord, refcursor.MoveAnchor)
            refcursor.movePosition(refcursor.EndOfWord, refcursor.KeepAnchor)
            self.refword = refcursor.selectedText()
            self.ui.RefText.setTextCursor(refcursor)
            #print(f'Reference versecursor start of first ref word position: {str(refcursor.position())}')
            self.refwordnum = 1
            self.ui.RefWordNumlineEdit.setText(str(self.refwordnum))

            if self.initverse == True:
                self.initverse = False

            #if versewordcount == refwordcount:
                #print('Additions anticipated')
                # Since there are extra ref words,
            for word in self.versewords:
                print("Running Resolver")
                #self.versebook = self.ui.VersebookComboBox.currentText()
                #self.refbook = self.ui.RefbookComboBox.currentText()
                #self.refchapter = self.ui.RefchapterComboBox.currentText()
                self.refwordnum += 1
                self.findNextRefWord()
                self.ui.RefWordNumlineEdit.setText(str(self.refwordnum))
                self.refword = self.ui.RefText.textCursor().selectedText()
                self.versewordnum += 1
                self.findNextVerseWord()
                self.ui.VerseWordNumlineEdit.setText(str(self.versewordnum))
                self.verseword = self.ui.VerseText.textCursor().selectedText()
                print(f'Verse wordnum: {str(self.versewordnum)} Verse word: {self.verseword} Ref wordnum: {str(self.refwordnum)} Ref word: {self.refword}')
                #if self.versebook == self.refbook and self.versechapter == self.refchapter and self.verseversenum ==  self.refversenum and self.verseword != self.refword:
                if self.stoprecorder == True:
                    print("Stopping the Variant Recorder")
                    return

                if self.verseword != self.refword:
                    self.VarianceRecorderDialog()

                    #if self.VariantRecorderDialog.Accepted == True:
                        #  accept()
                    #elif: self.VariantRecorderDialog.Rejected == True:
                        #reject()

            #if self.stoprecorder == True:
                #print("Stopping the Variant Recorder")
                #break
            self.verseversenum = int(self.ui.VerseverseComboBox.currentText())
            self.nextverseversenum = int(self.ui.VerseverseComboBox.currentText()) + 1
            print(str(f'Next Verse Num: {self.nextverseversenum}'))

            self.ui.VersebookComboBox.setCurrentText(str(self.versebook))
            self.ui.VersechapterComboBox.setCurrentText(str(self.versechapter))
            self.ui.VerseverseComboBox.setCurrentText(str(self.nextverseversenum))

            self.ui.RefbookComboBox.setCurrentText(str(self.versebook))
            self.ui.RefchapterComboBox.setCurrentText(str(self.versechapter))
            self.ui.RefverseComboBox.setCurrentText(str(self.nextverseversenum))

            self.ui.bookComboBox.setCurrentText(self.ui.VersebookComboBox.currentText())
            self.ui.chapterComboBox.setCurrentText(self.ui.VersechapterComboBox.currentText())
            self.ui.verseComboBox.setCurrentText(self.ui.VerseverseComboBox.currentText())

            print(str(f'Next Verse Num: {self.nextverseversenum}'))
            #self.findVerseVerse()
            self.findBothVerse()

    def selectVerseBookCombo(self):
        oldbookabbr = self.versebookabbr
        self.versebookabbr = self.ui.VersebookComboBox.currentText()

        if self.ui.VersebookComboBox.currentText() != oldbookabbr:

            jsonfile = self.booksmarkdown

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == self.versebookabbr:
                        bookmarkdown = BookAbbr['BookMarkdown']
                        self.sourcebookmarkdown = 'source'+bookmarkdown
                        self.greekbookmarkdown = 'greek'+bookmarkdown
                        self.latinbookmarkdown = 'latin'+bookmarkdown
                        print(bookmarkdown,self.sourcebookmarkdown,self.greekbookmarkdown,self.latinbookmarkdown)
            f.close()

            SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
                'self.versebookabbr': self.versebookabbr,
                'self.sourcebookmarkdown': self.sourcebookmarkdown,
                'self.greekbookmarkdown': self.greekbookmarkdown,
                'self.latinbookmarkdown': self.latinbookmarkdown,
            })

            # Opening JSON file
            '''with open(self.booksabbr) as f:
                # returns JSON object as
                    # a dictionary
                data = json.load(f)'''

            #self.ui.VersebookComboBox.clear()

            # Iterating through the json
            # list
            '''for booknumber in data:
                print(booknumber['bookabbr'])
                self.ui.VersebookComboBox.addItem(booknumber['bookabbr'])

            # Closing file
            f.close()'''

        self.ui.VersebookComboBox.setCurrentText(self.versebookabbr)
        '''self.refbookabbr = self.ui.bookComboBox.currentText()
        self.refbooknum = self.ui.bookComboBox.currentIndex() + 40
        self.refbookindex = self.ui.bookComboBox.currentIndex()
        self.refbookcount = self.ui.bookComboBox.count()'''
        self.versebookabbr = self.ui.VersebookComboBox.currentText()
        self.versebookindex = self.ui.VersebookComboBox.currentIndex()
        self.versebooknum = self.refbookindex + 40
        self.versebookcount = self.ui.VersebookComboBox.count()

    def loadVerseChapterCombo(self):
        self.ui.VersechapterComboBox.clear()
        # Opening JSON file
        with open(self.bookchapter) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
        for Chapter in data:
            if Chapter['Book'] == self.ui.VersebookComboBox.currentText():
                self.ui.VersechapterComboBox.addItem(str(Chapter['Chapter']))
        # Closing file
        f.close()

        #self.ui.VersebookComboBox.setEditText(self.bookabbr)
        self.versechapter = self.ui.VersechapterComboBox.currentText()
        self.versechapternum = int(self.versechapter)
        self.versechaptercount = self.ui.VersechapterComboBox.count()

    def loadVerseVerseCombo(self):
        self.ui.VerseverseComboBox.clear()

        # Opening JSON file
        with open(self.bookchapterverse) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for Verse in data:
            if Verse['Book'] == self.ui.VersebookComboBox.currentText() and str(Verse['Chapter']) == self.ui.VersechapterComboBox.currentText():
                self.ui.VerseverseComboBox.addItem(str(Verse["Verse"]))
        # Closing file
        f.close()

    def loadVerseLineCombo(self):
        self.ui.VerselineComboBox.clear()

        # Opening JSON file
        with open(self.linebookchapterverse) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for Line in data:
            if Line['Book'] == self.ui.VersebookComboBox.currentText() and str(Line['Chapter']) == self.ui.VersechapterComboBox.currentText():
                self.ui.VerselineComboBox.addItem(str(Line["Line"]))
        # Closing file
        f.close()
        #self.updateVerseLineCombo()

    def updateVerseLineCombo(self):
        #self.ui.VerselineComboBox.clear()
        # Opening JSON file
        with open(self.linebookchapterverse) as f:
            # returns JSON object as a dictionary
            data = json.load(f)

        # Iterating through the json list
        for Line in data:
            if Line['Book'] == self.ui.VersebookComboBox.currentText() and str(Line['Chapter']) == self.ui.VersechapterComboBox.currentText() and str(Line['Verse']) == self.ui.VerseverseComboBox.currentText():
                self.ui.VerselineComboBox.setCurrentText(str(Line["Line"]))
                #self.ui.VerseverseComboBox.setCurrentText(str(Line["Verse"]))
                self.verseline = str(Line["Line"])
                #self.findVerseVerse()

        # Closing file
        f.close()

    def selectRefBookCombo(self):
        oldbookabbr = self.refbookabbr
        self.refbookabbr = self.ui.RefbookComboBox.currentText()

        if self.ui.RefbookComboBox.currentText() != oldbookabbr:

            jsonfile = self.booksmarkdown

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == self.refbookabbr:
                        bookmarkdown = BookAbbr['BookMarkdown']
                        self.sourcebookmarkdown = 'source'+bookmarkdown
                        self.greekbookmarkdown = 'greek'+bookmarkdown
                        self.latinbookmarkdown = 'latin'+bookmarkdown
                        print(bookmarkdown,self.sourcebookmarkdown,self.greekbookmarkdown,self.latinbookmarkdown)
            f.close()

            SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
                'self.bookabbr': self.refbookabbr,
                'self.sourcebookmarkdown': self.sourcebookmarkdown,
                'self.greekbookmarkdown': self.greekbookmarkdown,
                'self.latinbookmarkdown': self.latinbookmarkdown,
            })

            # Opening JSON file
            '''with open(self.booksabbr) as f:
                # returns JSON object as
                    # a dictionary
                data = json.load(f)'''

            #self.ui.RefbookComboBox.clear()

            # Iterating through the json
            # list
            '''for booknumber in data:
                print(booknumber['bookabbr'])
                self.ui.RefbookComboBox.addItem(booknumber['bookabbr'])

            # Closing file
            f.close()'''

        self.ui.RefbookComboBox.setCurrentText(self.refbookabbr)
        self.refbookabbr = self.ui.RefbookComboBox.currentText()
        self.refbooknum = self.ui.RefbookComboBox.currentIndex() + 40
        self.refbookindex = self.ui.RefbookComboBox.currentIndex()
        self.refbookcount = self.ui.RefbookComboBox.count()

    def loadRefChapterCombo(self):
        self.ui.RefchapterComboBox.clear()
        # Opening JSON file
        with open(self.bookchapter) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
        for Chapter in data:
            if Chapter['Book'] == self.ui.RefbookComboBox.currentText():
                self.ui.RefchapterComboBox.addItem(str(Chapter['Chapter']))
        # Closing file
        f.close()

        #self.ui.RefbookComboBox.setEditText(self.bookabbr)
        self.refchapter = self.ui.RefchapterComboBox.currentText()
        self.refchapternum = int(self.refchapter)
        self.refchaptercount = self.ui.RefchapterComboBox.count()

    def loadRefVerseCombo(self):
        self.ui.RefverseComboBox.clear()

        # Opening JSON file
        with open(self.bookchapterverse) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for Verse in data:
            if Verse['Book'] == self.ui.RefbookComboBox.currentText() and str(Verse['Chapter']) == self.ui.RefchapterComboBox.currentText():
                self.ui.RefverseComboBox.addItem(str(Verse["Verse"]))
        # Closing file
        f.close()
        #self.loadRefLineCombo()

    def loadRefLineCombo(self):
        self.ui.ReflineComboBox.clear()

        # Opening JSON file
        with open(self.linebookchapterverse) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for Line in data:
            if Line['Book'] == self.ui.RefbookComboBox.currentText() and str(Line['Chapter']) == self.ui.RefchapterComboBox.currentText():
                self.ui.ReflineComboBox.addItem(str(Line["Line"]))
        # Closing file
        f.close()
        #self.updateRefLineCombo()

    def updateRefLineCombo(self):
        #self.ui.ReflineComboBox.clear()
        # Opening JSON file
        with open(self.linebookchapterverse) as f:
            # returns JSON object as a dictionary
            data = json.load(f)

        # Iterating through the json list
        for Line in data:
            if Line['Book'] == self.ui.RefbookComboBox.currentText() and str(Line['Chapter']) == self.ui.RefchapterComboBox.currentText() and str(Line['Verse']) == self.ui.RefverseComboBox.currentText():
                #self.ui.RefverseComboBox.setCurrentText(str(Line["Verse"]))
                self.ui.ReflineComboBox.setCurrentText(str(Line["Line"]))
                self.refline = self.ui.ReflineComboBox.currentText()
                #self.findRefVerse()
        # Closing file
        f.close()

    def bothLoad(self):
        ''' load the matching file for either the current image or the current text '''
        def accept():
            #if self.ImageTextPairDialog.Accepted:
            if self.ImageTextPairDialog_ui.MatchTxt2Imgbutton.isChecked():
                print("matching text file to current image file")
                print(self.imgpath)
                if self.imgpath:
                    print("finding matched text file for " + self.imgpath)
                    imgfilename = self.imgpath
                    file = qtc.QFile(imgfilename)
                    filestr = os.path.basename(imgfilename)
                    filedir = os.path.dirname(imgfilename)
                    filesplit = os.path.splitext(filestr)
                    filename = filesplit[0]
                    fileext = filesplit[1]
                    namesplit = filename.split("_")
                    versionref = namesplit[0]
                    pagestr = namesplit[2]
                    pagenum = int(pagestr)
                    print(self.versedir +r"/"+ versionref + "_Page_" + pagestr + r".txt")
                else:
                    print(self.imgpath + " does not exist")

                self.trytxtpath = self.versedir +r"/"+ versionref + "_Page_" + pagestr + r".txt"
                if self.trytxtpath:
                    print("opening " + self.trytxtpath)
                    self.versepath = self.trytxtpath
                    self.showText(self.versepath)
                    #self.ReloadText()
                else:
                    print(self.trytxtpath + " does not exist")

            elif self.ImageTextPairDialog_ui.MatchImg2Txtbutton.isChecked():
                print("matching image file to current text file")
                print(self.versepath)
                if self.versepath:
                    print("finding matched image file for " + self.versepath)
                    txtfilename = self.versepath
                    file = qtc.QFile(txtfilename)
                    filestr = os.path.basename(txtfilename)
                    filedir = os.path.dirname(txtfilename)
                    filesplit = os.path.splitext(filestr)
                    filename = filesplit[0]
                    fileext = filesplit[1]
                    namesplit = filename.split("_")
                    versionref = namesplit[0]
                    pagestr = namesplit[2]
                    pagenum = int(pagestr)
                    print(self.imgdir +r"/"+ versionref + "_Page_" + pagestr + r".tif")
                else:
                    print(self.versepath + " does not exist")

                self.tryimgpath = self.imgdir +r"/"+ versionref + "_Page_" + pagestr + r".tif"
                if self.tryimgpath:
                    print("opening " + self.tryimgpath)
                    self.imgpath = self.tryimgpath
                    self.showImage(self.imgpath)
                else:
                    print(self.tryimgpath + " does not exist")


        def reject():
            pass

        self.ImageTextPairDialog = qtw.QDialog()
        self.ImageTextPairDialog_ui.setupUi(self.ImageTextPairDialog)
        self.ImageTextPairDialog.show()

        self.ImageTextPairDialog_ui.buttonBox.accepted.connect(accept)
        self.ImageTextPairDialog_ui.buttonBox.rejected.connect(reject)

    def findVerseBook(self):
        findversebook = self.ui.VersebookComboBox.currentText() + " "
        print(f'find book = {findversebook}')
        cursor = self.ui.VerseText.textCursor()
        cursor.setPosition(0)
        self.ui.VerseText.setTextCursor(cursor)
        self.ui.VerseText.verticalScrollBar().setValue(self.ui.VerseText.verticalScrollBar().maximum())
        #if not self.ui.VerseText.find(verseverse):
        versebookfound = self.ui.VerseText.find(findversebook)
        if versebookfound:
            self.versebook = self.ui.VersebookComboBox.currentText()
            self.versebookindex = self.ui.VersebookComboBox.currentIndex()
            #self.ui.VerseText.setTextCursor(cursor)
            #self.ui.VerseText.find(verseverse)
            print(f'found = {findversebook}')
            self.versebookcount = self.ui.VersebookComboBox.count()
            self.prevversebookindex = str(int(self.versebookindex) - 1)
            self.nextversebookindex = str(int(self.versebookindex) + 1)
            #comment out the line of code below to highlight the entire verse
            #self.ui.VerseText.moveCursor(cursor.EndOfBlock, cursor.KeepAnchor)
            print(f'self.versebook = {self.versebook}')
            print(f'self.versebookindex = {self.versebookindex}')
            print(f'self.versebookcount = {self.versebookcount}')
            print(f'self.prevversebookindex = {self.prevversebookindex}')
            print(f'self.nextversebookindex = {self.nextversebookindex}')
        else:
            print(f'Unable to find verse book: {findversebook}')
        self.ui.VersebookComboBox.setCurrentIndex(self.versebookindex)
        self.ui.VersechapterComboBox.setCurrentText("1")
        self.ui.VerseverseComboBox.setCurrentText("1")
        self.findVerseVerse()

    def findNextVerseBook(self):
        self.ui.VersebookComboBox.setCurrentIndex(self.ui.VersebookComboBox.currentIndex() + 1)
        self.findVerseBook()

    def findPrevVerseBook(self):
        self.ui.VersebookComboBox.setCurrentIndex(self.ui.VersebookComboBox.currentIndex() - 1)
        self.findVerseBook()

    def findVerseChapter(self):
        versebook = self.ui.VersebookComboBox.currentText()
        print(f' versebook: {versebook}')
        self.versechapter = self.ui.VersechapterComboBox.currentText()
        print(self.versechapter)
        findversechapter = self.versebook + " " + self.ui.VersechapterComboBox.currentText() + ":"
        print(f'find verse chapter = {findversechapter}')
        cursor = self.ui.VerseText.textCursor()
        cursor.setPosition(0)
        self.ui.VerseText.setTextCursor(cursor)
        self.ui.VerseText.verticalScrollBar().setValue(self.ui.VerseText.verticalScrollBar().maximum())
        versechapterfound = self.ui.VerseText.find(findversechapter)
        if versechapterfound:
            self.versechapter = self.ui.VersechapterComboBox.currentText()
            print(f'found verse chapter = {findversechapter}')
            self.versechaptercount = self.ui.VersechapterComboBox.count()
            print(f'self.versechapter = {self.versechapter}')
            print(f'self.versechaptercount = {self.versechaptercount}')
        else:
            print(f'Unable to find verse chapter: {findversechapter}')
        self.ui.VersebookComboBox.setCurrentText(versebook)
        self.ui.VersechapterComboBox.setCurrentText(self.versechapter)
        self.ui.VerseverseComboBox.setCurrentText("1")
        self.findVerseVerse()

    def findNextVerseChapter(self):
        self.ui.VersechapterComboBox.setCurrentText(str(int(self.ui.VersechapterComboBox.currentText()) + 1))
        versechapternum = int(self.ui.VersechapterComboBox.currentText())
        versechapter = self.ui.VersechapterComboBox.currentText()
        versechaptercount =  self.ui.VersechapterComboBox.count()
        nextversechapternum = int(self.ui.VersechapterComboBox.currentText()) + 1
        # Opening JSON file
        with open(self.booksabbrnamenumindex) as f:
            # returns JSON object as a dictionary
            books = json.load(f)
        # Iterating through the json list
        for book in books:
            versebookabbr = str(book["bookabbr"])
            if versebookabbr == self.ui.VersebookComboBox.currentText():
                versebookindex = int(book["bookindex"])
                versebook = str(book["bookabbr"])
                nextversebookindex = versebookindex + 1
        # Closing json file
        f.close()
        nextversebook = self.ui.VersebookComboBox.itemText(nextversebookindex)
        versebookcount = self.ui.VersebookComboBox.count()
        print(f'Verse Chapter Count: {versechaptercount} Verse Chapter Num: {versechapternum} Next Verse Chapter Num: {nextversechapternum}')
        print(f'versebookindex: {versebookindex} versebook: {versebook} nextversebookindex: {nextversebookindex} nextversebook: {nextversebook}')
        if versechapternum > versechaptercount:
            self.ui.VersebookComboBox.setCurrentText(versebook)
            self.ui.VersechapterComboBox.setCurrentText("1")
            self.ui.VerseverseComboBox.setCurrentText("1")
            self.versechapter = versechapter
            if nextversechapternum > versechaptercount:
                self.ui.VersebookComboBox.setCurrentText(nextversebook)
                self.ui.VersechapterComboBox.setCurrentText("1")
                self.ui.VerseverseComboBox.setCurrentText("1")

        self.findVerseChapter()

    def findPrevVerseChapter(self):
        self.ui.VersechapterComboBox.setCurrentText(str(int(self.ui.VersechapterComboBox.currentText()) - 1))
        versechapternum = int(self.ui.VersechapterComboBox.currentText())
        versechapter = self.ui.VersechapterComboBox.currentText()
        versechaptercount =  self.ui.VersechapterComboBox.count()
        prevversechapternum = int(self.ui.VersechapterComboBox.currentText()) - 1
        # Opening JSON file
        with open(self.booksabbrnamenumindex) as f:
            # returns JSON object as a dictionary
            books = json.load(f)
        # Iterating through the json list
        for book in books:
            versebookabbr = str(book["bookabbr"])
            if versebookabbr == self.ui.VersebookComboBox.currentText():
                versebookindex = int(book["bookindex"])
                versebook = str(book["bookabbr"])
                prevversebookindex = versebookindex - 1
        # Closing json file
        f.close()
        prevversebook = self.ui.VersebookComboBox.itemText(prevversebookindex)
        versebookcount = self.ui.VersebookComboBox.count()
        print(f'Verse Chapter Num: {versechapternum} Prev Verse Chapter Num: {prevversechapternum}')
        print(f'versebookindex: {versebookindex} versebook: {versebook} prevversebookindex: {prevversebookindex} prevversebook: {prevversebook}')
        if versechapternum == 0:
            self.ui.VersebookComboBox.setCurrentText(versebook)
            self.ui.VersechapterComboBox.setCurrentText(str(self.ui.VersechapterComboBox.count()))
            self.ui.VerseverseComboBox.setCurrentText("1")
            self.versechapter = versechapter
            if prevversechapternum < 0:
                self.ui.VersebookComboBox.setCurrentText(str(prevversebook))
                self.ui.VersechapterComboBox.setCurrentText(str(self.ui.VersechapterComboBox.count()))
                self.ui.VerseverseComboBox.setCurrentText("1")

        self.findVerseChapter()

    def findBothVerse(self):

        if self.ui.radioButtonRef.isChecked():
            verse = self.ui.RefbookComboBox.currentText() + " " + self.ui.RefchapterComboBox.currentText() + ":" + self.ui.RefverseComboBox.currentText() + " "
        elif self.ui.radioButtonVerses.isChecked():
            verse = self.ui.VersebookComboBox.currentText() + " " + self.ui.VersechapterComboBox.currentText() + ":" + self.ui.VerseverseComboBox.currentText() + " "
        elif self.ui.radioButtonSel.isChecked():
            verse = self.ui.bookComboBox.currentText() + " " + self.ui.chapterComboBox.currentText() + ":" + self.ui.verseComboBox.currentText() + " "
        elif self.ui.AnchorCkBox.isChecked():
            verse = self.anchorbook + " " + self.anchorchapter + ":" + self.anchorverse + " "

        print(f'find both Verse verse = {verse}')

        cursor = self.ui.VerseText.textCursor()
        cursor.setPosition(0)
        self.ui.VerseText.setTextCursor(cursor)
        self.ui.VerseText.verticalScrollBar().setValue(self.ui.VerseText.verticalScrollBar().maximum())

        if self.ui.VerseNormcheckBox.isChecked():
            findline = self.ui.VerselineComboBox.currentText()
            print(f'find verse = {verse} find line = {findline}')
            linefound = self.ui.VerseText.find(findline)
            #comment out the line of code below to highlight the entire verse
            self.ui.VerseText.moveCursor(cursor.EndOfBlock, cursor.KeepAnchor)
            if linefound:
                self.verseline = self.ui.VerselineComboBox.currentText()
                #self.ui.VerseText.setTextCursor(cursor)
                #self.ui.VerseText.find(verseverse)
                print(f'found = {linefound}')
                self.verselinenum = int(self.verseline)
                self.verselinecount = self.ui.VerselineComboBox.count()
                self.prevtextversenum = str(int(self.verseversenum) - 1)
                self.nexttextversenum = str(int(self.verseversenum) + 1)
                print(f'self.verseline = {self.verseline}')
                print(f'self.verselinecount = {self.verselinecount}')
                print(f'self.prevtextversenum = {self.prevtextversenum}')
                print(f'self.nexttextversenum = {self.nexttextversenum}')
                self.ui.VerselineComboBox.setCurrentText(self.verseline)
            else:
                print(f'Unable to find verse line: {findline}')
        else:
            versefound = self.ui.VerseText.find(verse)
            if versefound:
                self.verseverse = self.ui.verseComboBox.currentText()
                print(f'find self.verseverse = {self.verseverse}')
                self.verseversenum = int(self.verseverse)
                self.verseversecount = self.ui.verseComboBox.count()
                self.prevtextversenum = str(int(self.verseverse) - 1)
                self.nexttextversenum = str(int(self.verseverse) + 1)
                #comment out the line of code below to highlight the entire verse
                #self.ui.VerseText.moveCursor(cursor.EndOfBlock, cursor.KeepAnchor)
                print(f'self.verseverse = {self.verseverse}')
                print(f'self.verseversenum = {self.verseversenum}')
                print(f'self.verseversecount = {self.verseversecount}')
                print(f'self.prevtextversenum = {self.prevtextversenum}')
                print(f'self.nexttextversenum = {self.nexttextversenum}')
            else:
                print(f'Unable to find verse: {findline}')
        #self.ui.VerselineComboBox.setCurrentText(self.verseline)

        print(f'find both Ref verse = {verse}')
        refcursor = self.ui.RefText.textCursor()
        refcursor.setPosition(0)
        self.ui.RefText.setTextCursor(refcursor)
        self.ui.RefText.verticalScrollBar().setValue(self.ui.RefText.verticalScrollBar().maximum())

        if self.ui.RefNormcheckBox.isChecked():
            findline = self.ui.ReflineComboBox.currentText()
            print(f'find verse = {verse} find line = {findline}')
            linefound = self.ui.RefText.find(findline)
            #comment out the line of code below to highlight the entire verse
            self.ui.RefText.moveCursor(refcursor.EndOfBlock, refcursor.KeepAnchor)
            if linefound:
                self.refline = self.ui.ReflineComboBox.currentText()
                #self.ui.RefText.setTextCursor(cursor)
                #self.ui.RefText.find(refverse)
                print(f'found = {linefound}')
                self.reflinenum = int(self.refline)
                self.reflinecount = self.ui.ReflineComboBox.count()
                self.prevtextrefnum = str(int(self.refversenum) - 1)
                self.nexttextrefnum = str(int(self.refversenum) + 1)

                print(f'self.refline = {self.refline}')
                print(f'self.reflinecount = {self.reflinecount}')
                print(f'self.prevrefversenum = {self.prevrefversenum}')
                print(f'self.nextrefversenum = {self.nextrefversenum}')
                self.ui.ReflineComboBox.setCurrentText(self.refline)
            else:
                print(f'Unable to find ref verse line: {findline}')

        else:
            refversefound = self.ui.RefText.find(verse)
            if refversefound:
                self.refverse = self.ui.verseComboBox.currentText()
                print(f'find self.refverse = {self.refverse}')
                self.refversenum = int(self.refverse)
                self.refversecount = self.ui.verseComboBox.count()
                self.prevrefversenum = str(int(self.refverse) - 1)
                self.nextrefversenum = str(int(self.refverse) + 1)

                #refcursor.EndOfLine()
                print(f'self.refverse = {self.refverse}')
                print(f'self.refversenum = {self.refversenum}')
                print(f'self.refversecount = {self.refversecount}')
                print(f'self.prevrefversenum = {self.prevrefversenum}')
                print(f'self.nextrefversenum = {self.nextrefversenum}')
            else:
                print(f'Unable to find ref verse: {refversefound}')

        #self.ui.ReflineComboBox.setCurrentText(self.refline)

        self.ui.VersebookComboBox.setCurrentText(self.ui.bookComboBox.currentText())
        self.ui.VersechapterComboBox.setCurrentText(self.ui.chapterComboBox.currentText())
        self.ui.VerseverseComboBox.setCurrentText(self.ui.verseComboBox.currentText())
        self.updateVerseLineCombo()
        self.versebook = self.ui.bookComboBox.currentText()
        self.versebookindex = self.ui.bookComboBox.currentIndex()
        self.versechapter = self.ui.chapterComboBox.currentText()
        self.versechapterindex = self.ui.chapterComboBox.currentIndex()

        self.ui.RefbookComboBox.setCurrentText(self.ui.bookComboBox.currentText())
        self.ui.RefchapterComboBox.setCurrentText(self.ui.chapterComboBox.currentText())
        self.ui.RefverseComboBox.setCurrentText(self.ui.verseComboBox.currentText())
        self.updateRefLineCombo()
        self.refbook = self.ui.bookComboBox.currentText()
        self.refbookindex = self.ui.bookComboBox.currentIndex()
        self.refchapter = self.ui.chapterComboBox.currentText()
        self.refchapterindex = self.ui.chapterComboBox.currentIndex()

        self.updateSessionBothVerse()

    def updateBothVerse(self):
            self.ui.bookComboBox.setCurrentText(self.ui.VersebookComboBox.currentText())
            self.ui.chapterComboBox.setCurrentText(self.ui.VersechapterComboBox.currentText())
            self.ui.verseComboBox.setCurrentText(self.ui.VerseverseComboBox.currentText())
            self.book = self.ui.VersebookComboBox.currentText()
            self.bookindex = self.ui.VersebookComboBox.currentIndex()
            self.bookchapter = self.ui.VersechapterComboBox.currentText()
            self.bookverse = self.ui.VersechapterComboBox.currentText()

    def updateSessionBothVerse(self):
        print(f'Updating the both verse session settings')
        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.bothbookabbr': self.bothbookabbr,
            'self.bothchapter': self.bothchapter,
            'self.bothverse': self.bothverse,
        })

    def findVerseVerse(self):

        #self.verseversenum = self.refversenum
        findverse = self.ui.VersebookComboBox.currentText() + " " + self.ui.VersechapterComboBox.currentText() + ":" + self.ui.VerseverseComboBox.currentText() + " "
        findline = self.ui.VerselineComboBox.currentText()
        print(f'find verse = {findverse} find line = {findline}')
        cursor = self.ui.VerseText.textCursor()
        cursor.setPosition(0)
        self.ui.VerseText.setTextCursor(cursor)
        self.ui.VerseText.verticalScrollBar().setValue(self.ui.VerseText.verticalScrollBar().maximum())
        if self.ui.VerseNormcheckBox.isChecked():
            linefound = self.ui.VerseText.find(findline)
            #comment out the line of code below to highlight the entire verse
            self.ui.VerseText.moveCursor(cursor.EndOfBlock, cursor.KeepAnchor)
            if linefound:
                self.verseline = self.ui.VerselineComboBox.currentText()
                #self.ui.VerseText.setTextCursor(cursor)
                #self.ui.VerseText.find(verseverse)
                print(f'found = {linefound}')
                self.verselinenum = int(self.verseline)
                self.verselinecount = self.ui.VerselineComboBox.count()
                self.prevtextversenum = str(int(self.verseversenum) - 1)
                self.nexttextversenum = str(int(self.verseversenum) + 1)
                print(f'self.verseline = {self.verseline}')
                print(f'self.verselinecount = {self.verselinecount}')
                print(f'self.prevtextversenum = {self.prevtextversenum}')
                print(f'self.nexttextversenum = {self.nexttextversenum}')
            else:
                print(f'Unable to find verse line: {findline}')
            self.ui.VerselineComboBox.setCurrentText(self.verseline)
        else:
            versefound = self.ui.VerseText.find(findverse)
            if versefound:
                self.verseverse = self.ui.VerseverseComboBox.currentText()
                #self.ui.VerseText.setTextCursor(cursor)
                #self.ui.VerseText.find(verseverse)
                print(f'found = {findverse}')
                self.verseversenum = int(self.verseverse)
                self.verseversecount = self.ui.VerseverseComboBox.count()
                self.prevtextversenum = str(int(self.verseversenum) - 1)
                self.nexttextversenum = str(int(self.verseversenum) + 1)
                #comment out the line of code below to highlight the entire verse
                #self.ui.VerseText.moveCursor(cursor.EndOfBlock, cursor.KeepAnchor)
                print(f'self.verseverse = {self.verseverse}')
                print(f'self.verseversenum = {self.verseversenum}')
                print(f'self.verseversecount = {self.verseversecount}')
                print(f'self.prevtextversenum = {self.prevtextversenum}')
                print(f'self.nexttextversenum = {self.nexttextversenum}')
            else:
                print(f'Unable to find verse verse: {findverse}')
            self.ui.VerseverseComboBox.setCurrentText(self.verseverse)

        self.versebook = self.ui.VersebookComboBox.currentText()
        self.versebookindex = self.ui.VersebookComboBox.currentIndex()
        self.versechapter = self.ui.VersechapterComboBox.currentText()
        self.versechapterindex = self.ui.VersechapterComboBox.currentIndex()
        self.updateSessionVerseVerse()

    def updateSessionVerseVerse(self):
        print(f'Updating the verse text session settings')
        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.versebookabbr': self.versebookabbr,
            'self.versechapter': self.versechapter,
            'self.verseverse': self.verseverse,
            'self.verseline': self.ui.VerselineComboBox.currentText(),
        })

    def findNextVerseVerse(self):
        self.ui.VerseverseComboBox.setCurrentText(str(int(self.ui.VerseverseComboBox.currentText()) + 1))
        verseversenum = int(self.ui.VerseverseComboBox.currentText())
        nextverseversenum = int(self.ui.VerseverseComboBox.currentText()) + 1
        nextversechapter = int(self.ui.VersechapterComboBox.currentText()) + 1
        versebook = self.ui.VersebookComboBox.currentText()
        versebookindex = self.ui.VersebookComboBox.currentIndex()
        nextversebookindex = self.ui.VersebookComboBox.currentIndex() + 1
        versechaptercount = self.ui.VersechapterComboBox.count()
        print(f'Next Text Verse: {nextverseversenum}')
        if verseversenum == self.ui.VerseverseComboBox.count() + 1:
            self.ui.VersebookComboBox.setCurrentText(versebook)
            self.ui.VersechapterComboBox.setCurrentText(str(nextversechapter))
            self.ui.VerseverseComboBox.setCurrentText("1")
            self.versechapter = str(nextversechapter)
            if nextversechapter > versechaptercount:
                self.ui.VersebookComboBox.setCurrentIndex(nextversebookindex)
                self.ui.VersechapterComboBox.setCurrentText("1")
                self.ui.VerseverseComboBox.setCurrentText("1")
        self.updateVerseLineCombo()
        self.findVerseVerse()

    def findPrevVerseVerse(self):
        self.ui.VerseverseComboBox.setCurrentText(str(int(self.ui.VerseverseComboBox.currentText()) - 1))
        verseversenum = int(self.ui.VerseverseComboBox.currentText())
        prevverseversenum = int(self.ui.VerseverseComboBox.currentText()) - 1
        prevversechapter = int(self.ui.VersechapterComboBox.currentText()) - 1
        versechapter = int(self.ui.VersechapterComboBox.currentText())
        versebook = self.ui.VersebookComboBox.currentText()
        versebookindex = self.ui.VersebookComboBox.currentIndex()
        prevversebook =  self.ui.VersebookComboBox.itemText(versebookindex)
        print(f'Prev Text Verse: {prevverseversenum}')
        print(f'Text Chapter: {versechapter}')
        print(f'Prev Text Chapter: {prevversechapter}')
        print(f'Prev Verse Book: {prevversebook}')
        if verseversenum == 0:
            self.ui.VersebookComboBox.setCurrentText(versebook)
            self.ui.VersechapterComboBox.setCurrentText(str(prevversechapter))
            self.ui.VerseverseComboBox.setCurrentText(str(self.ui.VerseverseComboBox.count()))
            self.versechapter = str(prevversechapter)
            if prevversechapter == 0:
                self.ui.VersebookComboBox.setCurrentText(prevversebook)
                versechaptercount = self.ui.VersechapterComboBox.count()
                self.ui.VersechapterComboBox.setCurrentText(str(versechaptercount))
                self.ui.VerseverseComboBox.setCurrentText(str(self.ui.VerseverseComboBox.count()))
        self.updateVerseLineCombo()
        self.findVerseVerse()

    def updateVerseVerseRegEx(self):
        self.refword = self.ui.RefText.textCursor().selectedText()
        print(self.refword)
        txtfile = open(self.refpath)
        csv_f = csv.reader(txtfile, delimiter = "\t")
        #print(csv_f)
        # Parse lines of biblical text(tab delimited) as a csv with regexp
        for row in csv_f:
            #print(row[0])

            # Each line is a verse => parse and label each book chapter:verse reference

            rowline = row[0]
            textline = rowline.replace("\n","")
            #fbook, fchapt, fverse, fscrip  = (row[0], row[1], row[2], row[3])
            pattern = re.compile('(\w+\s)(\d+:)(\d+\s)')
            matches = pattern.finditer(textline)
            for match in matches:
                    #print(match)
                    if match[0] == self.refword:
                        book = match[1]
                        self.ui.RefbookComboBox.setCurrentText(book)
                        print(book)
                        chcolon = match[2]
                        chapter = str(chcolon.replace(":","")).strip()
                        self.ui.RefchapterComboBox.setCurrentText(chapter)
                        print(chapter)
                        verse = str(match[3]).strip()
                        self.ui.RefverseComboBox.setCurrentText(verse)
                        print(verse)

        txtfile.close()

    '''
    def parseLinesRegEx(self):
        #***This is the original parse routine.  Keep for reference***
        # Each line is a verse => pares and label each verse
        rowline = row[0]
        textline = rowline.replace("\n","")
        #fbook, fchapt, fverse, fscrip  = (row[0], row[1], row[2], row[3])
        pattern = re.compile('(\w+\s)(\d+:)(\d+\s)(.*)')
        matches = pattern.finditer(textline)
        for match in matches:
            book = match[1]
            chcolon = match[2]
            chapter = chcolon.replace(":","")
            verse = match[3]
            scripture = match[4]
            #print(row[0])
            print(book,"\t", chapter,"\t", verse,"\t",scripture)
    '''
    def wordCount(self):

        wc = versifiercount.WordCount(self)

        wc.getText()

        wc.show()

    def getVerseLinePositions(self):
        cursor = self.ui.VerseText.textCursor()
        self.currentpos = cursor.position()

        cursor2 = self.ui.VerseText.textCursor()
        cursor2.setPosition(self.currentpos)

        cursor2.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        self.endofline = cursor2.position()

        cursor2.movePosition(cursor.PreviousWord, cursor.KeepAnchor)
        self.lastwordstart = cursor2.position()

        cursor2.movePosition(cursor.EndOfWord, cursor.KeepAnchor)
        self.lastwordend = cursor2.position()

        cursor2.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        self.startofline = cursor2.position()
        self.bookwordstart = self.startofline
        '''cursor2.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor2.movePosition(cursor.NextWord, cursor.MoveAnchor)
        cursor2.movePosition(cursor.StartOfWord, cursor.MoveAnchor)
        self.bookwordstart = cursor2.position()
        cursor2.movePosition(cursor.EndOfWord,cursor.MoveAnchor )
        self.bookwordend = cursor2.position()'''
        cursor2.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        if self.ui.VerseNormcheckBox.isChecked():
            cursor2.movePosition(cursor.NextWord, cursor.MoveAnchor,1)
        else:
            cursor2.movePosition(cursor.NextWord, cursor.MoveAnchor,4)
        cursor2.movePosition(cursor.StartOfWord, cursor.MoveAnchor)
        self.firstwordstart = cursor2.position()

        cursor2.movePosition(cursor.EndOfWord, cursor.KeepAnchor)
        self.firstwordend = cursor2.position()

        print(f'current position: {self.currentpos} start of line: {self.startofline} first word start: {self.firstwordstart} first word end: {self.firstwordend}')
        print(f'end of line: {self.endofline} last word start: {self.lastwordstart} last word end: {self.lastwordend}')

    def findNextVerseWord(self):
        self.getVerseLinePositions()
        cursor = self.ui.VerseText.textCursor()
        print(f'previous word: {cursor.selectedText()}')
        if cursor.position() <= self.firstwordstart:
            cursor.setPosition(self.firstwordstart - 1)
        if cursor.position() >= self.endofline:
            self.findNextVerseVerse()
            self.getVerseLinePositions()
            cursor.setPosition(self.firstwordstart - 1)
        cursor.movePosition(cursor.NextWord,cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfWord,cursor.KeepAnchor)
        self.ui.VerseText.setTextCursor(cursor)
        self.verseword = cursor.selectedText()
        print(f'selected word: {self.verseword}')

    def findPrevVerseWord(self):
        self.getVerseLinePositions()
        cursor = self.ui.VerseText.textCursor()
        print(f'previous word: {cursor.selectedText()}')

        if cursor.selectedText() == self.verseword:
            cursor.setPosition(cursor.position() - 1)

        if cursor.position() <= self.firstwordend:
            self.findPrevVerseVerse()
            self.getVerseLinePositions()
            print(f'cursor position after findPreviousVerse: {cursor.position()}')
            cursor.setPosition(self.endofline)
            print(f'cursor position at endofline: {cursor.position()}')
            #cursor.movePosition(cursor.NextWord,cursor.MoveAnchor)
            #self.ui.VerseText.setTextCursor(cursor)
        if cursor.position() != self.endofline:
            cursor.movePosition(cursor.StartOfWord,cursor.MoveAnchor)
        cursor.movePosition(cursor.PreviousWord,cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfWord,cursor.KeepAnchor)
        self.ui.VerseText.setTextCursor(cursor)
        self.verseword = cursor.selectedText()
        print(f'selected position: {cursor.position()} selected word: {self.verseword}')

    def findRefBook(self):
        findrefbook = self.ui.RefbookComboBox.currentText() + " "
        print(f'find book = {findrefbook}')
        cursor = self.ui.RefText.textCursor()
        cursor.setPosition(0)
        self.ui.RefText.setTextCursor(cursor)
        self.ui.RefText.verticalScrollBar().setValue(self.ui.RefText.verticalScrollBar().maximum())
        refbookfound = self.ui.RefText.find(findrefbook)
        if refbookfound:
            self.refbook = self.ui.RefbookComboBox.currentText()
            self.refbookindex = self.ui.RefbookComboBox.currentIndex()
            #self.ui.VerseText.setTextCursor(cursor)
            #self.ui.VerseText.find(refverse)
            print(f'found = {findrefbook}')
            self.refbookcount = self.ui.RefbookComboBox.count()
            self.prevrefbookindex = str(int(self.refbookindex) - 1)
            self.nextrefbookindex = str(int(self.refbookindex) + 1)
            #comment out the line of code below to highlight the entire verse
            #self.ui.VerseText.moveCursor(cursor.EndOfBlock, cursor.KeepAnchor)
            print(f'self.refbook = {self.refbook}')
            print(f'self.refbookindex = {self.refbookindex}')
            print(f'self.refbookcount = {self.refbookcount}')
            print(f'self.prevrefbookindex = {self.prevrefbookindex}')
            print(f'self.nextrefbookindex = {self.nextrefbookindex}')
        else:
            print(f'Unable to find verse book: {findrefbook}')
        self.ui.RefbookComboBox.setCurrentIndex(self.refbookindex)
        self.ui.RefchapterComboBox.setCurrentText("1")
        self.ui.RefverseComboBox.setCurrentText("1")
        self.findRefVerse()

    def findNextRefBook(self):
        self.ui.RefbookComboBox.setCurrentIndex(self.ui.RefbookComboBox.currentIndex() + 1)
        self.findRefBook()

    def findPrevRefBook(self):
        self.ui.RefbookComboBox.setCurrentIndex(self.ui.RefbookComboBox.currentIndex() - 1)
        self.findRefBook()

    def findRefChapter(self):
        refbook = self.ui.RefbookComboBox.currentText()
        print(f' refbook: {refbook}')
        self.refchapter = self.ui.RefchapterComboBox.currentText()
        print(self.refchapter)
        findrefchapter = self.refbook + " " + self.ui.RefchapterComboBox.currentText() + ":"
        print(f'find ref chapter = {findrefchapter}')
        refcursor = self.ui.RefText.textCursor()
        refcursor.setPosition(0)
        self.ui.RefText.setTextCursor(refcursor)
        self.ui.RefText.verticalScrollBar().setValue(self.ui.RefText.verticalScrollBar().maximum())
        refchapterfound = self.ui.RefText.find(findrefchapter)
        if refchapterfound:
            self.refchapter = self.ui.RefchapterComboBox.currentText()
            print(f'found ref chapter = {findrefchapter}')
            self.refchaptercount = self.ui.RefchapterComboBox.count()
            print(f'self.refchapter = {self.refchapter}')
            print(f'self.refchaptercount = {self.refchaptercount}')
        else:
            print(f'Unable to find ref chapter: {findrefchapter}')
        self.ui.RefbookComboBox.setCurrentText(refbook)
        self.ui.RefchapterComboBox.setCurrentText(self.refchapter)
        self.ui.RefverseComboBox.setCurrentText("1")
        self.findRefVerse()

    def findNextRefChapter(self):
        self.ui.RefchapterComboBox.setCurrentText(str(int(self.ui.RefchapterComboBox.currentText()) + 1))
        refchapternum = int(self.ui.RefchapterComboBox.currentText())
        refchapter = self.ui.RefchapterComboBox.currentText()
        refchaptercount =  self.ui.RefchapterComboBox.count()
        nextrefchapternum = int(self.ui.RefchapterComboBox.currentText()) + 1
        # Opening JSON file
        with open(self.booksabbrnamenumindex) as f:
            # returns JSON object as a dictionary
            books = json.load(f)
        # Iterating through the json list
        for book in books:
            refbookabbr = str(book["bookabbr"])
            if refbookabbr == self.ui.RefbookComboBox.currentText():
                refbookindex = int(book["bookindex"])
                refbook = str(book["bookabbr"])
                nextrefbookindex = refbookindex + 1
        # Closing json file
        f.close()
        nextrefbook = self.ui.RefbookComboBox.itemText(nextrefbookindex)
        refbookcount = self.ui.RefbookComboBox.count()
        print(f'Ref Chapter Count: {refchaptercount} Ref Chapter Num: {refchapternum} Next Ref Chapter Num: {nextrefchapternum}')
        print(f'refbookindex: {refbookindex} refbook: {refbook} nextrefbookindex: {nextrefbookindex} nextrefbook: {nextrefbook}')
        if refchapternum > refchaptercount:
            self.ui.RefbookComboBox.setCurrentText(refbook)
            self.ui.RefchapterComboBox.setCurrentText("1")
            self.ui.RefverseComboBox.setCurrentText("1")
            self.refchapter = refchapter
            if nextrefchapternum > refchaptercount:
                self.ui.RefbookComboBox.setCurrentText(nextrefbook)
                self.ui.RefchapterComboBox.setCurrentText("1")
                self.ui.RefverseComboBox.setCurrentText("1")

        self.findRefChapter()

    def findPrevRefChapter(self):
        self.ui.RefchapterComboBox.setCurrentText(str(int(self.ui.RefchapterComboBox.currentText()) - 1))
        refchapternum = int(self.ui.RefchapterComboBox.currentText())
        refchapter = self.ui.RefchapterComboBox.currentText()
        refchaptercount =  self.ui.RefchapterComboBox.count()
        prevrefchapternum = int(self.ui.RefchapterComboBox.currentText()) - 1
        # Opening JSON file
        with open(self.booksabbrnamenumindex) as f:
            # returns JSON object as a dictionary
            books = json.load(f)
        # Iterating through the json list
        for book in books:
            refbookabbr = str(book["bookabbr"])
            if refbookabbr == self.ui.RefbookComboBox.currentText():
                refbookindex = int(book["bookindex"])
                refbook = str(book["bookabbr"])
                prevrefbookindex = refbookindex - 1
        # Closing json file
        f.close()
        prevrefbook = self.ui.RefbookComboBox.itemText(prevrefbookindex)
        refbookcount = self.ui.RefbookComboBox.count()
        print(f'Ref Chapter Num: {refchapternum} Prev Ref Chapter Num: {prevrefchapternum}')
        print(f'refbookindex: {refbookindex} refbook: {refbook} prevrefbookindex: {prevrefbookindex} prevrefbook: {prevrefbook}')
        if refchapternum == 0:
            self.ui.RefbookComboBox.setCurrentText(refbook)
            self.ui.RefchapterComboBox.setCurrentText(str(self.ui.RefchapterComboBox.count()))
            self.ui.RefverseComboBox.setCurrentText("1")
            self.refchapter = refchapter
            if prevrefchapternum < 0:
                self.ui.RefbookComboBox.setCurrentText(str(prevrefbook))
                self.ui.RefchapterComboBox.setCurrentText(str(self.ui.RefchapterComboBox.count()))
                self.ui.RefverseComboBox.setCurrentText("1")

        self.findRefChapter()

    def findRefVerse(self):
        findverse = self.ui.RefbookComboBox.currentText() + " " + self.ui.RefchapterComboBox.currentText() + ":" + self.ui.RefverseComboBox.currentText() + " "
        findline = self.ui.ReflineComboBox.currentText()
        print(f'find ref verse = {findverse}')
        refcursor = self.ui.RefText.textCursor()
        refcursor.setPosition(0)
        self.ui.RefText.setTextCursor(refcursor)
        self.ui.RefText.verticalScrollBar().setValue(self.ui.RefText.verticalScrollBar().maximum())

        if self.ui.RefNormcheckBox.isChecked():
            linefound = self.ui.RefText.find(findline)
            #comment out the line of code below to highlight the entire verse
            self.ui.RefText.moveCursor(refcursor.EndOfBlock, refcursor.KeepAnchor)
            if linefound:
                self.refline = self.ui.ReflineComboBox.currentText()
                #self.ui.RefText.setTextCursor(cursor)
                #self.ui.RefText.find(refverse)
                print(f'found = {linefound}')
                self.reflinenum = int(self.refline)
                self.reflinecount = self.ui.ReflineComboBox.count()
                self.prevtextrefnum = str(int(self.refversenum) - 1)
                self.nexttextrefnum = str(int(self.refversenum) + 1)
                print(f'self.refline = {self.refline}')
                print(f'self.reflinecount = {self.reflinecount}')
                print(f'self.prevrefversenum = {self.prevrefversenum}')
                print(f'self.nextrefversenum = {self.nextrefversenum}')
            else:
                print(f'Unable to find verse line: {findline}')
            self.ui.ReflineComboBox.setCurrentText(self.refline)
        else:
            reffound = self.ui.RefText.find(findverse)
            if reffound:
                self.refverse = self.ui.RefverseComboBox.currentText()
                #self.ui.RefText.setTextCursor(refcursor)
                #self.ui.RefText.find(refverse)
                print(f'found = {findverse}')
                self.refversenum = int(self.refverse)
                self.refversecount = self.ui.RefverseComboBox.count()
                self.prevrefversenum = str(int(self.refversenum) - 1)
                self.nextrefversenum = str(int(self.refversenum) + 1)

                #refcursor.EndOfLine()
                print(f'self.refverse = {self.refverse}')
                print(f'self.refversenum = {self.refversenum}')
                print(f'self.refversecount = {self.refversecount}')
                print(f'self.prevrefversenum = {self.prevrefversenum}')
                print(f'self.nextrefversenum = {self.nextrefversenum}')
            else:
                print(f'Unable to find ref verse: {findverse}')
            self.ui.RefverseComboBox.setCurrentText(self.refverse)
        #self.updateRefLineCombo()
        self.refbook = self.ui.RefbookComboBox.currentText()
        self.refbookindex = self.ui.RefbookComboBox.currentIndex()
        self.refchapter = self.ui.RefchapterComboBox.currentText()
        self.refchapterindex = self.ui.RefchapterComboBox.currentIndex()
        self.updateSessionRefVerse()

    def updateSessionRefVerse(self):
        print(f'Updating the reference text session settings')
        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.refbookabbr': self.refbookabbr,
            'self.refchapter': self.refchapter,
            'self.refverse': self.refverse,
            'self.refline': self.ui.VerselineComboBox.currentText(),
        })

    def findNextRefVerse(self):
        self.ui.RefverseComboBox.setCurrentText(str(int(self.ui.RefverseComboBox.currentText()) + 1))
        refversenum = int(self.ui.RefverseComboBox.currentText())
        nextrefversenum = int(self.ui.RefverseComboBox.currentText()) + 1
        nextrefchapter = int(self.ui.RefchapterComboBox.currentText()) + 1
        refbook = self.ui.RefbookComboBox.currentText()
        refbookindex = self.ui.RefbookComboBox.currentIndex()
        nextrefbookindex = self.ui.RefbookComboBox.currentIndex() + 1
        refchaptercount = self.ui.RefchapterComboBox.count()
        print(f'Next Ref Verse: {nextrefversenum}')
        if refversenum == self.ui.RefverseComboBox.count() + 1:
            self.ui.RefchapterComboBox.setCurrentText(str(nextrefchapter))
            self.ui.RefverseComboBox.setCurrentText("1")
            self.refchapter = str(nextrefchapter)
            if nextrefchapter > refchaptercount:
                self.ui.RefbookComboBox.setCurrentIndex(nextrefbookindex)
                self.ui.RefchapterComboBox.setCurrentText("1")
                self.ui.RefverseComboBox.setCurrentText("1")
        #self.updateRefLineCombo()
        self.findRefVerse()

    def findPrevRefVerse(self):
        self.ui.RefverseComboBox.setCurrentText(str(int(self.ui.RefverseComboBox.currentText()) - 1))
        refversenum = int(self.ui.RefverseComboBox.currentText())
        prevrefversenum = int(self.ui.RefverseComboBox.currentText()) - 1
        prevrefchapter = int(self.ui.RefchapterComboBox.currentText()) - 1
        refchapter = int(self.ui.RefchapterComboBox.currentText())
        refbook = self.ui.RefbookComboBox.currentText()
        refbookindex = self.ui.RefbookComboBox.currentIndex()
        prevrefbook =  self.ui.RefbookComboBox.itemText(refbookindex - 1)
        print(f'Prev Ref Verse: {prevrefversenum}')
        print(f'Ref Chapter: {refchapter}')
        print(f'Prev Ref Chapter: {prevrefchapter}')
        print(f'Prev Ref Book: {prevrefbook}')
        if refversenum == 0:
            self.ui.RefbookComboBox.setCurrentText(refbook)
            self.ui.RefchapterComboBox.setCurrentText(str(prevrefchapter))
            self.ui.RefverseComboBox.setCurrentText(str(self.ui.RefverseComboBox.count()))
            self.refchapter = str(prevrefchapter)
            if prevrefchapter == 0:
                self.ui.RefbookComboBox.setCurrentText(prevrefbook)
                refchaptercount = self.ui.RefchapterComboBox.count()
                self.ui.RefchapterComboBox.setCurrentText(str(refchaptercount))
                self.ui.RefverseComboBox.setCurrentText(str(self.ui.RefverseComboBox.count()))
        #self.updateRefLineCombo()
        self.findRefVerse()

    def updateRefVerse(self):
        self.refword = self.ui.RefText.textCursor().selectedText()
        print(self.refword)
        txtfile = open(self.refpath)
        csv_f = csv.reader(txtfile, delimiter = "\t")
        #print(csv_f)
        # Parse lines of biblical text(tab delimited) as a csv with regexp
        for row in csv_f:
            #print(row[0])

            # Each line is a verse => parse and label each book chapter:verse reference

            rowline = row[0]
            textline = rowline.replace("\n","")
            #fbook, fchapt, fverse, fscrip  = (row[0], row[1], row[2], row[3])
            pattern = re.compile('(\w+\s)(\d+:)(\d+\s)')
            matches = pattern.finditer(textline)
            for match in matches:
                    #print(match)
                    if match[0] == self.refword:
                        book = match[1]
                        self.ui.RefbookComboBox.setCurrentText(book)
                        print(book)
                        chcolon = match[2]
                        chapter = str(chcolon.replace(":","")).strip()
                        self.ui.RefchapterComboBox.setCurrentText(chapter)
                        print(chapter)
                        verse = str(match[3]).strip()
                        self.ui.RefverseComboBox.setCurrentText(verse)
                        print(verse)

        txtfile.close()
        #self.updateRefLineCombo()

    def findRefWord(self):
        self.refword = self.ui.RefText.textCursor.selectedText()
        self.updateRefVerse()

    def getRefLinePositions(self):
        cursor = self.ui.RefText.textCursor()
        self.currentpos = cursor.position()

        cursor2 = self.ui.RefText.textCursor()
        cursor2.setPosition(self.currentpos)

        cursor2.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        self.endofline = cursor2.position()

        cursor2.movePosition(cursor.PreviousWord, cursor.KeepAnchor)
        self.lastwordstart = cursor2.position()

        cursor2.movePosition(cursor.EndOfWord, cursor.KeepAnchor)
        self.lastwordend = cursor2.position()

        cursor2.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        self.startofline = cursor2.position()
        self.bookwordstart = self.startofline
        '''cursor2.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor2.movePosition(cursor.NextWord, cursor.MoveAnchor)
        cursor2.movePosition(cursor.StartOfWord, cursor.MoveAnchor)
        self.bookwordstart = cursor2.position()
        cursor2.movePosition(cursor.EndOfWord,cursor.MoveAnchor )
        self.bookwordend = cursor2.position()'''
        cursor2.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)

        if self.ui.RefNormcheckBox.isChecked():
            cursor2.movePosition(cursor.NextWord, cursor.MoveAnchor,1)
        else:
            cursor2.movePosition(cursor.NextWord, cursor.MoveAnchor,4)

        cursor2.movePosition(cursor.StartOfWord, cursor.MoveAnchor)
        self.firstwordstart = cursor2.position()

        cursor2.movePosition(cursor.EndOfWord, cursor.KeepAnchor)
        self.firstwordend = cursor2.position()

        print(f'current position: {self.currentpos} start of line: {self.startofline} first word start: {self.firstwordstart} first word end: {self.firstwordend}')
        print(f'end of line: {self.endofline} last word start: {self.lastwordstart} last word end: {self.lastwordend}')

    def findNextRefWord(self):
        self.getRefLinePositions()
        cursor = self.ui.RefText.textCursor()
        print(f'next word: {cursor.selectedText()}')
        if cursor.position() <= self.firstwordstart:
            cursor.setPosition(self.firstwordstart - 1)
        if cursor.position() >= self.endofline:
            self.findNextRefVerse()
            self.getRefLinePositions()
            cursor.setPosition(self.firstwordstart - 1)
        cursor.movePosition(cursor.NextWord,cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfWord,cursor.KeepAnchor)
        self.ui.RefText.setTextCursor(cursor)
        self.refword = cursor.selectedText()
        print(f'selected word: {self.refword}')

    def findPrevRefWord(self):
        self.getRefLinePositions()
        cursor = self.ui.RefText.textCursor()
        print(f'previous word: {cursor.selectedText()}')

        if cursor.selectedText() == self.refword:
            cursor.setPosition(cursor.position() - 1)

        if cursor.position() <= self.firstwordend:
            self.findPrevRefVerse()
            self.getRefLinePositions()
            print(f'cursor position after findPreviousVerse: {cursor.position()}')
            cursor.setPosition(self.endofline)
            print(f'cursor position at endofline: {cursor.position()}')
            #cursor.movePosition(cursor.NextWord,cursor.MoveAnchor)
            #self.ui.RefText.setTextCursor(cursor)
        if cursor.position() != self.endofline:
            cursor.movePosition(cursor.StartOfWord,cursor.MoveAnchor)
        cursor.movePosition(cursor.PreviousWord,cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfWord,cursor.KeepAnchor)
        self.ui.RefText.setTextCursor(cursor)
        self.refword = cursor.selectedText()
        print(f'selected position: {cursor.position()} selected word: {self.refword}')

    def OpenWithMyWriter(self):
        script = os.path.join(self.mod_abspath, "ViewController", "0-MainUI", "MyWriter.py")
        print(f'Launching: {sys.executable} {script}')
        try:
            subprocess.Popen([sys.executable, script], close_fds=True)
        except Exception as e:
            qtw.QMessageBox.warning(self, "Launch failed", f"Failed to open MyWriter: {e}")

    def OpenWithLibreCalc(self):
        lo = shutil.which('libreoffice') or shutil.which('soffice')
        if lo:
            try:
                subprocess.Popen([lo, '--calc', self.versepath], close_fds=True)
            except Exception as e:
                qtw.QMessageBox.warning(self, "Launch failed", f"Failed to open LibreOffice: {e}")
        else:
            qtw.QMessageBox.warning(self, "LibreOffice not found", "LibreOffice/soffice not found on PATH.")

    def OpenWithLibreWriter(self):
        lo = shutil.which('libreoffice') or shutil.which('soffice')
        if lo:
            try:
                subprocess.Popen([lo, '--writer', self.versepath], close_fds=True)
            except Exception as e:
                qtw.QMessageBox.warning(self, "Launch failed", f"Failed to open LibreOffice: {e}")
        else:
            qtw.QMessageBox.warning(self, "LibreOffice not found", "LibreOffice/soffice not found on PATH.")

    def on_versefont_update(self):
        # update font to selection and size
        font = qtg.QFont(self.ui.VersefontComboBox.currentFont())
        font.setPointSize(self.ui.VersefontSizeBox.value())

        self.ui.VerseText.setFont(font)

    def on_reffont_update(self):
        # update font to selection and size
        font = qtg.QFont(self.ui.ReffontComboBox.currentFont())
        font.setPointSize(self.ui.ReffontSizeBox.value())

        self.ui.RefText.setFont(font)

    def on_lang_select(self):
        pass

    def GetVerseLineSpacing(self):
        self.ui.VerseLHslider.setEnabled(True)
        self.ui.VerseLHslider.show()
        self.ui.VerseLHlineEdit.setPlaceholderText(str(self.ui.VerseLHslider.value()))

    def DisableVerseLHSlider(self):
        self.ui.VerseLHslider.hide()
        self.ui.VerseLHslider.setEnabled(False)

    def MoveVerseLHSlider(self):
        self.ui.VerseLHslider.setEnabled(True)
        self.ui.VerseLHslider.setValue(int(self.ui.VerseLHlineEdit.text()))

    def SetVerseLineSpacing(self):

        lineSpacing = self.ui.VerseLHslider.value()
        self.ui.VerseLHlineEdit.setText(str(lineSpacing))

        cursor = self.ui.VerseText.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.VerseCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.VerseBlockFormat.ProportionalHeight)
        cursor.mergeBlockFormat(bf)

    def GetRefLineSpacing(self):
        self.ui.RefLHslider.setEnabled(True)
        self.ui.RefLHslider.show()
        self.ui.RefLHlineEdit.setPlaceholderText(str(self.ui.RefLHslider.value()))

    def DisableRefLHSlider(self):
        self.ui.RefLHslider.hide()
        self.ui.RefLHslider.setEnabled(False)

    def MoveRefLHSlider(self):
        self.ui.RefLHslider.setEnabled(True)
        self.ui.RefLHslider.setValue(int(self.ui.RefLHlineEdit.text()))

    def SetRefLineSpacing(self):

        lineSpacing = self.ui.RefLHslider.value()
        self.ui.RefLHlineEdit.setText(str(lineSpacing))

        cursor = self.ui.RefText.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.ReferenceCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.ReferenceBlockFormat.ProportionalHeight)
        cursor.mergeBlockFormat(bf)

    def SaveAsVerseTextDialog(self):

        path = qtw.QFileDialog.getSaveFileName(
        self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
        filename = os.path.basename(path)

        with open(path, 'w') as file:
            my_CorrectedText = self.ui.VerseDocument.toPlainText()
            file.write(my_CorrectedText)

        self.ui.TextLE.setText(filename)
        file.close()

    def SaveVerseTextDialog(self):

        defaultdir = self.versedir + r"/"
        defaultfile = self.ui.TextLE.displayText()
        defaultpath = defaultdir + defaultfile

        if defaultpath:
            path = defaultpath
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)

        with open(path, 'w') as file:
            my_CorrectedText = self.ui.VerseDocument.toPlainText()
            file.write(my_CorrectedText)

        self.ui.TextLE.setText(filename)
        file.close()

    def _open_non_modal_text_dialog(self, title, directory, selected_handler, dialog_attr_name):
        """Open a non-modal file picker that can also be used as a drag source."""
        self.open_non_modal_text_picker(title, directory or self.projecthome, selected_handler, dialog_attr_name)

    def loadVerseText(self):
        self._open_non_modal_text_dialog(
            'Open verse text file',
            self.versedir,
            self.getVerseText,
            '_verse_open_dialog',
        )

    def getVerseText(self,textpath):
            self.versepath = textpath
            self.versedirname = os.path.dirname(self.versepath)
            #create file list
            if self.versepath:
                self._begin_visible_text_load('Verse text', self.versepath)
                try:
                    #self.ui.BoxText.setText(os.path.basename(self.txtpath))
                    self.versefile = qtc.QFile(self.versepath)
                    self.versefilename = os.path.basename(self.versepath)
                    self.versedir = os.path.dirname(self.versepath)
                    self.ui.VerseTextLE.setText(self.versefilename)
                    self.showVerseText(self.versepath)
                finally:
                    self._end_visible_text_load('Verse text')

    def showVerseText(self,textpath):
        self.versepath = textpath
        if self.versepath:
            versetext = self._read_text_file_with_progress(self.versepath, 'Verse text')
            self._startup_progress('Verse text: rendering in pane')
            self._run_with_terminal_spinner(
                'Verse text: rendering in pane',
                lambda: self.ui.VerseText.setPlainText(versetext),
            )
            self.versefilename = os.path.basename(self.versepath)
            self.versedir = os.path.dirname(self.versepath)
            self.ui.VerseTextLE.setText(self.versefilename)
            '''
            if self.versefile.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(self.versefile)
                stream.setCodec("UTF-8")
                text = stream.readAll()
                info = qtc.QFileInfo(self.versepath)
                self.ui.VerseTextLE.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text)
                    self.ui.VerseText.insertPlainText(text)
                else:
                    self.ui.VerseText.setPlainText(text)'''
            self.on_versefont_update()

            # update line spacing
            self.SetVerseLineSpacing()
            self.versefile.close()

        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.versepath': self.versepath.replace(self.projecthome, ""),
            'self.versedir': self.versedir.replace(self.projecthome, ""),
        })

        self.versetxtfileList = []
        for t in os.listdir(self.versedir):
            tpath = os.path.join(self.versedir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.versetxtfileList.append(tpath)

        self.sortVerseTextFiles()

    def ReloadVerseText(self):
        if self.versepath:
            print("Reloading "+ self.versepath)
            file = qtc.QFile(self.versepath)
            filename = os.path.basename(self.versepath)
            self.ui.VerseTextLE.setText(filename)
            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.versepath)
                self.ui.VerseText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.VerseText.insertPlainText(text)
                else:
                    self.ui.VerseText.setPlainText(text)

                # update font to selection and size
                self.on_versefont_update()

                # update line spacing
                self.SetLineSpacing()

    '''
    def loadText(self):

        self.versepath = qtw.QFileDialog.getOpenFileName(
        self.ui.centralwidget, 'Open text file',self.versedir,
        'Text files (*.txt *.csv)')[0]

        if self.versepath:
            file = qtc.QFile(self.versepath)
            filename = os.path.basename(self.versepath)
            self.versedir = os.path.dirname(self.versepath)
            self.ui.TextLE.setText(filename)
            #self.sortTextFiles(MainWindow)
            self.showText(self.versepath)
            self.sortTextFiles()
    '''
    '''
    def showText(self, txtfilename):
        #self.textfile = txtfilename
        if self.versepath and not self.ui.VerseNormcheckBox.isChecked():
            file = qtc.QFile(self.versepath)
            filename = os.path.basename(self.versepath)
            self.versedir = os.path.dirname(self.versepath)
            self.ui.TextLE.setText(filename)

            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.versepath)
                self.ui.VerseText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.VerseText.insertPlainText(text)
                else:
                    self.ui.VerseText.setPlainText(text)
            #textfile.close()
            #txtdirpath = os.path.dirname(self.textpath)

            # update font to selection and size
            self.on_versefont_update()

            # update line spacing
            self.SetLineSpacing()
            file.close()

        jsonfile = self.projecthome +  'Model/Project/Data/json/Session.json'

        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.versepath"
            txtdir_key = r"self.versedir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.versepath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:
                    Setting['CurrentValue'] = self.versedir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

        self.txtfileList = []
        for t in os.listdir(self.versedir):
            tpath = os.path.join(self.versedir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.txtfileList.append(tpath)

        self.sortTextFiles()
    '''

    def showVerseNormText(self, txtfilename):
        #self.textfile = txtfilename
        if self.versenormpath and self.ui.VerseNormcheckBox.isChecked():
            file = qtc.QFile(self.versenormpath)
            filename = os.path.basename(self.versenormpath)
            self.versenormdir = os.path.dirname(self.versenormpath)
            self.ui.TextLE.setText(filename)

            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.versepath)
                self.ui.VerseText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.VerseText.insertPlainText(text)
                else:
                    self.ui.VerseText.setPlainText(text)
            #textfile.close()
            #txtdirpath = os.path.dirname(self.textpath)

            # update font to selection and size
            self.on_versefont_update()

            # update line spacing
            self.SetLineSpacing()
            file.close()

        '''jsonfile = self.projecthome +  'Model/Project/Data/json/Session.json'

        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.versepath"
            txtdir_key = r"self.versedir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.versepath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:
                    Setting['CurrentValue'] = self.versedir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()'''

        '''self.txtfileList = []
        for t in os.listdir(self.versenormdir):
            tpath = os.path.join(self.versenormdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.txtfileList.append(tpath)

        #self.sortTextFiles()'''

    def bothNormCheckbox(self):
        if self.ui.NormcheckBox.isChecked():
            self.ui.RefNormcheckBox.setChecked(True)
            self.ui.VerseNormcheckBox.setChecked(True)
        elif not self.ui.NormcheckBox.isChecked():
            self.ui.RefNormcheckBox.setChecked(False)
            self.ui.VerseNormcheckBox.setChecked(False)

    def VerseNormalize(self):
        script = os.path.join(self.mod_abspath, "ViewController", "0-MainUI", "NormalizeVerseText.py")
        print(f'Launching: {sys.executable} {script}')
        try:
            subprocess.Popen([sys.executable, script], close_fds=True)
        except Exception as e:
            qtw.QMessageBox.warning(self, "Launch failed", f"Failed to run NormalizeVerseText: {e}")

    def sortVerseTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_reftxtfilelist = sorted(self.reftxtfileList, key=alphanum_key)

    def nextVerseText(self):
        if self.refpath:
            self.refpath = self.sorted_reftxtfilelist[(self.sorted_reftxtfilelist.index(self.textpath) + 1) % len(self.sorted_txtfilelist)]
            self.ui.RefTextLE.setText(os.path.basename(self.refpath))
            self.getRefText(self.refpath)

    def prevVerseText(self):
        if self.refpath:
            self.refpath = self.sorted_reftxtfilelist[(self.sorted_reftxtfilelist.index(self.textpath) - 1) % len(self.sorted_txtfilelist)]
            self.ui.RefTextLE.setText(os.path.basename(self.refpath))
            self.getRefText(self.refpath)

    '''
    def sortTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_txtfilelist)
        self.versedirIterator = iter(self.sorted_txtfilelist)
        self.versedirRevIterator = reversed(self.sorted_txtfilelist)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.versedirIterator) == self.versepath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.versedirRevIterator) == self.versepath:
                break

    def nextText(self):
        # ensure that the file list has not been cleared due to missing files
        filestr = os.path.basename(self.versepath)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if self.txtfileList:
            try:
                txtfile = next(self.versedirIterator)
                self.ui.TextLE.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(),
                    #QtCore.Qt.KeepAspectRatio)
                self.txtfile = qtc.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.versepath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.versepath = txtfile
                print(txtfile,"\t",self.versepath,"\t",self.txtfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.versedirIterator = iter(self.sorted_txtfilelist)
                self.versedirRevIterator = reversed(self.sorted_txtfilelist)
                self.prevText()
            self.versepath = txtfile
            self.showText(txtfile)
        else:
            # no file list found, load an image
            self.loadText()

    def prevText(self):
        # ensure that the file list has not been cleared due to missing files
        filestr = os.path.basename(self.versepath)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if self.txtfileList:
            try:
                #txtfile = self.textfile
                txtfile = next(self.versedirRevIterator)
                self.ui.TextLE.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(),
                    #QtCore.Qt.KeepAspectRatio)
                self.txtfile = qtc.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.versepath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.versepath = txtfile
                print(txtfile,"\t",self.versepath,"\t",self.txtfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.versedirRevIterator = reversed(sorted_txtfilelist)
                self.versedirIterator = iter(sorted_txtfilelist)
                self.nextText()
            self.versepath = txtfile
            self.showText(txtfile)
        else:
            # no file list found, load an image
            self.loadText()
    '''

    def loadRefText(self):
        self._open_non_modal_text_dialog(
            'Open reference text file',
            self.refdir,
            self.getRefText,
            '_ref_open_dialog',
        )

    def getRefText(self,textpath):
            self.refpath = textpath
            self.refdirname = os.path.dirname(self.refpath)
            #create file list
            if self.refpath:
                self._begin_visible_text_load('Reference text', self.refpath)
                try:
                    #self.ui.BoxText.setText(os.path.basename(self.txtpath))
                    self.reffile = qtc.QFile(self.refpath)
                    self.reffilename = os.path.basename(self.refpath)
                    self.refdir = os.path.dirname(self.refpath)
                    self.ui.RefTextLE.setText(self.reffilename)
                    self.refpath = textpath
                    self.showRefText(self.refpath)
                finally:
                    self._end_visible_text_load('Reference text')

    def showRefText(self,textpath):
        self.refpath = textpath
        self._startup_progress(f'Reference File Path: {self.refpath}')
        if self.refpath:
            reftext = self._read_text_file_with_progress(self.refpath, 'Reference text')
            self._startup_progress('Reference text: rendering in pane')
            self._run_with_terminal_spinner(
                'Reference text: rendering in pane',
                lambda: self.ui.RefText.setPlainText(reftext),
            )
            self.reffilename = os.path.basename(self.refpath)
            self.refdir = os.path.dirname(self.refpath)
            self.ui.RefTextLE.setText(self.reffilename)
            self._run_with_terminal_spinner(
                'Reference text: applying font to large document',
                self.on_reffont_update,
            )
            # update line spacing
            self._run_with_terminal_spinner(
                'Reference text: applying line spacing to large document',
                self.SetRefLineSpacing,
            )
            #self.reffile.close()

        self._startup_progress('Reference text: updating session settings')
        SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')).update('VersifierSession.json', {
            'self.refpath': self.refpath.replace(self.projecthome, ""),
            'self.refdir': self.refdir.replace(self.projecthome, ""),
        })

        self._startup_progress('Reference text: building directory file list')
        self.reftxtfileList = []
        for t in os.listdir(self.refdir):
            tpath = os.path.join(self.refdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.reftxtfileList.append(tpath)

        self._startup_progress(f'Reference text: sorting {len(self.reftxtfileList)} text files')
        self.sortRefTextFiles()
        self._startup_progress('Reference text: startup processing complete')

    '''
    def loadRefText(self):

        self.refpath = qtw.QFileDialog.getOpenFileName(
        self.ui.centralwidget, 'Open text file',self.refdir,
        'Text files (*.txt *.csv)')[0]

        if self.refpath:
            file = qtc.QFile(self.refpath)
            filename = os.path.basename(self.refpath)
            self.versedir = os.path.dirname(self.refpath)
            self.ui.RefTextLE.setText(filename)
            #self.sortTextFiles(MainWindow)
            self.showRefText()
            #self.sortRefTextFiles()
    '''
    '''

    def showRefText(self):
        print(f'Reference File Path: {self.refpath}')

        #self.refpath = txtfilename
        if self.refpath and not self.ui.RefNormcheckBox.isChecked():
            file = qtc.QFile(self.refpath)
            filename = os.path.basename(self.refpath)
            self.refdir = os.path.dirname(self.refpath)
            self.ui.RefTextLE.setText(filename)

            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.refpath)
                self.ui.RefText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text)
                    self.ui.RefText.insertPlainText(text)
                else:
                    self.ui.RefText.setPlainText(text)
            #textfile.close()
            #txtdirpath = os.path.dirname(self.textpath)

            self.on_reffont_update()

            # update line spacing
            self.SetRefLineSpacing()
            file.close()


        jsonfile = self.projecthome +  'Model/Project/Data/json/Session.json'

        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.versepath"
            txtdir_key = r"self.versedir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.versepath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:
                    Setting['CurrentValue'] = self.versedir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

        self.reftxtfileList = []
        for t in os.listdir(self.refdir):
            tpath = os.path.join(self.refdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.reftxtfileList.append(tpath)

        self.sortRefTextFiles()
    '''

    def showRefNormText(self, txtfilename):
        #self.textfile = txtfilename
        if self.refnormpath and self.ui.RefNormcheckBox.isChecked():
            self.refnormfile = qtc.QFile(self.refnormpath)
            self.refnormfilename = os.path.basename(self.refnormpath)
            self.refnormdir = os.path.dirname(self.refnormpath)
            self.ui.RefTextLE.setText(self.refnormfilename)

            if self.refnormfile.open(qtc.QIODevice.ReadOnly, encoding='UTF-8'):
                stream = qtc.QTextStream(self.refnormfile)
                text = stream.readAll()
                info = qtc.QFileInfo(self.refnormpath)
                self.ui.RefText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.RefText.insertPlainText(text)
                else:
                    self.ui.RefText.setPlainText(text)

            self.on_reffont_update()

            # update line spacing
            self.SetRefLineSpacing()
            self.refnormfile.close()

        '''jsonfile = self.projecthome +  'Model/Project/Data/json/Session.json'

        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.versepath"
            txtdir_key = r"self.versedir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.versepath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:
                    Setting['CurrentValue'] = self.versedir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()'''

        self.reftxtfileList = []
        for t in os.listdir(self.refnormdir):
            tpath = os.path.join(self.refnormdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.reftxtfileList.append(tpath)

        self.sortRefTextFiles()

    def RefNormalize(self):
        script = os.path.join(self.mod_abspath, "ViewController", "0-MainUI", "NormalizeRefText.py")
        print(f'Launching: {sys.executable} {script}')
        try:
            subprocess.Popen([sys.executable, script], close_fds=True)
        except Exception as e:
            qtw.QMessageBox.warning(self, "Launch failed", f"Failed to run NormalizeRefText: {e}")

    def sortRefTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_reftxtfilelist = sorted(self.reftxtfileList, key=alphanum_key)

    def nextRefText(self):
        if self.refpath:
            self.refpath = self.sorted_reftxtfilelist[(self.sorted_reftxtfilelist.index(self.textpath) + 1) % len(self.sorted_txtfilelist)]
            self.ui.RefTextLE.setText(os.path.basename(self.refpath))
            self.getRefText(self.refpath)

    def prevRefText(self):
        if self.refpath:
            self.refpath = self.sorted_reftxtfilelist[(self.sorted_reftxtfilelist.index(self.textpath) - 1) % len(self.sorted_txtfilelist)]
            self.ui.RefTextLE.setText(os.path.basename(self.refpath))
            self.getRefText(self.refpath)

    '''
    def sortRefTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_reftxtfilelist = sorted(self.reftxtfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_txtfilelist)
        self.reftxtdirIterator = iter(self.sorted_reftxtfilelist)
        self.reftxtdirRevIterator = reversed(self.sorted_reftxtfilelist)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.reftxtdirIterator) == self.refpath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.reftxtdirRevIterator) == self.refpath:
                break

    def nextRefText(self):
        # ensure that the file list has not been cleared due to missing files
        filestr = os.path.basename(self.refpath)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if self.reftxtfileList:
            try:
                reftxtfile = next(self.reftxtdirIterator)
                self.ui.RefTextLE.setText(os.path.basename(reftxtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(),
                    #QtCore.Qt.KeepAspectRatio)
                self.reftxtfile = qtc.QFile(reftxtfile)
                self.reftxtfilename = os.path.basename(reftxtfile)
                self.refdirname = os.path.dirname(self.refpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.refpath = reftxtfile
                print(reftxtfile,"\t",self.refpath,"\t",self.reftxtfile,"\t",self.reftxtfilename)
                #print(self.txtfilename)
                self.showText(self.reftxtfilename)
            except:
                # the iterator has finished, restart it
                self.reftxtdirIterator = iter(self.sorted_reftxtfilelist)
                self.reftxtdirRevIterator = reversed(self.sorted_reftxtfilelist)
                self.prevRefText()
            self.refpath = reftxtfile
            self.showText(txtfile)
        else:
            # no file list found, load an image
            self.loadRefText()

    def prevRefText(self):
        # ensure that the file list has not been cleared due to missing files
        filestr = os.path.basename(self.refpath)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if self.reftxtfileList:
            try:
                #txtfile = self.textfile
                txtfile = next(self.reftxtdirRevIterator)
                self.ui.TextLE.setText(os.path.basename(reftxtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(),
                    #QtCore.Qt.KeepAspectRatio)
                self.reftxtfile = qtc.QFile(reftxtfile)
                self.reftxtfilename = os.path.basename(reftxtfile)
                self.refdirname = os.path.dirname(self.refpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.refpath = reftxtfile
                print(reftxtfile,"\t",self.refpath,"\t",self.reftxtfile,"\t",self.reftxtfilename)
                #print(self.txtfilename)
                self.showText(self.reftxtfilename)
            except:
                # the iterator has finished, restart it
                self.reftxtdirRevIterator = reversed(sorted_reftxtfilelist)
                self.reftxtdirIterator = iter(sorted_reftxtfilelist)
                self.nextRefText()
            self.refpath = reftxtfile
            self.showText(reftxtfile)
        else:
            # no file list found, load an image
            self.loadRefText()
    '''

    def ReloadRefText(self):
        if self.refpath:
            print("Reloading "+ self.refpath)
            self.reffile = qtc.QFile(self.refpath)
            self.reffilename = os.path.basename(self.refpath)
            self.ui.RefTextLE.setText(self.reffilename)
            if self.reffile.open(qtc.QIODevice.ReadOnly, encoding = 'UTF-8'):
                stream = qtc.QTextStream(self.reffile)
                text = stream.readAll()
                info = qtc.QFileInfo(self.refpath)
                self.ui.RefText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.RefText.insertPlainText(text)
                else:
                    self.ui.RefText.setPlainText(text)

                # update font to selection and size
                self.on_reffont_update()

                # update line spacing
                self.SetRefLineSpacing()

    def OpenRefWithLibreCalc(self):
        lo_cmd = 'libreoffice --calc ' + self.refpath
        print(lo_cmd)
        os.system(lo_cmd)

    def OpenRefWithLibreWriter(self):
        lo_cmd = 'libreoffice --writer ' + self.refpath
        print(lo_cmd)
        os.system(lo_cmd)

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    w = Ui_MainWindow()
    w.show()
    app.exec()
