import os
import subprocess

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtPrintSupport as qps


_TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".log",
    ".md",
    ".py",
    ".rst",
    ".sql",
    ".text",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


class ProjectPrintHandler:
    """Unified print handler for UI modules."""

    def __init__(self, parent=None):
        self.parent = parent

    def _printer(self):
        return qps.QPrinter(qps.QPrinter.HighResolution)

    def _show_error(self, owner, title, message):
        qtw.QMessageBox.warning(owner, title, message)

    def _show_info(self, owner, title, message):
        qtw.QMessageBox.information(owner, title, message)

    def _print_dialog(self, owner, printer):
        dialog = qps.QPrintDialog(printer, owner)
        dialog.setWindowTitle("Print")
        return dialog.exec_() == qtw.QDialog.Accepted

    def _render_image(self, printer, image):
        painter = qtg.QPainter(printer)
        if not painter.isActive():
            return

        page_rect = printer.pageRect()
        scaled = image.scaled(
            page_rect.size(),
            qtc.Qt.KeepAspectRatio,
            qtc.Qt.SmoothTransformation,
        )
        x = page_rect.x() + (page_rect.width() - scaled.width()) // 2
        y = page_rect.y() + (page_rect.height() - scaled.height()) // 2
        painter.drawImage(qtc.QPoint(x, y), scaled)
        painter.end()

    def handle_image(self, image, owner, preview=False):
        if image is None:
            self._show_info(owner, "No Image", "No image is available to print.")
            return

        if isinstance(image, qtg.QPixmap):
            image = image.toImage()
        elif not isinstance(image, qtg.QImage):
            self._show_error(owner, "Print Error", "Unsupported image type for printing.")
            return

        if image.isNull():
            self._show_info(owner, "No Image", "The selected image is empty.")
            return

        printer = self._printer()
        if preview:
            preview_dialog = qps.QPrintPreviewDialog(printer, owner)
            preview_dialog.paintRequested.connect(lambda p: self._render_image(p, image))
            preview_dialog.exec_()
            return

        if self._print_dialog(owner, printer):
            self._render_image(printer, image)

    def handle_document(self, document, owner, preview=False):
        if document is None:
            self._show_info(owner, "No Document", "No document is available to print.")
            return

        if isinstance(document, str):
            doc = qtg.QTextDocument()
            doc.setPlainText(document)
            document = doc

        if not hasattr(document, "print_"):
            self._show_error(owner, "Print Error", "Unsupported document type for printing.")
            return

        printer = self._printer()
        if preview:
            preview_dialog = qps.QPrintPreviewDialog(printer, owner)
            preview_dialog.paintRequested.connect(document.print_)
            preview_dialog.exec_()
            return

        if self._print_dialog(owner, printer):
            document.print_(printer)

    def _print_text_file(self, target_file, owner, preview=False):
        try:
            with open(target_file, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except OSError as exc:
            self._show_error(owner, "Print Error", f"Unable to read file:\n{exc}")
            return

        doc = qtg.QTextDocument()
        doc.setPlainText(content)
        self.handle_document(doc, owner, preview=preview)

    def _print_with_cups(self, target_file, owner):
        try:
            completed = subprocess.run(
                ["lp", target_file],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            self._show_error(owner, "Print Error", "The 'lp' command is not installed on this system.")
            return
        except subprocess.CalledProcessError as exc:
            output = (exc.stderr or exc.stdout or "").strip()
            self._show_error(owner, "Print Error", f"CUPS rejected the print job.\n{output}")
            return

        output = (completed.stdout or "").strip()
        if output:
            self._show_info(owner, "Print Job Submitted", output)

    def handle_print(self, target_file, owner, preview=False):
        if not target_file:
            self._show_info(owner, "No File", "No file is selected for printing.")
            return

        target_file = os.path.abspath(str(target_file))
        if not os.path.exists(target_file):
            self._show_error(owner, "Print Error", f"File does not exist:\n{target_file}")
            return

        suffix = os.path.splitext(target_file)[1].lower()
        if suffix in _TEXT_EXTENSIONS:
            self._print_text_file(target_file, owner, preview=preview)
            return

        image = qtg.QImage(target_file)
        if not image.isNull():
            self.handle_image(image, owner, preview=preview)
            return

        if preview:
            self._show_info(
                owner,
                "Preview Not Supported",
                "Print preview is not available for this file type.",
            )
            return

        self._print_with_cups(target_file, owner)
