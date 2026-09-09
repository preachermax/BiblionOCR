from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

from PIL import Image
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

try:
    from .SourceReaderUI import Ui_SourceReader
except ImportError:
    from SourceReaderUI import Ui_SourceReader


SOURCE_DOCUMENT_EXTENSIONS = {".pdf", ".tif", ".tiff"}
SOURCE_DOCUMENT_FILTER = "Multi-page source documents (*.pdf *.tif *.tiff)"


def _validate_source_document_type(source_path):
    if os.path.splitext(str(source_path))[1].lower() not in SOURCE_DOCUMENT_EXTENSIONS:
        raise ValueError("Source reader supports multi-page PDF and TIFF documents only.")


def _choose_source_document(parent, current_path=""):
    start_directory = os.path.dirname(os.path.abspath(current_path)) if current_path else ""
    return qtw.QFileDialog.getOpenFileName(
        parent,
        "Open Multi-page Source Document",
        start_directory,
        SOURCE_DOCUMENT_FILTER,
    )[0]


def _renderer_path():
    return os.path.join(os.path.dirname(__file__), "qt_pdf_renderer.py")


def _run_pdf_renderer(*arguments):
    try:
        return subprocess.run(
            [sys.executable, _renderer_path(), *[str(argument) for argument in arguments]],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        if "PyQt6" in detail or "QtPdf" in detail:
            detail = "QtPdf support requires PyQt6 6.10 or newer in the active Python environment."
        raise RuntimeError(detail.strip()) from exc


def _source_page_count(source_path):
    extension = os.path.splitext(source_path)[1].lower()
    if extension == ".pdf":
        result = _run_pdf_renderer("metadata", source_path)
        return int(json.loads(result.stdout).get("page_count", 0))
    try:
        with Image.open(source_path) as source_image:
            return int(getattr(source_image, "n_frames", 1))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Could not read TIFF source document: {exc}") from exc


def _render_source_page(source_path, page_index, render_width, output_path):
    if os.path.splitext(source_path)[1].lower() == ".pdf":
        _run_pdf_renderer("render", source_path, page_index, render_width, output_path)
        return
    try:
        with Image.open(source_path) as source_image:
            source_image.seek(page_index)
            page_image = source_image.convert("RGBA")
            if page_image.width != render_width:
                render_height = max(1, round(page_image.height * render_width / page_image.width))
                page_image = page_image.resize((render_width, render_height), Image.Resampling.LANCZOS)
            page_image.save(output_path, format="PNG")
    except (EOFError, OSError, ValueError) as exc:
        raise ValueError(f"Could not render TIFF page {page_index + 1}: {exc}") from exc


class SourceDocumentLoadWorker(qtc.QObject):
    progress = qtc.pyqtSignal(int, str)
    loaded = qtc.pyqtSignal(str, int, str)
    failed = qtc.pyqtSignal(str)

    def __init__(self, source_path, render_width=800):
        super().__init__()
        self.source_path = os.path.abspath(source_path)
        self.render_width = max(200, int(render_width))

    @qtc.pyqtSlot()
    def run(self):
        output_path = ""
        try:
            _validate_source_document_type(self.source_path)
            self.progress.emit(10, "Reading source document metadata...")
            page_count = _source_page_count(self.source_path)
            if page_count < 2:
                raise ValueError(
                    "Source reader requires a multi-page document containing at least two pages."
                )
            self.progress.emit(45, f"Preparing page 1 of {page_count}...")
            output_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            output_path = output_file.name
            output_file.close()
            _render_source_page(self.source_path, 0, self.render_width, output_path)
            self.progress.emit(100, "Source document ready.")
            self.loaded.emit(self.source_path, page_count, output_path)
        except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
            if output_path:
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            self.failed.emit(str(exc))


class SourceReaderWidget(qtw.QWidget):
    closeRequested = qtc.pyqtSignal()
    hideRequested = qtc.pyqtSignal()
    dockToggleRequested = qtc.pyqtSignal()
    openRequested = qtc.pyqtSignal()

    ZOOM_LEVELS = (25, 50, 75, 100, 125, 150, 175, 200)

    def __init__(self, pdf_path, parent=None, preloaded_page_count=None, preloaded_image_path=""):
        super().__init__(parent)
        self.pdf_path = os.path.abspath(pdf_path)
        self.source_type = os.path.splitext(self.pdf_path)[1].lower()
        _validate_source_document_type(self.pdf_path)
        self.page_count = 0
        self.page_index = 0
        self.zoom_percent = 100
        self.fit_width = True
        self._rendered_pixmap = qtg.QPixmap()
        self.source_reader_ui = Ui_SourceReader()
        self.source_reader_ui.setupUi(self)
        for name in (
            "toolbar_widget",
            "previous_button",
            "next_button",
            "page_spin",
            "page_count_label",
            "open_button",
            "zoom_out_button",
            "zoom_combo",
            "zoom_slider",
            "zoom_in_button",
            "fit_width_button",
            "dock_toggle_button",
            "hide_button",
            "close_button",
            "scroll_area",
            "page_label",
        ):
            setattr(self, name, getattr(self.source_reader_ui, name))

        toolbar_font = self.toolbar_widget.font()
        if toolbar_font.pointSizeF() > 0:
            toolbar_font.setPointSizeF(max(8.0, toolbar_font.pointSizeF() - 1.0))
        self.toolbar_widget.setFont(toolbar_font)
        self.previous_button.clicked.connect(self.previous_page)
        self.next_button.clicked.connect(self.next_page)
        self.page_spin.valueChanged.connect(self._select_page)
        self.open_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_DialogOpenButton))
        self.open_button.clicked.connect(self.openRequested)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_combo.addItems([f"{level}%" for level in self.ZOOM_LEVELS])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self._select_zoom)
        self.zoom_slider.setRange(self.ZOOM_LEVELS[0], self.ZOOM_LEVELS[-1])
        self.zoom_slider.setSingleStep(5)
        self.zoom_slider.setPageStep(25)
        self.zoom_slider.setValue(self.zoom_percent)
        self.zoom_slider.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
        self.zoom_slider.valueChanged.connect(self._select_slider_zoom)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.fit_width_button.clicked.connect(self.fit_to_width)
        self.dock_toggle_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_TitleBarNormalButton))
        self.dock_toggle_button.clicked.connect(self.dockToggleRequested)
        self.hide_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_TitleBarMinButton))
        self.hide_button.clicked.connect(self.hideRequested)
        self.close_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_DialogCloseButton))
        self.close_button.clicked.connect(self.closeRequested)
        self.page_label.setBackgroundRole(qtg.QPalette.Base)
        scroll_contents = self.scroll_area.takeWidget()
        self.page_label.setParent(self.scroll_area)
        self.scroll_area.setWidget(self.page_label)
        scroll_contents.deleteLater()

        if preloaded_page_count is None:
            self._load_document()
        else:
            self._apply_loaded_page(int(preloaded_page_count), preloaded_image_path)
        self._initial_fit_pending = True

    @property
    def renderer_path(self):
        return _renderer_path()

    def _run_renderer(self, *arguments):
        return _run_pdf_renderer(*arguments)

    def _load_document(self):
        self.page_count = _source_page_count(self.pdf_path)
        if self.page_count < 2:
            raise ValueError(
                "Source reader requires a multi-page document containing at least two pages."
            )

        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, self.page_count)
        self.page_spin.setValue(1)
        self.page_spin.blockSignals(False)
        self.page_count_label.setText(f"of {self.page_count}")
        self._render_page(0)

    def _apply_loaded_page(self, page_count, image_path):
        self.page_count = page_count
        if self.page_count < 2:
            raise ValueError(
                "Source reader requires a multi-page document containing at least two pages."
            )
        pixmap = qtg.QPixmap(image_path)
        if pixmap.isNull():
            raise ValueError("The source reader returned an empty page image.")
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, self.page_count)
        self.page_spin.setValue(1)
        self.page_spin.blockSignals(False)
        self.page_count_label.setText(f"of {self.page_count}")
        self.page_index = 0
        self._rendered_pixmap = pixmap
        self.page_label.setPixmap(self._rendered_pixmap)
        self.page_label.setFixedSize(self._rendered_pixmap.size())
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(self.page_count > 1)
        self._update_zoom_buttons()

    def _render_page(self, page_index):
        output_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        output_path = output_file.name
        output_file.close()
        try:
            fit_width = max(200, self.scroll_area.viewport().width() - 4)
            render_width = fit_width if self.fit_width else max(200, round(800 * self.zoom_percent / 100))
            _render_source_page(self.pdf_path, page_index, render_width, output_path)
            pixmap = qtg.QPixmap(output_path)
            if pixmap.isNull():
                raise ValueError("The source reader returned an empty page image.")
            self.page_index = page_index
            self._rendered_pixmap = pixmap
            self.page_label.setPixmap(self._rendered_pixmap)
            self.page_label.setFixedSize(self._rendered_pixmap.size())
            self.scroll_area.ensureVisible(0, 0, 0, 0)
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(page_index + 1)
            self.page_spin.blockSignals(False)
            self.previous_button.setEnabled(page_index > 0)
            self.next_button.setEnabled(page_index < self.page_count - 1)
            self._update_zoom_buttons()
        finally:
            try:
                os.remove(output_path)
            except OSError:
                pass

    def _select_page(self, page_number):
        self._render_page(page_number - 1)

    def previous_page(self):
        if self.page_index > 0:
            self._render_page(self.page_index - 1)

    def next_page(self):
        if self.page_index < self.page_count - 1:
            self._render_page(self.page_index + 1)

    def _select_zoom(self, zoom_text):
        try:
            zoom_percent = int(str(zoom_text).rstrip("%"))
        except ValueError:
            return
        self.zoom_percent = zoom_percent
        self.fit_width = False
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(zoom_percent)
        self.zoom_slider.blockSignals(False)
        self._render_page(self.page_index)

    def _select_slider_zoom(self, zoom_percent):
        self.zoom_percent = int(zoom_percent)
        self.fit_width = False
        zoom_text = f"{self.zoom_percent}%"
        if self.zoom_combo.findText(zoom_text) >= 0:
            self.zoom_combo.blockSignals(True)
            self.zoom_combo.setCurrentText(zoom_text)
            self.zoom_combo.blockSignals(False)
        self._render_page(self.page_index)

    def _set_zoom(self, zoom_percent):
        bounded_zoom = min(self.ZOOM_LEVELS[-1], max(self.ZOOM_LEVELS[0], int(zoom_percent)))
        self.zoom_combo.setCurrentText(f"{bounded_zoom}%")

    def zoom_out(self):
        current_zoom = self.zoom_percent if not self.fit_width else 100
        lower_levels = [level for level in self.ZOOM_LEVELS if level < current_zoom]
        self._set_zoom(lower_levels[-1] if lower_levels else self.ZOOM_LEVELS[0])

    def zoom_in(self):
        current_zoom = self.zoom_percent if not self.fit_width else 100
        higher_levels = [level for level in self.ZOOM_LEVELS if level > current_zoom]
        self._set_zoom(higher_levels[0] if higher_levels else self.ZOOM_LEVELS[-1])

    def fit_to_width(self):
        self.fit_width = True
        self._render_page(self.page_index)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._initial_fit_pending:
            return
        self._initial_fit_pending = False
        qtc.QTimer.singleShot(0, self._apply_initial_fit_width)

    def _apply_initial_fit_width(self):
        if self._rendered_pixmap.isNull():
            return
        self.fit_width = True
        for _attempt in range(2):
            render_width = max(200, self.scroll_area.viewport().width() - 4)
            if self._rendered_pixmap.width() == render_width:
                break
            self._rendered_pixmap = self._rendered_pixmap.scaledToWidth(
                render_width,
                qtc.Qt.SmoothTransformation,
            )
            self.page_label.setPixmap(self._rendered_pixmap)
            self.page_label.setFixedSize(self._rendered_pixmap.size())
            qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 10)
        self._update_zoom_buttons()

    def _update_zoom_buttons(self):
        effective_zoom = self.zoom_percent if not self.fit_width else 100
        self.zoom_out_button.setEnabled(self.fit_width or effective_zoom > self.ZOOM_LEVELS[0])
        self.zoom_in_button.setEnabled(self.fit_width or effective_zoom < self.ZOOM_LEVELS[-1])


