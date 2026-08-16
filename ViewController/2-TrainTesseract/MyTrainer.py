from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
_LEGACY_MAINUI_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", "0-MainUI"))
_LEGACY_MAINUI_HELPERS_DIR = os.path.abspath(os.path.join(_LEGACY_MAINUI_DIR, "helpers"))
_LOCAL_HELPERS_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "helpers"))
_PROJECT_ROOT_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))

if _PROJECT_ROOT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT_DIR)
if _LEGACY_MAINUI_DIR not in sys.path:
    sys.path.insert(0, _LEGACY_MAINUI_DIR)
if _LEGACY_MAINUI_HELPERS_DIR not in sys.path:
    sys.path.insert(0, _LEGACY_MAINUI_HELPERS_DIR)
if _LOCAL_HELPERS_DIR not in sys.path:
    sys.path.insert(0, _LOCAL_HELPERS_DIR)

from gui_runtime_env import sanitize_current_process_and_reexec

sanitize_current_process_and_reexec()

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from SessionManager import SessionManager
from tesseract_wordlist_helper import update_tesseract_wordlist_from_text
from SqliteHelper import *
from ext import *
from ext import reffind, versefind, versifiercount
import ChrReference as chrref
from project_status_controller import ProjectStatusController
from Core.workflow_wizard_actions import (
    install_workflow_wizard_menu_actions,
    open_default_module_page_workflow_wizard,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from MyTrainerUI import Ui_Trainer
from Dialogs.VariantRecorderDialog import Ui_RecorderDialog

from tesseract_training_support import (
    TrainingWorkspace,
    build_training_command_environment,
    discover_tesseract_installation,
    load_training_progress,
)


class TrainingProgressWidget(qtw.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.summary_label = qtw.QLabel("Training progress will appear here after a log is generated.", self)
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.figure = Figure(figsize=(5.5, 3.5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("Tesseract training progress")
        self.axes.set_xlabel("Iteration")
        self.axes.set_ylabel("Loss / error")
        self.axes.grid(True, alpha=0.25)
        self._draw_empty_state()

    def _draw_empty_state(self, message: str = "No training log found yet.") -> None:
        self.axes.clear()
        self.axes.set_title("Tesseract training progress")
        self.axes.set_xlabel("Iteration")
        self.axes.set_ylabel("Loss / error")
        self.axes.grid(True, alpha=0.25)
        self.axes.text(0.5, 0.5, message, ha="center", va="center", transform=self.axes.transAxes)
        self.canvas.draw_idle()

    def update_from_log(self, log_path: str, installation_summary: str = "") -> None:
        if installation_summary:
            self.summary_label.setText(installation_summary)

        points = load_training_progress(log_path)
        if not points:
            self._draw_empty_state(f"No parseable training metrics found in {log_path}.")
            return

        iterations = [point.iteration for point in points]
        values = [point.value for point in points]
        metric_label = points[-1].label if points else "loss"

        self.axes.clear()
        self.axes.plot(iterations, values, marker="o", linewidth=1.5)
        self.axes.set_title("Tesseract training progress")
        self.axes.set_xlabel("Iteration")
        self.axes.set_ylabel(metric_label.capitalize())
        self.axes.grid(True, alpha=0.25)
        self.canvas.draw_idle()

        plot_path = Path(log_path).with_name("training_progress.png")
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        self.figure.savefig(plot_path, dpi=120)


class Ui_MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Trainer()
        self.ui.setupUi(self)
        install_workflow_wizard_menu_actions(
            self,
            'MyTrainer',
            include_project_wizard=False,
            include_page_wizard=True,
        )
        self.open_page_workflow_wizard = (
            lambda _requested_module=None: open_default_module_page_workflow_wizard(self, 'MyTrainer')
        )

        self.projecthome = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.project_root = Path(self.projecthome)
        self.workspace = TrainingWorkspace.from_project_root(self.project_root, language_code="feg")
        self.workspace.ensure_directories()
        self.installation = discover_tesseract_installation()
        self.session_manager = SessionManager(os.path.join(self.projecthome, "Model", "Project", "Data", "json"))
        self.inbound_default_source = self.session_manager.resolve_receiving_default_input(
            "MyTrainer",
            preferred_input_modules=("MyGlypher", "MyReader", "MyResolver", "MyVersifier"),
            language_hint="greek",
        )
        if self.inbound_default_source:
            os.makedirs(self.inbound_default_source, exist_ok=True)
        self.training_process = qtc.QProcess(self)
        self.training_process.setProcessChannelMode(qtc.QProcess.MergedChannels)
        self.training_process.readyReadStandardOutput.connect(self._consume_training_output)
        self.training_process.readyReadStandardError.connect(self._consume_training_output)
        self.training_process.finished.connect(self._training_finished)

        self._setup_training_pages()

        self.get_session_settings()
        self._apply_closed_loop_defaults()
        self._apply_project_font_defaults()
        self.save_session_settings()
        self.OpenChrReference()
        self.project_status_controller = ProjectStatusController(
            self,
            "MyTrainer",
            session_manager=self.session_manager,
        )

        self.ui.stepReviewNextButton.clicked.connect(self.go_to_training_step)
        self.ui.stepTrainingBackButton.clicked.connect(self.go_to_review_step)
        self.ui.stepTrainingRefreshButton.clicked.connect(self.refresh_training_progress)
        self.ui.stepTrainingStartButton.clicked.connect(self.start_training)
        self.ui.actionTrain_Tesseract_tb.triggered.connect(self.start_training)
        self.ui.actionUpdate_Greek_Wordlist.triggered.connect(
            lambda: self.update_training_wordlist("Greek", "feg")
        )
        self.ui.actionUpdate_Hebrew_Wordlist.triggered.connect(
            lambda: self.update_training_wordlist("Hebrew", "heb")
        )
        self.ui.actionUpdate_Latin_Wordlist.triggered.connect(
            lambda: self.update_training_wordlist("Latin", "lat")
        )
        self.ui.actionSelect_Language_Model.triggered.connect(self.select_language_model)
        self.ui.actionSelect_Fonts.triggered.connect(self.select_training_fonts)
        self.refresh_training_progress()
        self.show()

    def _setup_training_pages(self) -> None:
        container_layout = self.ui.trainingPlotContainer.layout()
        if container_layout is None:
            container_layout = qtw.QVBoxLayout(self.ui.trainingPlotContainer)
            container_layout.setContentsMargins(0, 0, 0, 0)
        else:
            container_layout.setContentsMargins(0, 0, 0, 0)

        self.trainingProgressWidget = TrainingProgressWidget(self.ui.trainingPlotContainer)
        container_layout.addWidget(self.trainingProgressWidget)

        self._update_page_title()
        installation_summary = self._training_installation_summary()
        self.ui.trainingSummaryLabel.setText(installation_summary)

    def OpenChrReference(self) -> None:
        self.chrrefmain = chrref.CharacterReference(self)
        self.chrrefmain.show()

    def _update_page_title(self) -> None:
        if self.ui.page_stack.currentIndex() == 0:
            self.ui.pageTitleLabel.setText("Step 1 of 2: Source review")
        else:
            self.ui.pageTitleLabel.setText("Step 2 of 2: Training and progress")

    def go_to_training_step(self) -> None:
        self.ui.page_stack.setCurrentIndex(1)
        self._update_page_title()
        self.refresh_training_progress()

    def go_to_review_step(self) -> None:
        self.ui.page_stack.setCurrentIndex(0)
        self._update_page_title()

    def _training_installation_summary(self) -> str:
        installation = self.installation
        if not installation:
            return (
                f"Training workspace: {self.workspace.workspace_root}\n"
                "Tesseract is not currently visible on PATH. Install tesseract-ocr 5.0+ or set TESSERACT_BIN."
            )

        languages = ", ".join(installation.languages) if installation.languages else "none detected"
        tessdata_dir = installation.tessdata_dir or "not found"
        return (
            f"Training workspace: {self.workspace.workspace_root}\n"
            f"Tesseract: {installation.binary_path}\n"
            f"Tessdata: {tessdata_dir}\n"
            f"Languages: {languages}"
        )

    def _training_environment(self) -> dict[str, str]:
        environment = build_training_command_environment(self.projecthome, language_code=self.workspace.language_code)
        environment["BIBLION_PROJECT_FONT"] = self.session_manager.get_active_project_font()
        selected_language_model = str(getattr(self, "selected_language_model", "") or "").strip()
        selected_training_fonts = str(getattr(self, "selected_training_fonts", "") or "").strip()
        if selected_language_model:
            environment["BIBLION_TRAINING_LANGUAGE_MODEL"] = selected_language_model
        if selected_training_fonts:
            environment["BIBLION_TRAINING_FONTS_DIR"] = selected_training_fonts
        if self.installation:
            environment["TESSERACT_BIN"] = self.installation.binary_path
            if self.installation.tessdata_dir:
                environment["TESSDATA_PREFIX"] = self.installation.tessdata_dir
        if self.inbound_default_source:
            environment["BIBLION_TRAINING_INPUT_SOURCE"] = self.inbound_default_source
        return environment

    def _training_script_path(self) -> Path:
        return Path(_LOCAL_HELPERS_DIR) / "run_tesseract_training.sh"

    def _training_summary_text(self) -> str:
        lines = [self._training_installation_summary()]
        if self.inbound_default_source:
            lines.append(f"Inbound source default: {self.inbound_default_source}")
        lines.append(f"Tesseract project font: {self.session_manager.get_active_project_font()}")
        lines.append(f"Ground truth: {self.workspace.ground_truth_root}")
        lines.append(f"Wordlists: {self.workspace.wordlist_root}")
        lines.append(f"Configs: {self.workspace.config_root}")
        lines.append(f"Logs: {self.workspace.log_root}")
        lines.append(f"Plots: {self.workspace.plot_root}")
        lines.append(f"Models: {self.workspace.model_root}")
        return "\n".join(lines)

    def get_session_settings(self):
        print("loading session")
        active_project = self.session_manager.get_active_project("Session.json")
        self.current_project_root = active_project.get("project_root", "")
        self.current_project_name = active_project.get("project_name", "")
        session = self.session_manager.values("Session.json")
        for setting, value in session.items():
            if setting.startswith("self."):
                setattr(self, setting[5:], value)

    def _apply_closed_loop_defaults(self) -> None:
        if not self.inbound_default_source:
            self.inbound_default_source = self.session_manager.resolve_receiving_default_input(
                "MyTrainer",
                preferred_input_modules=("MyGlypher", "MyReader", "MyResolver", "MyVersifier"),
                language_hint="greek",
            )
        if self.inbound_default_source:
            os.makedirs(self.inbound_default_source, exist_ok=True)

    def _apply_project_font_defaults(self) -> None:
        point_size = 8
        raw_size = str(getattr(self, "fontsize", "") or "").strip()
        if raw_size.isdigit():
            point_size = int(raw_size)

        workflow_font = self.session_manager.build_workflow_font(
            "FROMVS [MAXR]",
            point_size,
            os.path.dirname(os.path.realpath(__file__)),
        )
        for widget_name in ("RefText", "VerseText", "OutputText"):
            widget = getattr(self.ui, widget_name, None)
            if widget is not None:
                widget.setFont(workflow_font)
        self.font = workflow_font.family()
        self.fontsize = str(workflow_font.pointSize())

    def get_workflow_settings(self):
        workflow_path = os.path.join(self.projecthome, "Model", "SQLite", "json", "Workflow.json")
        with open(workflow_path, encoding="utf-8") as handle:
            data = json.load(handle)
        for sequence in data:
            print(sequence["Sequence"], sequence["DialogUi"], sequence["DefaultSource"])

    def save_session_settings(self, **updates):
        payload = {
            "self.font": str(getattr(self, "font", "") or ""),
            "self.fontsize": str(getattr(self, "fontsize", "") or ""),
            "self.inbound_default_source": str(getattr(self, "inbound_default_source", "") or ""),
            "self.current_project_root": str(getattr(self, "current_project_root", "") or ""),
            "self.current_project_name": str(getattr(self, "current_project_name", "") or ""),
        }
        payload.update(updates)
        self.session_manager.update("Session.json", payload)

    def update_training_wordlist(self, language_name: str, language_code: str) -> None:
        source_path = qtw.QFileDialog.getOpenFileName(
            self,
            f"Select {language_name} wordlist source text",
            self.inbound_default_source or str(self.project_root),
            "Text Files (*.txt *.csv);;All Files (*.*)",
        )[0]
        if not source_path:
            return

        try:
            source_text = Path(source_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            self.ui.OutputText.append(f"Could not read {source_path}: {error}")
            return

        output_dir = self.workspace.wordlist_root.parent / language_code
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{language_code}.wordlist"
        update_tesseract_wordlist_from_text(
            source_text,
            project_root=str(self.project_root),
            output_path=str(output_path),
        )
        self.ui.OutputText.append(f"Updated {language_name} wordlist: {output_path}")

    def select_language_model(self) -> None:
        selected_path = qtw.QFileDialog.getOpenFileName(
            self,
            "Select Tesseract language model",
            str(self.workspace.model_root),
            "Tesseract Models (*.traineddata);;All Files (*.*)",
        )[0]
        if not selected_path:
            return
        self.selected_language_model = selected_path
        self.save_session_settings(**{"self.selected_language_model": selected_path})
        self.ui.OutputText.append(f"Training language model: {selected_path}")
        self.refresh_training_progress()

    def select_training_fonts(self) -> None:
        selected_path = qtw.QFileDialog.getExistingDirectory(
            self,
            "Select training fonts directory",
            str(self.project_root),
        )
        if not selected_path:
            return
        self.selected_training_fonts = selected_path
        self.save_session_settings(**{"self.selected_training_fonts": selected_path})
        self.ui.OutputText.append(f"Training fonts directory: {selected_path}")
        self.refresh_training_progress()

    def refresh_training_progress(self):
        self.workspace.ensure_directories()
        installation_summary = self._training_summary_text()
        self.ui.trainingSummaryLabel.setText(installation_summary)
        self.trainingProgressWidget.update_from_log(str(self.workspace.log_file), installation_summary)

    def start_training(self):
        self.workspace.ensure_directories()
        script_path = self._training_script_path()
        self.go_to_training_step()
        if not script_path.exists():
            self.ui.OutputText.append(
                f"Training script not found at {script_path}. Create it or point TRAINING_COMMAND at your tesstrain entrypoint."
            )
            self.refresh_training_progress()
            return

        if self.training_process.state() != qtc.QProcess.NotRunning:
            self.ui.OutputText.append("Training is already running.")
            return

        environment = qtc.QProcessEnvironment.systemEnvironment()
        for key, value in self._training_environment().items():
            environment.insert(key, value)
        self.training_process.setProcessEnvironment(environment)

        command_arguments = [str(script_path), self.projecthome, self.workspace.language_code]
        self.ui.OutputText.append(f"Launching training wrapper: {' '.join(command_arguments)}")
        self.training_process.start("bash", command_arguments)

    def _consume_training_output(self):
        output = bytes(self.training_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if output:
            self.ui.OutputText.append(output.rstrip())
            if self.workspace.log_file.exists():
                self.refresh_training_progress()

    def _training_finished(self, exit_code: int, exit_status: qtc.QProcess.ExitStatus) -> None:
        status_text = "normal" if exit_status == qtc.QProcess.NormalExit else "crashed"
        self.ui.OutputText.append(f"Training process finished with exit code {exit_code} ({status_text}).")
        self.refresh_training_progress()

    def OpenWithMyWriter(self):
        mw_file = os.path.join(self.projecthome, "ViewController", "4-PostProcess", "MyWriter.py")
        print(f"Launching: {sys.executable} {mw_file}")
        subprocess.Popen([sys.executable, mw_file])


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = Ui_MainWindow()
    window.show()
    app.exec()

