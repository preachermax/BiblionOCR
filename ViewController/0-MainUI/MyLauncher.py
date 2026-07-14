#print(len(locals()))

# Python imports
import sys
import os
import subprocess
#import glob
import json
from html import escape

from gui_runtime_env import sanitize_current_process_and_reexec

script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
portal_feed_dir = os.path.join(project_root, 'docs', 'portal', 'PortalFeed')
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if portal_feed_dir not in sys.path:
    sys.path.insert(0, portal_feed_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

sanitize_current_process_and_reexec()

from SessionManager import SessionManager
from project_status_controller import ProjectStatusController
#from subprocess import Popen, PIPE, CalledProcessError
from HelpSystem import PROGRAM_HELP, add_help_menu, show_help
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
# Custom imports
from MyLauncherUI import Ui_MainUI
from LocalFileDrop import LocalFileDropMixin
from PortalHtmlPanel import mount_html_panel
from PortalFeedClient import PortalFeedClient

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

PORTAL_PLACEHOLDER_ALIASES = {
    'main': ('portal_placeholder_main', 'html_placeholder', 'Main_placeholder', 'Main_widget'),
    'banner': ('portal_placeholder_banner', 'Banner_widget'),
    'top_left': ('portal_placeholder_top_left', 'TopLeft_widget'),
    'upper_left': ('portal_placeholder_upper_left', 'UpperLeft_widget'),
    'lower_left': ('portal_placeholder_lower_left', 'LowerLeft_widget'),
    'right_center': ('portal_placeholder_right_center', 'RightCenter_widget'),
    'secondary': ('portal_placeholder_secondary', 'html_placeholder_2', 'Secondary_placeholder', 'Footer_widget'),
    'tertiary': ('portal_placeholder_tertiary', 'html_placeholder_3', 'Tertiary_placeholder', 'BottomLeft_widget'),
    'activity': ('portal_placeholder_activity',),
}

LEGACY_PORTAL_PLACEHOLDER_ORDER = ('main', 'secondary', 'tertiary')

PORTAL_PANEL_FALLBACKS = {
    'main': ('main',),
    'banner': ('banner', 'activity', 'main'),
    'top_left': ('top_left', 'secondary', 'activity', 'main'),
    'upper_left': ('upper_left', 'activity', 'secondary', 'main'),
    'lower_left': ('lower_left', 'tertiary', 'activity', 'secondary'),
    'right_center': ('right_center', 'activity', 'tertiary', 'secondary', 'main'),
    'secondary': ('secondary', 'activity', 'tertiary'),
    'tertiary': ('tertiary', 'activity', 'secondary'),
    'activity': ('activity', 'secondary', 'tertiary'),
}

LAUNCHER_BUTTON_PROGRAMS = {
    'MyReaderbutton': 'MyReader',
    'MyScannerbutton': 'MyScanner',
    'MyGlypherbutton': 'MyGlypher',
    'MyBoxerbutton': 'MyBoxer',
    'MyPixlerbutton': 'MyPixler',
    'MyServerbutton': 'MyServer',
    'MyVersifierbutton': 'MyVersifier',
    'MyResolverbutton': 'MyResolver',
    'MyLexerbutton': 'MyLexer',
    'MyGrounderbutton': 'MyGrounder',
    'MyTrainerbutton': 'MyTrainer',
    'MyWriterbutton': 'MyWriter',
    'MyExplorerbutton': 'MyExplorer',
}

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
        add_help_menu(self, 'MyLauncher')
        # extended slots code
        #
        self.ui.actionMy_Reader.triggered.connect(self.OpenWithMyReader)
        self.ui.actionMy_Scanner.triggered.connect(self.OpenWithMyScanner)
        self.ui.actionMy_Glypher.triggered.connect(self.OpenWithMyGlypher)
        self.ui.actionMy_Pixler.triggered.connect(self.OpenWithMyPixler)
        self.ui.actionMy_Boxer.triggered.connect(self.OpenWithMyBoxer)
        self.ui.actionMy_Server.triggered.connect(self.OpenWithMyServer)
        self.ui.actionMy_Versifier.triggered.connect(self.OpenWithMyVersifier)
        self.ui.actionMy_Resolver.triggered.connect(self.OpenWithMyResolver)
        self.ui.actionMy_Lexer.triggered.connect(self.OpenWithMyLexer)
        self.ui.actionMy_Grounder.triggered.connect(self.OpenWithMyGrounder)
        self.ui.actionMy_Trainer.triggered.connect(self.OpenWithMyTrainer)
        self.ui.actionMy_Writer.triggered.connect(self.OpenWithMyWriter)
        self.ui.actionMy_Explorer.triggered.connect(self.OpenWithMyExplorer)

        self.ui.actionUpdate_Wordlist_tb.triggered.connect(self.actionUpdate_Wordlist)
        self.ui.actionTrain_Tesseract_tb.triggered.connect(self.actionTrain_Tesseract)

        #self.ui.Gimpbutton.clicked.connect(self.actionGimpEdit)
        self.ui.MyReaderbutton.clicked.connect(self.OpenWithMyReader)
        self.ui.MyScannerbutton.clicked.connect(self.OpenWithMyScanner)
        self.ui.MyGlypherbutton.clicked.connect(self.OpenWithMyGlypher)
        self.ui.MyBoxerbutton.clicked.connect(self.OpenWithMyBoxer)
        self.ui.MyPixlerbutton.clicked.connect(self.OpenWithMyPixler)
        self.ui.MyServerbutton.clicked.connect(self.OpenWithMyServer)
        self.ui.MyVersifierbutton.clicked.connect(self.OpenWithMyVersifier)
        self.ui.MyResolverbutton.clicked.connect(self.OpenWithMyResolver)
        self.ui.MyLexerbutton.clicked.connect(self.OpenWithMyLexer)
        self.ui.MyGrounderbutton.clicked.connect(self.OpenWithMyGrounder)
        self.ui.MyTrainerbutton.clicked.connect(self.OpenWithMyTrainer)
        self.ui.MyWriterbutton.clicked.connect(self.OpenWithMyWriter)
        self.ui.MyExplorerbutton.clicked.connect(self.OpenWithMyExplorer)

        # UI and slots code ends here.

        self.readme_path = os.path.join(project_root, 'README.md')
        self.readme_url = qtc.QUrl.fromLocalFile(self.readme_path)
        self.initialize_readme_panel()

        self.portal_client = PortalFeedClient()
        self.portal_panels = self.initialize_portal_panels()
        self.setup_launcher_context_menus()
        self.load_portal_feed()

        # Restore Session settings
        self.get_session_settings()
        self.project_status_controller = ProjectStatusController(
            self,
            'MyLauncher',
            session_manager=self.session_manager,
        )

        self.show()

    def initialize_readme_panel(self):
        if not hasattr(self.ui, 'OCRText'):
            self.ui.OCRDocument = None
            self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
            self.ui.OCRTextFormat = qtg.QTextFormat()
            self.ui.OCRCursor = None
            return

        original_ocr_text = self.ui.OCRText
        ocr_browser = qtw.QTextBrowser(self.ui.centralwidget)
        ocr_browser.setObjectName(original_ocr_text.objectName())
        ocr_browser.setGeometry(original_ocr_text.geometry())
        ocr_browser.setMinimumSize(original_ocr_text.minimumSize())
        ocr_browser.setMaximumSize(original_ocr_text.maximumSize())
        ocr_browser.setUndoRedoEnabled(False)
        ocr_browser.setReadOnly(True)
        ocr_browser.setOpenLinks(False)
        ocr_browser.setOpenExternalLinks(False)
        ocr_browser.setTextInteractionFlags(qtc.Qt.TextBrowserInteraction)
        original_ocr_text.deleteLater()
        self.ui.OCRText = ocr_browser
        self.ui.OCRText.anchorClicked.connect(self.open_readme_link)

        self.ui.OCRDocument = self.ui.OCRText.document()
        self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
        self.ui.OCRTextFormat = qtg.QTextFormat()
        self.ui.OCRCursor = qtg.QTextCursor(self.ui.OCRDocument)

        self.ui.OCRDocument.setBaseUrl(self.readme_url)

        with open(self.readme_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if hasattr(self.ui.OCRText, 'setMarkdown'):
            self.ui.OCRText.setMarkdown(content)
        else:
            self.ui.OCRText.setPlainText(content)

    def load_portal_feed(self):
        fallback_feed = {
            'title': 'Biblion Portal Feed',
            'panels': {
                'main': (
                    "<h2>Biblion Portal Feed</h2>"
                    "<p>The launcher landing page is ready for the primary Django feed.</p>"
                    "<p>Set <code>BIBLION_PORTAL_FEED_URL</code> to enable live content.</p>"
                ),
                'banner': (
                    "<h3>Portal Banner</h3>"
                    "<p>This placeholder now accepts live portal feed content.</p>"
                ),
                'top_left': (
                    "<h3>Top Left</h3>"
                    "<p>Reserve this surface for status or summary content from the portal.</p>"
                ),
                'upper_left': (
                    "<h3>Upper Left</h3>"
                    "<p>Reserve this surface for activity or navigation excerpts.</p>"
                ),
                'lower_left': (
                    "<h3>Lower Left</h3>"
                    "<p>Reserve this surface for documentation or announcements.</p>"
                ),
                'right_center': (
                    "<h3>Right Center</h3>"
                    "<p>Reserve this surface for stacked live feed excerpts.</p>"
                ),
                'secondary': (
                    "<h3>Project Status</h3>"
                    "<p>Reserve this card for project health, build status, or OCR pipeline summaries.</p>"
                ),
                'tertiary': (
                    "<h3>Announcements</h3>"
                    "<p>Reserve this card for portal notices, onboarding, or recent activity.</p>"
                ),
                'activity': (
                    "<h3>Activity</h3>"
                    "<p>Add a placeholder named <code>portal_placeholder_activity</code> to render this feed block.</p>"
                ),
            },
        }

        try:
            if self.portal_client.get_url:
                feed = self.portal_client.fetch_feed()
            else:
                feed = fallback_feed
        except Exception as error:
            feed = fallback_feed
            feed['panels']['main'] += f"<p><b>Feed load failed:</b> {error}</p>"

        self.render_portal_feed(feed)

    def render_portal_feed(self, feed):
        panels = feed.get('panels', {})
        self.setWindowTitle(feed.get('title', 'MyLauncher'))
        for name, panel in self.portal_panels.items():
            panel.set_html(self.resolve_panel_html(name, panels))

    def resolve_panel_html(self, panel_name, panels):
        for candidate_name in PORTAL_PANEL_FALLBACKS.get(panel_name, (panel_name,)):
            candidate_value = panels.get(candidate_name, '')
            if isinstance(candidate_value, str) and candidate_value:
                return candidate_value
        return ''

    def setup_launcher_context_menus(self):
        for button_name, program_name in LAUNCHER_BUTTON_PROGRAMS.items():
            button = getattr(self.ui, button_name, None)
            if button is None:
                continue

            button.customContextMenuRequested.connect(
                lambda point, source_button=button, source_program=program_name: self.open_launcher_context_menu(
                    source_button,
                    source_program,
                    point,
                )
            )

    def open_launcher_context_menu(self, button, program_name, point):
        menu = qtw.QMenu(self)
        open_action = menu.addAction(f'Open {program_name}')
        help_panel_action = menu.addAction('Generate Project Help in Mainwidget')
        help_dialog_action = menu.addAction('Open Program Help Dialog')

        selected_action = menu.exec_(button.mapToGlobal(point))
        if selected_action == open_action:
            self.open_program_by_name(program_name)
        elif selected_action == help_panel_action:
            self.render_program_help_in_main_panel(program_name)
        elif selected_action == help_dialog_action:
            show_help(self, program_name)

    def open_program_by_name(self, program_name):
        handler = getattr(self, f'OpenWith{program_name}', None)
        if callable(handler):
            handler()

    def render_program_help_in_main_panel(self, program_name):
        help_data = PROGRAM_HELP.get(program_name, {})
        html = self.build_program_help_html(program_name, help_data)
        main_panel = self.portal_panels.get('main')

        if main_panel is not None:
            main_panel.set_html(html)
        elif hasattr(self.ui, 'OCRText'):
            self.ui.OCRText.setHtml(html)

        self.setWindowTitle(f"{program_name} Help - MyLauncher")

    def build_program_help_html(self, program_name, help_data):
        title = help_data.get('title', program_name)
        sections = [
            '<article style="padding: 18px; font-family: Georgia, serif; line-height: 1.6;">',
            f'<h1>{escape(title)}</h1>',
            f'<p><strong>Program key:</strong> {escape(program_name)}</p>',
            '<p>Use the launcher context menu to review project help here, or open the full help dialog for the same tool.</p>',
        ]

        for label, key in (
            ('Overview', 'description'),
            ('Usage Guide', 'usage'),
            ('Development Notes', 'development'),
        ):
            value = help_data.get(key)
            if not value:
                continue

            sections.extend([
                f'<h2>{escape(label)}</h2>',
                '<pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">'
                f'{escape(value).strip()}'
                '</pre>',
            ])

        sections.append('</article>')
        return ''.join(sections)

    def initialize_portal_panels(self):
        panels = {}
        placeholders = self.discover_portal_placeholders()
        for name, placeholder in placeholders.items():
            panels[name] = mount_html_panel(placeholder)
        return panels

    def discover_portal_placeholders(self):
        discovered = {}
        ui_widgets = {
            attr_name: getattr(self.ui, attr_name)
            for attr_name in dir(self.ui)
            if isinstance(getattr(self.ui, attr_name), qtw.QWidget)
        }

        for panel_name, aliases in PORTAL_PLACEHOLDER_ALIASES.items():
            for alias in aliases:
                widget = ui_widgets.get(alias)
                if widget is not None:
                    discovered[panel_name] = widget
                    break

        dynamic_placeholders = []
        for attr_name, widget in ui_widgets.items():
            if attr_name in {'centralwidget', 'menubar', 'statusbar'}:
                continue

            panel_name = self.placeholder_name_to_panel_key(attr_name)
            if panel_name is None or panel_name in discovered:
                continue

            dynamic_placeholders.append((panel_name, widget))

        for panel_name, widget in dynamic_placeholders:
            discovered[panel_name] = widget

        return discovered

    def placeholder_name_to_panel_key(self, widget_name):
        if widget_name == 'html_placeholder':
            return 'main'

        if widget_name in {'Main_placeholder', 'Main_widget'}:
            return 'main'

        if widget_name == 'Banner_widget':
            return 'banner'

        if widget_name == 'TopLeft_widget':
            return 'top_left'

        if widget_name == 'UpperLeft_widget':
            return 'upper_left'

        if widget_name == 'LowerLeft_widget':
            return 'lower_left'

        if widget_name == 'RightCenter_widget':
            return 'right_center'

        if widget_name == 'Footer_widget':
            return 'secondary'

        if widget_name == 'BottomLeft_widget':
            return 'tertiary'

        if widget_name.startswith('portal_placeholder_'):
            suffix = widget_name[len('portal_placeholder_'):]
            return suffix or None

        if widget_name.startswith('html_placeholder_'):
            suffix = widget_name[len('html_placeholder_'):]
            if suffix.isdigit():
                index = int(suffix)
                if 1 <= index <= len(LEGACY_PORTAL_PLACEHOLDER_ORDER):
                    return LEGACY_PORTAL_PLACEHOLDER_ORDER[index - 1]
                return f'legacy_{index}'

            return suffix or None

        return None

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

    def open_readme_link(self, url):
        target_url = self.readme_url.resolved(url)
        qtg.QDesktopServices.openUrl(target_url)

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
        subprocess.Popen([sys.executable, module_path], cwd=project_root)

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

    def OpenWithMyServer(self):
        self.run_child_module('MyServer.py')

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
