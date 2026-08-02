# Python imports
import sys
import os
import json

script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui_runtime_env import sanitize_current_process_and_reexec

sanitize_current_process_and_reexec()

# PyQt5 imports
from PyQt5 import QtWidgets as qtw

from SessionManager import SessionManager
from project_status_controller import ProjectStatusController
from ext import *
# Custom imports
from MyTrainerUI import Ui_Trainer
from SqliteHelper import *
#import pytesseract


def _first_existing_path(*paths):
    for path in paths:
        if os.path.exists(path):
            return path
    return paths[0] if paths else ""

class Ui_MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Trainer()
        self.ui.setupUi(self)
        if hasattr(self.ui, 'actionExit'):
            self.ui.actionExit.triggered.connect(self.close)

        self.projecthome = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.session_manager = SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json'))

        chr_ref_path = _first_existing_path(
            os.path.join(self.projecthome, 'ViewController', '3-ConductOCR', 'FROMVS ChrReference.txt'),
            os.path.join(self.projecthome, 'ViewController', 'Application', '3-ConductOCR', 'FROMVS ChrReference.txt'),
        )
        with open(chr_ref_path, encoding='utf-8') as f:
            ChrRefText = f.read()
        self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        # Restore Session settings
        self.get_session_settings()
        self.project_status_controller = ProjectStatusController(
            self,
            'MyTrainer',
            session_manager=self.session_manager,
        )

        self.show()

    def get_session_settings(self):
        # get session settings from shared manager
        print("loading session")
        active_project = SessionManager().get_active_project('Session.json')
        self.current_project_root = active_project.get('project_root', '')
        self.current_project_name = active_project.get('project_name', '')
        session = self.session_manager.values('VersifierSession.json')
        for setting, value in session.items():
            if setting.startswith('self.'):
                setattr(self, setting[5:], value)

    def get_workflow_settings(self):
        workflow_path = os.path.join(self.projecthome, 'Model', 'SQLite', 'json', 'Workflow.json')
        with open(workflow_path, encoding='utf-8') as f:
            data = json.load(f)
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'], Sequence['DefaultSource'])

    def save_session_settings(self):
        print("Saving Trainer session settings")  

    def OpenWithMyWriter(self):
        mw_file = _first_existing_path(
            os.path.join(self.projecthome, 'ViewController', '0-MainUI', 'MyWriter.py'),
            os.path.join(self.projecthome, 'ViewController', 'Application', '0-MainUI', 'MyWriter.py'),
        )
        mw_cmd = f"{sys.executable} {mw_file}"
        print(mw_cmd)
        os.system(mw_cmd)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    w = Ui_MainWindow()
    w.show()
    app.exec()

