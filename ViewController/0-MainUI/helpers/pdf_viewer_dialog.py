from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


class PdfViewerWidget(qtw.QWidget):
    closeRequested = qtc.pyqtSignal()
    hideRequested = qtc.pyqtSignal()
    dockToggleRequested = qtc.pyqtSignal()

    ZOOM_LEVELS = (25, 50, 75, 100, 125, 150, 175, 200)

    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = os.path.abspath(pdf_path)
        self.page_count = 0
        self.page_index = 0
        self.zoom_percent = 100
        self.fit_width = True
        self._rendered_pixmap = qtg.QPixmap()

        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.toolbar_widget = qtw.QWidget(self)
        toolbar_font = self.toolbar_widget.font()
        if toolbar_font.pointSizeF() > 0:
            toolbar_font.setPointSizeF(max(8.0, toolbar_font.pointSizeF() - 1.0))
        self.toolbar_widget.setFont(toolbar_font)
        toolbar = qtw.QGridLayout(self.toolbar_widget)
        toolbar.setContentsMargins(0, 0, 0, 2)
        toolbar.setHorizontalSpacing(3)
        toolbar.setVerticalSpacing(2)
        toolbar.setColumnStretch(5, 1)

        self.previous_button = qtw.QToolButton(self)
        self.previous_button.setArrowType(qtc.Qt.LeftArrow)
        self.previous_button.setToolTip("Previous page")
        self.previous_button.clicked.connect(self.previous_page)
        toolbar.addWidget(self.previous_button, 0, 0)

        self.next_button = qtw.QToolButton(self)
        self.next_button.setArrowType(qtc.Qt.RightArrow)
        self.next_button.setToolTip("Next page")
        self.next_button.clicked.connect(self.next_page)
        toolbar.addWidget(self.next_button, 0, 1)

        toolbar.addWidget(qtw.QLabel("Page", self), 0, 2)
        self.page_spin = qtw.QSpinBox(self)
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximumWidth(58)
        self.page_spin.valueChanged.connect(self._select_page)
        toolbar.addWidget(self.page_spin, 0, 3)

        self.page_count_label = qtw.QLabel("of 0", self)
        toolbar.addWidget(self.page_count_label, 0, 4)

        self.zoom_out_button = qtw.QToolButton(self)
        self.zoom_out_button.setText("-")
        self.zoom_out_button.setToolTip("Zoom out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        toolbar.addWidget(self.zoom_out_button, 1, 0)

        self.zoom_combo = qtw.QComboBox(self)
        self.zoom_combo.addItems([f"{level}%" for level in self.ZOOM_LEVELS])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setMaximumWidth(72)
        self.zoom_combo.setToolTip("Zoom level")
        self.zoom_combo.currentTextChanged.connect(self._select_zoom)
        toolbar.addWidget(self.zoom_combo, 1, 1)

        self.zoom_slider = qtw.QSlider(qtc.Qt.Horizontal, self)
        self.zoom_slider.setRange(self.ZOOM_LEVELS[0], self.ZOOM_LEVELS[-1])
        self.zoom_slider.setSingleStep(5)
        self.zoom_slider.setPageStep(25)
        self.zoom_slider.setValue(self.zoom_percent)
        self.zoom_slider.setMinimumWidth(72)
        self.zoom_slider.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
        self.zoom_slider.setToolTip("Zoom level")
        self.zoom_slider.valueChanged.connect(self._select_slider_zoom)
        toolbar.addWidget(self.zoom_slider, 1, 2, 1, 4)

        self.zoom_in_button = qtw.QToolButton(self)
        self.zoom_in_button.setText("+")
        self.zoom_in_button.setToolTip("Zoom in")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        toolbar.addWidget(self.zoom_in_button, 1, 6)

        self.fit_width_button = qtw.QToolButton(self)
        self.fit_width_button.setText("Fit Width")
        self.fit_width_button.setToolTip("Fit the page to the viewer width")
        self.fit_width_button.clicked.connect(self.fit_to_width)
        toolbar.addWidget(self.fit_width_button, 1, 7, 1, 3)

        self.dock_toggle_button = qtw.QToolButton(self)
        self.dock_toggle_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_TitleBarNormalButton))
        self.dock_toggle_button.setToolTip("Dock or undock source viewer")
        self.dock_toggle_button.clicked.connect(self.dockToggleRequested)
        toolbar.addWidget(self.dock_toggle_button, 0, 7)

        self.hide_button = qtw.QToolButton(self)
        self.hide_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_TitleBarMinButton))
        self.hide_button.setToolTip("Hide source viewer")
        self.hide_button.clicked.connect(self.hideRequested)
        toolbar.addWidget(self.hide_button, 0, 8)

        self.close_button = qtw.QToolButton(self)
        self.close_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_DialogCloseButton))
        self.close_button.setToolTip("Close source viewer")
        self.close_button.clicked.connect(self.closeRequested)
        toolbar.addWidget(self.close_button, 0, 9)
        layout.addWidget(self.toolbar_widget)

        self.scroll_area = qtw.QScrollArea(self)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.page_label = qtw.QLabel(self.scroll_area)
        self.page_label.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.page_label.setBackgroundRole(qtg.QPalette.Base)
        self.page_label.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)
        self.scroll_area.setWidget(self.page_label)
        layout.addWidget(self.scroll_area, 1)

        self._load_document()

    @property
    def renderer_path(self):
        return os.path.join(os.path.dirname(__file__), "qt_pdf_renderer.py")

    def _run_renderer(self, *arguments):
        try:
            return subprocess.run(
                [sys.executable, self.renderer_path, *[str(argument) for argument in arguments]],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            if "PyQt6" in detail or "QtPdf" in detail:
                detail = "QtPdf support requires PyQt6 6.10 or newer in the active Python environment."
            raise RuntimeError(detail.strip()) from exc

    def _load_document(self):
        result = self._run_renderer("metadata", self.pdf_path)
        metadata = json.loads(result.stdout)
        self.page_count = int(metadata.get("page_count", 0))
        if self.page_count < 1:
            raise ValueError("The PDF contains no readable pages.")

        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, self.page_count)
        self.page_spin.setValue(1)
        self.page_spin.blockSignals(False)
        self.page_count_label.setText(f"of {self.page_count}")
        self._render_page(0)

    def _render_page(self, page_index):
        output_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        output_path = output_file.name
        output_file.close()
        try:
            fit_width = max(200, self.scroll_area.viewport().width() - 4)
            render_width = fit_width if self.fit_width else max(200, round(800 * self.zoom_percent / 100))
            self._run_renderer("render", self.pdf_path, page_index, render_width, output_path)
            pixmap = qtg.QPixmap(output_path)
            if pixmap.isNull():
                raise ValueError("QtPdf returned an empty page image.")
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

    def _update_zoom_buttons(self):
        effective_zoom = self.zoom_percent if not self.fit_width else 100
        self.zoom_out_button.setEnabled(self.fit_width or effective_zoom > self.ZOOM_LEVELS[0])
        self.zoom_in_button.setEnabled(self.fit_width or effective_zoom < self.ZOOM_LEVELS[-1])