class SourceReaderDialog(qtw.QDialog):
    def __init__(self, pdf_path, parent=None, preloaded_page_count=None, preloaded_image_path=""):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowModality(qtc.Qt.NonModal)
        self.viewer = SourceReaderWidget(
            pdf_path,
            self,
            preloaded_page_count=preloaded_page_count,
            preloaded_image_path=preloaded_image_path,
        )
        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewer)
        self.setWindowTitle(f"Source Reader - {os.path.basename(self.viewer.pdf_path)}")
        self.resize(1000, 800)
        self.viewer.dock_toggle_button.hide()
        self.viewer.openRequested.connect(self._open_another_document)
        self.viewer.closeRequested.connect(self.close)
        self.viewer.hideRequested.connect(self.hide)

    def _open_another_document(self):
        source_path = _choose_source_document(self, self.viewer.pdf_path)
        if not source_path:
            return
        try:
            replacement = SourceReaderWidget(source_path, self)
        except (RuntimeError, ValueError) as exc:
            qtw.QMessageBox.warning(self, "Open Source Document", str(exc))
            return
        replacement.dock_toggle_button.hide()
        replacement.openRequested.connect(self._open_another_document)
        replacement.closeRequested.connect(self.close)
        replacement.hideRequested.connect(self.hide)
        previous = self.viewer
        self.layout().replaceWidget(previous, replacement)
        self.viewer = replacement
        self.setWindowTitle(f"Source Reader - {os.path.basename(source_path)}")
        previous.deleteLater()

    def __getattr__(self, name):
        viewer = self.__dict__.get("viewer")
        if viewer is not None and hasattr(viewer, name):
            return getattr(viewer, name)
        raise AttributeError(name)


