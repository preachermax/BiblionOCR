import os
import shutil
import subprocess
import sys
import tempfile

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from SessionManager import SessionManager


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_DEFAULT_PIXLER_SCRIPT = os.path.join(
    _PROJECT_ROOT,
    "ViewController",
    "1-PreProcess",
    "MyPixler.py",
)


class PixlerHandoffController(qtc.QObject):
    def __init__(self, owner, module_name, pixler_script=None):
        super().__init__(owner)
        self.owner = owner
        self.module_name = str(module_name or owner.__class__.__name__)
        self.pixler_script = os.path.abspath(pixler_script or _DEFAULT_PIXLER_SCRIPT)
        self.session_manager = SessionManager()
        self.source_path = ""
        self.return_path = ""
        self.return_dialog = None
        self.poll_timer = qtc.QTimer(self)
        self.poll_timer.setInterval(250)
        self.poll_timer.timeout.connect(self._poll_return)

    def launch(self, source_path=None):
        resolved_source = self._resolve_source_path(source_path)
        if not resolved_source:
            qtw.QMessageBox.information(
                self.owner,
                "Open MyPixler",
                "Open an image first so MyPixler can return the edited image to this module.",
            )
            return False

        if not os.path.isfile(self.pixler_script):
            qtw.QMessageBox.warning(
                self.owner,
                "Open MyPixler",
                f"MyPixler was not found:\n{self.pixler_script}",
            )
            return False

        self.source_path = resolved_source
        self.return_path = self._create_return_path()
        self.session_manager.set_active_project_page_state(
            self.source_path,
            module_name=self.module_name,
        )
        command = [
            sys.executable,
            self.pixler_script,
            "--subprocess-mode",
            "--return-path",
            self.return_path,
            "--caller",
            self.module_name,
            self.source_path,
        ]

        try:
            process = subprocess.Popen(command)
        except OSError as exc:
            qtw.QMessageBox.critical(
                self.owner,
                "Open MyPixler",
                f"Unable to launch MyPixler:\n{self.pixler_script}\n\n{exc}",
            )
            return False

        print(f"[MyPixler HANDOFF] {self.module_name} launched PID {process.pid}: {self.source_path}")
        self.poll_timer.start()
        return True

    def _resolve_source_path(self, source_path=None):
        candidates = (
            source_path,
            getattr(self.owner, "imgpath", ""),
            self.session_manager.get_active_project_page_state().get("page_path", ""),
        )
        for candidate in candidates:
            normalized = os.path.abspath(os.path.normpath(str(candidate or "")))
            if candidate and os.path.isfile(normalized):
                return normalized
        return ""

    @staticmethod
    def _create_return_path():
        return os.path.join(
            tempfile.mkdtemp(prefix="biblion_pixler_return_"),
            "pixler_return.tif",
        )

    def _poll_return(self):
        if not self.return_path or not os.path.isfile(self.return_path):
            return
        if os.path.getsize(self.return_path) <= 0:
            return

        self.poll_timer.stop()
        self._show_return_dialog()

    def _show_return_dialog(self):
        pixmap = qtg.QPixmap(self.return_path)
        if pixmap.isNull():
            qtw.QMessageBox.warning(
                self.owner,
                "MyPixler Return",
                f"MyPixler returned an unreadable image:\n{self.return_path}",
            )
            return

        dialog = qtw.QDialog(self.owner)
        dialog.setWindowTitle(f"MyPixler Return - {self.module_name}")
        dialog.resize(760, 600)
        layout = qtw.QVBoxLayout(dialog)

        message = qtw.QLabel(
            f"MyPixler returned an edited image to {self.module_name}."
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        preview = qtw.QLabel(dialog)
        preview.setAlignment(qtc.Qt.AlignCenter)
        preview.setMinimumSize(480, 320)
        preview.setPixmap(
            pixmap.scaled(
                720,
                500,
                qtc.Qt.KeepAspectRatio,
                qtc.Qt.SmoothTransformation,
            )
        )
        layout.addWidget(preview, 1)

        button_row = qtw.QHBoxLayout()
        overwrite_button = qtw.QPushButton("Overwrite Source", dialog)
        save_as_button = qtw.QPushButton("Save As...", dialog)
        close_button = qtw.QPushButton("Close", dialog)
        button_row.addWidget(overwrite_button)
        button_row.addWidget(save_as_button)
        button_row.addStretch(1)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

        overwrite_button.clicked.connect(self._overwrite_source)
        overwrite_button.clicked.connect(dialog.accept)
        save_as_button.clicked.connect(self._save_return_as)
        close_button.clicked.connect(dialog.reject)

        self.return_dialog = dialog
        dialog.finished.connect(self._clear_return_dialog)
        dialog.show()
        dialog.raise_()

    def _overwrite_source(self):
        if not self.source_path or not self.return_path:
            return False
        if not os.path.isfile(self.return_path):
            return False

        shutil.copy2(self.return_path, self.source_path)
        self.session_manager.set_active_project_page_state(
            self.source_path,
            module_name=self.module_name,
        )
        self._refresh_owner_image()
        status_bar = getattr(self.owner, "statusBar", None)
        if callable(status_bar):
            status_bar().showMessage(
                f"MyPixler changes applied to {os.path.basename(self.source_path)}",
                5000,
            )
        return True

    def _save_return_as(self):
        suggested_path = os.path.join(
            os.path.dirname(self.source_path),
            f"{os.path.splitext(os.path.basename(self.source_path))[0]}_pixler.tif",
        )
        destination, _selected_filter = qtw.QFileDialog.getSaveFileName(
            self.owner,
            "Save MyPixler Result",
            suggested_path,
            "TIFF images (*.tif *.tiff);;All files (*)",
        )
        if not destination:
            return False
        shutil.copy2(self.return_path, destination)
        return True

    def _refresh_owner_image(self):
        show_image = getattr(self.owner, "showImage", None)
        if callable(show_image):
            show_image(self.source_path)
            return

        reload_image = getattr(self.owner, "ReloadImage", None)
        if callable(reload_image):
            reload_image()

    def _clear_return_dialog(self):
        self.return_dialog = None


def launch_pixler_handoff(owner, module_name, source_path=None, pixler_script=None):
    controller = getattr(owner, "_pixler_handoff_controller", None)
    if controller is None:
        controller = PixlerHandoffController(owner, module_name, pixler_script)
        owner._pixler_handoff_controller = controller
    return controller.launch(source_path)