class PdfViewerDialog(qtw.QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.viewer = PdfViewerWidget(pdf_path, self)
        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewer)
        self.setWindowTitle(f"Source PDF - {os.path.basename(self.viewer.pdf_path)}")
        self.resize(1000, 800)
        self.viewer.dock_toggle_button.hide()
        self.viewer.closeRequested.connect(self.close)
        self.viewer.hideRequested.connect(self.hide)

    def __getattr__(self, name):
        viewer = self.__dict__.get("viewer")
        if viewer is not None and hasattr(viewer, name):
            return getattr(viewer, name)
        raise AttributeError(name)


class PdfViewerDock(qtw.QDockWidget):
    viewerVisibilityChanged = qtc.pyqtSignal(bool)

    def __init__(self, pdf_path, parent=None, embedded_host=None):
        super().__init__(f"Source PDF - {os.path.basename(pdf_path)}", parent)
        self.pdf_path = os.path.abspath(pdf_path)
        self._automatic_close = False
        self._embedded_host = embedded_host
        self._embedded = False
        self.viewer = PdfViewerWidget(self.pdf_path, self)
        self.setWidget(self.viewer)
        self.setAllowedAreas(qtc.Qt.LeftDockWidgetArea)
        self.setFeatures(
            qtw.QDockWidget.DockWidgetClosable
            | qtw.QDockWidget.DockWidgetMovable
            | qtw.QDockWidget.DockWidgetFloatable
        )
        self.setAttribute(qtc.Qt.WA_DeleteOnClose, True)
        self.viewer.closeRequested.connect(self.close)
        self.viewer.hideRequested.connect(self.hide_viewer)
        self.viewer.dockToggleRequested.connect(self.toggle_floating)
        self.visibilityChanged.connect(self._relay_dock_visibility)
        self.topLevelChanged.connect(self._sync_dock_button)
        self._sync_dock_button(self.isFloating())

    @property
    def page_count(self):
        return self.viewer.page_count

    def is_viewer_visible(self):
        if self._embedded:
            return self._embedded_host.isVisible()
        return self.isVisible()

    def is_viewer_floating(self):
        return not self._embedded and self.isFloating()

    def set_viewer_visible(self, visible):
        if self._embedded:
            self._embedded_host.setVisible(bool(visible))
            if visible:
                self._embedded_host.raise_()
        else:
            self.setVisible(bool(visible))
        self.viewerVisibilityChanged.emit(bool(visible))

    def show_viewer(self):
        self.set_viewer_visible(True)

    def hide_viewer(self):
        self.set_viewer_visible(False)

    def dock_in_host(self, visible=True):
        if self._embedded_host is None:
            if visible:
                self.show()
            return
        self._embedded = True
        super().hide()
        self.viewer.setParent(self._embedded_host)
        self._embedded_host.layout().addWidget(self.viewer)
        self._sync_dock_button(False)
        self.set_viewer_visible(visible)

    def float_viewer(self):
        if self._embedded:
            was_visible = self._embedded_host.isVisible()
            self._embedded_host.layout().removeWidget(self.viewer)
            self._embedded_host.hide()
            self.viewer.setParent(self)
            self.setWidget(self.viewer)
            self._embedded = False
        else:
            was_visible = self.isVisible()
        if not self.isFloating():
            self.setFloating(True)
        self.resize(1000, 800)
        if was_visible:
            self.show()
            self.raise_()
            self.activateWindow()
        self._sync_dock_button(True)
        self.viewerVisibilityChanged.emit(was_visible)

    def toggle_floating(self):
        if self._embedded:
            self.float_viewer()
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
            self.viewerVisibilityChanged.emit(visible)

    def _sync_dock_button(self, floating):
        action = "Dock" if floating else "Undock"
        self.viewer.dock_toggle_button.setToolTip(f"{action} source viewer")

    def closeEvent(self, event):
        if not self._automatic_close:
            answer = qtw.QMessageBox.question(
                self,
                "Close Source Viewer",
                "Are you sure you want to close the source document viewer?",
                qtw.QMessageBox.Yes | qtw.QMessageBox.No,
                qtw.QMessageBox.No,
            )
            if answer != qtw.QMessageBox.Yes:
                event.ignore()
                return
        if self._embedded:
            self._embedded_host.layout().removeWidget(self.viewer)
            self._embedded_host.hide()
            self.viewer.setParent(self)
            self.setWidget(self.viewer)
            self._embedded = False
            self.viewerVisibilityChanged.emit(False)
        event.accept()