class SourceReaderDock(qtw.QDockWidget):
    readerVisibilityChanged = qtc.pyqtSignal(bool)
    loadProgress = qtc.pyqtSignal(int, str)
    documentLoaded = qtc.pyqtSignal(str, int)
    documentReplaced = qtc.pyqtSignal(str, int)
    loadFailed = qtc.pyqtSignal(str)
    DOCK_PANEL_WIDTH = 420

    def __init__(self, pdf_path, parent=None, embedded_host=None):
        super().__init__(f"Source Reader - {os.path.basename(pdf_path)}", parent)
        self.pdf_path = os.path.abspath(pdf_path)
        self._automatic_close = False
        self._embedded_host = embedded_host
        self._embedded = False
        self._parent_window = parent if isinstance(parent, qtw.QMainWindow) else None
        self._parent_default_geometry = None
        self._parent_window_expanded = False
        self._source_load_thread = None
        self._source_load_worker = None
        self._pending_load_result = None
        self._pending_load_error = None
        self._loading_replacement = False
        self._pending_close_after_load = False
        self.viewer = None
        self._loading_widget = qtw.QWidget(self)
        loading_layout = qtw.QVBoxLayout(self._loading_widget)
        loading_layout.addStretch(1)
        self._loading_label = qtw.QLabel("Preparing source document...", self._loading_widget)
        self._loading_label.setAlignment(qtc.Qt.AlignCenter)
        loading_layout.addWidget(self._loading_label)
        self._loading_progress = qtw.QProgressBar(self._loading_widget)
        self._loading_progress.setRange(0, 100)
        self._loading_progress.setValue(0)
        loading_layout.addWidget(self._loading_progress)
        loading_layout.addStretch(1)
        self.setWidget(self._loading_widget)
        self.setMinimumWidth(320)
        self.setAllowedAreas(qtc.Qt.LeftDockWidgetArea)
        self.setFeatures(
            qtw.QDockWidget.DockWidgetClosable
            | qtw.QDockWidget.DockWidgetMovable
            | qtw.QDockWidget.DockWidgetFloatable
        )
        self.setAttribute(qtc.Qt.WA_DeleteOnClose, True)
        self.visibilityChanged.connect(self._relay_dock_visibility)
        self.topLevelChanged.connect(self._on_top_level_changed)
        self._sync_dock_button(self.isFloating())
        qtc.QTimer.singleShot(0, self._start_source_load)

    @property
    def page_count(self):
        return self.viewer.page_count if self.viewer is not None else 0

    @property
    def is_loading(self):
        return self._source_load_thread is not None

    def is_reader_visible(self):
        if self._embedded:
            return self._embedded_host.isVisible()
        return self.isVisible()

    def is_reader_floating(self):
        return not self._embedded and self.isFloating()

    def set_reader_visible(self, visible):
        if self._embedded:
            self._embedded_host.setVisible(bool(visible))
            if visible and self.viewer is not None:
                self.viewer.show()
                self._embedded_host.raise_()
            elif self.viewer is not None:
                self.viewer.hide()
        else:
            self.setVisible(bool(visible))
        self.readerVisibilityChanged.emit(bool(visible))

    def show_reader(self):
        self.set_reader_visible(True)
        self._start_source_load()
        if not self.is_reader_floating():
            self._expand_parent_window()

    def hide_reader(self):
        self.set_reader_visible(False)

    def dock_in_host(self, visible=True):
        if self._embedded_host is None:
            if visible:
                self.show()
            return
        self._embedded = True
        super().hide()
        content_widget = self.viewer or self._loading_widget
        content_widget.setParent(self._embedded_host)
        self._embedded_host.layout().addWidget(content_widget)
        self._sync_dock_button(False)
        self.set_reader_visible(visible)

    def float_reader(self):
        if self._embedded:
            was_visible = self._embedded_host.isVisible()
            content_widget = self.viewer or self._loading_widget
            self._embedded_host.layout().removeWidget(content_widget)
            self._embedded_host.hide()
            content_widget.setParent(self)
            self.setWidget(content_widget)
            self._embedded = False
        else:
            was_visible = self.isVisible()
        if not self.isFloating():
            self.setFloating(True)
        self._restore_parent_window()
        self.resize(1000, 800)
        if was_visible:
            self.show()
            self.raise_()
            self.activateWindow()
        self._sync_dock_button(True)
        self.readerVisibilityChanged.emit(was_visible)

    def toggle_floating(self):
        if self._embedded:
            self.float_reader()
        elif self._embedded_host is not None:
            self.dock_in_host(self.isVisible())
        else:
            self.setFloating(not self.isFloating())
            if self.isFloating():
                self.resize(1000, 800)
                self.raise_()
                self.activateWindow()

    def close_automatically(self):
        self._automatic_close = True
        self.close()

    def _relay_dock_visibility(self, visible):
        if not self._embedded:
            self.readerVisibilityChanged.emit(visible)

    def _sync_dock_button(self, floating):
        if self.viewer is None:
            return
        action = "Dock" if floating else "Undock"
        self.viewer.dock_toggle_button.setToolTip(f"{action} Source Reader")

    def _start_source_load(self, source_path=None, replacement=False):
        if self._source_load_thread is not None:
            return
        if self.viewer is not None and not replacement:
            return
        source_path = os.path.abspath(source_path or self.pdf_path)
        _validate_source_document_type(source_path)
        self._loading_replacement = bool(replacement)
        if self.viewer is not None:
            self.viewer.open_button.setEnabled(False)
        self._loading_progress.setValue(0)
        self._loading_progress.show()
        self._loading_label.setText("Preparing source document...")
        thread = qtc.QThread(self)
        worker = SourceDocumentLoadWorker(source_path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_source_load_progress)
        worker.loaded.connect(self._on_source_document_loaded)
        worker.failed.connect(self._on_source_document_load_failed)
        worker.loaded.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.loaded.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_source_load_thread_finished)
        self._source_load_thread = thread
        self._source_load_worker = worker
        thread.start()

    def _on_source_load_progress(self, value, message):
        self._loading_progress.setValue(int(value))
        self._loading_label.setText(str(message))
        self.loadProgress.emit(int(value), str(message))

    def _on_source_document_loaded(self, source_path, page_count, image_path):
        try:
            self._loading_progress.setValue(100)
            viewer = SourceReaderWidget(
                source_path,
                self,
                preloaded_page_count=page_count,
                preloaded_image_path=image_path,
            )
            viewer.closeRequested.connect(self.close)
            viewer.hideRequested.connect(self.hide_reader)
            viewer.dockToggleRequested.connect(self.toggle_floating)
            viewer.openRequested.connect(self._open_another_document)
            previous_viewer = self.viewer
            self.viewer = viewer
            if self._embedded:
                if previous_viewer is not None:
                    self._embedded_host.layout().removeWidget(previous_viewer)
                else:
                    self._embedded_host.layout().removeWidget(self._loading_widget)
                viewer.setParent(self._embedded_host)
                self._embedded_host.layout().addWidget(viewer)
                if self._embedded_host.isVisible():
                    viewer.show()
            else:
                self.setWidget(viewer)
            if previous_viewer is not None:
                previous_viewer.deleteLater()
            self.pdf_path = os.path.abspath(source_path)
            self.setWindowTitle(f"Source Reader - {os.path.basename(source_path)}")
            self._sync_dock_button(self.isFloating())
            self._pending_load_result = (
                source_path,
                int(page_count),
                self._loading_replacement,
            )
        except (RuntimeError, ValueError) as exc:
            self._on_source_document_load_failed(str(exc))
        finally:
            try:
                os.remove(image_path)
            except OSError:
                pass

    def _on_source_document_load_failed(self, message):
        if self._loading_replacement and self.viewer is not None:
            self.viewer.open_button.setEnabled(True)
            qtw.QMessageBox.warning(self, "Open Source Document", str(message))
            self._pending_load_error = ""
        else:
            self._loading_label.setText("Source document could not be loaded.")
            self._loading_progress.hide()
            self._pending_load_error = str(message)

    def _on_source_load_thread_finished(self):
        self._source_load_thread = None
        self._source_load_worker = None
        if self._pending_load_error:
            message = self._pending_load_error
            self._pending_load_error = None
            self.loadFailed.emit(message)
        elif self._pending_load_result is not None:
            source_path, page_count, replacement = self._pending_load_result
            self._pending_load_result = None
            if replacement:
                self.documentReplaced.emit(source_path, page_count)
            else:
                self.documentLoaded.emit(source_path, page_count)
        self._pending_load_error = None
        self._loading_replacement = False
        if self._pending_close_after_load:
            self._pending_close_after_load = False
            qtc.QTimer.singleShot(0, self.close)

    def _open_another_document(self):
        source_path = _choose_source_document(self, self.pdf_path)
        if not source_path:
            return
        try:
            self._start_source_load(source_path, replacement=True)
        except ValueError as exc:
            qtw.QMessageBox.warning(self, "Open Source Document", str(exc))

    def _on_top_level_changed(self, floating):
        self._sync_dock_button(floating)
        if floating:
            self._restore_parent_window()
        elif self.isVisible():
            self._expand_parent_window()

    def _expand_parent_window(self):
        window = self._parent_window
        if window is None or self._embedded or self.isFloating() or self._parent_window_expanded:
            return
        if window.isMaximized() or window.isFullScreen():
            return

        self._parent_default_geometry = qtc.QByteArray(window.saveGeometry())
        current_geometry = window.geometry()
        target_width = current_geometry.width() + self.DOCK_PANEL_WIDTH
        screen = window.screen() or qtw.QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            target_width = max(current_geometry.width(), min(target_width, available.width()))
            target_x = min(current_geometry.x(), available.right() - target_width + 1)
            target_x = max(available.x(), target_x)
        else:
            target_x = current_geometry.x()
        if target_width <= current_geometry.width():
            self._parent_default_geometry = None
            return

        window.setGeometry(target_x, current_geometry.y(), target_width, current_geometry.height())
        self._parent_window_expanded = True

    def _restore_parent_window(self):
        if not self._parent_window_expanded or self._parent_window is None:
            return
        self._parent_window.restoreGeometry(self._parent_default_geometry)
        self._parent_default_geometry = None
        self._parent_window_expanded = False

    def closeEvent(self, event):
        if self._source_load_thread is not None:
            if self._automatic_close:
                self._pending_close_after_load = True
                self.hide()
                self._restore_parent_window()
            else:
                qtw.QMessageBox.information(
                    self,
                    "Source Document Loading",
                    "Wait for the source document to finish loading before closing the reader.",
                )
            event.ignore()
            return
        if not self._automatic_close:
            answer = qtw.QMessageBox.question(
                self,
                "Close Source Reader",
                "Are you sure you want to close the Source Reader?",
                qtw.QMessageBox.Yes | qtw.QMessageBox.No,
                qtw.QMessageBox.No,
            )
            if answer != qtw.QMessageBox.Yes:
                event.ignore()
                return
        self._restore_parent_window()
        if self._embedded:
            content_widget = self.viewer or self._loading_widget
            self._embedded_host.layout().removeWidget(content_widget)
            self._embedded_host.hide()
            content_widget.setParent(self)
            self.setWidget(content_widget)
            self._embedded = False
            self.readerVisibilityChanged.emit(False)
        event.accept()