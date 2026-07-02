import os
import subprocess
import sys
import time
from datetime import datetime

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


class FileDragTreeView(qtw.QTreeView):
    def startDrag(self, supported_actions):
        index = self.currentIndex()
        model = self.model()
        if not index.isValid() or model is None or not hasattr(model, 'filePath'):
            return super().startDrag(supported_actions)

        file_path = model.filePath(index)
        if not file_path or not os.path.isfile(file_path):
            return super().startDrag(supported_actions)

        mime_data = qtc.QMimeData()
        mime_data.setUrls([qtc.QUrl.fromLocalFile(file_path)])

        drag = qtg.QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec_(qtc.Qt.CopyAction)


class FilePickerDialog(qtw.QDialog):
    def __init__(self, title, directory, selected_handler, name_filters=None, parent=None):
        super().__init__(parent)
        self.selected_handler = selected_handler
        self.setWindowTitle(title)
        self.setWindowModality(qtc.Qt.NonModal)
        self.setAttribute(qtc.Qt.WA_DeleteOnClose, True)
        self.resize(800, 500)

        start_directory = directory or os.getcwd()
        if not os.path.isdir(start_directory):
            start_directory = os.path.dirname(start_directory) or os.getcwd()

        self.model = qtw.QFileSystemModel(self)
        self.model.setFilter(qtc.QDir.AllDirs | qtc.QDir.Files | qtc.QDir.NoDotAndDotDot)
        self.model.setNameFilters(name_filters or ['*'])
        self.model.setNameFilterDisables(False)
        self.model.setReadOnly(True)
        self.model.setRootPath(start_directory)

        self.path_edit = qtw.QLineEdit(start_directory)
        self.up_button = qtw.QPushButton('Up')
        self.open_button = qtw.QPushButton('Open')
        self.close_button = qtw.QPushButton('Close')
        self.hint_label = qtw.QLabel('Drag a file to the application, double-click a file, or select a file and click Open.')

        self.tree = FileDragTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(start_directory))
        self.tree.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(qtw.QAbstractItemView.DragOnly)
        self.tree.setDefaultDropAction(qtc.Qt.CopyAction)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, qtc.Qt.AscendingOrder)

        top_layout = qtw.QHBoxLayout()
        top_layout.addWidget(self.path_edit, 1)
        top_layout.addWidget(self.up_button)

        button_layout = qtw.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.close_button)

        layout = qtw.QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.tree, 1)
        layout.addLayout(button_layout)

        self.path_edit.returnPressed.connect(self._go_to_path)
        self.up_button.clicked.connect(self._go_up)
        self.open_button.clicked.connect(self._open_current)
        self.close_button.clicked.connect(self.close)
        self.tree.doubleClicked.connect(self._open_or_enter)

    def _set_root_path(self, path):
        if not path or not os.path.isdir(path):
            return
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path))
        self.path_edit.setText(path)

    def _go_to_path(self):
        self._set_root_path(self.path_edit.text())

    def _go_up(self):
        current = self.path_edit.text()
        parent = os.path.dirname(current)
        if parent and parent != current:
            self._set_root_path(parent)

    def _open_or_enter(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self._set_root_path(path)
        elif os.path.isfile(path):
            self._select_file(path)

    def _open_current(self):
        path = self.model.filePath(self.tree.currentIndex())
        if os.path.isdir(path):
            self._set_root_path(path)
        elif os.path.isfile(path):
            self._select_file(path)

    def _select_file(self, path):
        self.selected_handler(path)
        self.close()


class LocalFileDropMixin:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
    TEXT_EXTENSIONS = {".txt", ".nt", ".md", ".json", ".csv", ".tsv", ".xml", ".html", ".htm", ".ris"}
    FILE_DROP_DEBUG = True
    FILE_DROP_DEBUG_LOG = os.path.join(os.path.dirname(__file__), "file_drop_debug.log")

    TEXT_NAME_FILTERS = ["*.txt", "*.nt", "*.md", "*.json", "*.csv", "*.tsv", "*.xml", "*.html", "*.htm", "*.ris"]
    IMAGE_NAME_FILTERS = ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp", "*.gif", "*.webp"]

    def _module_progress_label(self):
        title = self.windowTitle() if hasattr(self, "windowTitle") else ""
        return title or self.__class__.__name__

    def progress_message(self, message, end="\n"):
        print(f"[{self._module_progress_label()}] {message}", end=end, flush=True)

    @staticmethod
    def format_size(byte_count):
        byte_count = float(byte_count)
        for unit in ("B", "KB", "MB", "GB"):
            if byte_count < 1024 or unit == "GB":
                return f"{byte_count:.1f} {unit}" if unit != "B" else f"{int(byte_count)} {unit}"
            byte_count /= 1024

    def run_with_terminal_spinner(self, message, func):
        spinner_code = (
            "import sys,time; "
            f"message={message!r}; prefix={self._module_progress_label()!r}; "
            "frames='|/-\\\\'; start=time.time(); i=0; "
            "\nwhile True:\n"
            "    elapsed=int(time.time()-start)\n"
            "    sys.stdout.write(f'\\r[{prefix}] {message} {frames[i % len(frames)]} {elapsed}s elapsed')\n"
            "    sys.stdout.flush()\n"
            "    i += 1\n"
            "    time.sleep(0.5)\n"
        )
        spinner = subprocess.Popen([sys.executable, "-u", "-c", spinner_code])
        try:
            return func()
        finally:
            spinner.terminate()
            try:
                spinner.wait(timeout=1)
            except subprocess.TimeoutExpired:
                spinner.kill()
            print(f"\r[{self._module_progress_label()}] {message} complete           ", flush=True)

    def begin_visible_file_load(self, label, path):
        name = os.path.basename(path) if path else "file"
        message = f"{label}: loading {name} -- please wait..."
        self.progress_message(message)
        statusbar = getattr(getattr(self, "ui", None), "statusbar", None)
        if statusbar is not None:
            statusbar.showMessage(message)
        qtw.QApplication.setOverrideCursor(qtc.Qt.WaitCursor)
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)

    def end_visible_file_load(self, label):
        try:
            qtw.QApplication.restoreOverrideCursor()
        except Exception:
            pass
        message = f"{label}: load complete"
        self.progress_message(message)
        statusbar = getattr(getattr(self, "ui", None), "statusbar", None)
        if statusbar is not None:
            statusbar.showMessage(message, 5000)
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)

    def run_file_handler_with_feedback(self, label, file_path, handler):
        self.begin_visible_file_load(label, file_path)
        try:
            return handler(file_path)
        finally:
            self.end_visible_file_load(label)

    def open_non_modal_file_picker(self, title, directory, selected_handler, dialog_attr_name, name_filters=None):
        dialog = FilePickerDialog(title, directory, selected_handler, name_filters=name_filters, parent=self)
        setattr(self, dialog_attr_name, dialog)
        dialog.destroyed.connect(lambda *_: setattr(self, dialog_attr_name, None))
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def open_non_modal_text_picker(self, title, directory, selected_handler, dialog_attr_name):
        def wrapped(path):
            return self.run_file_handler_with_feedback("Text file", path, selected_handler)

        return self.open_non_modal_file_picker(title, directory, wrapped, dialog_attr_name, self.TEXT_NAME_FILTERS)

    def open_non_modal_image_picker(self, title, directory, selected_handler, dialog_attr_name):
        def wrapped(path):
            return self.run_file_handler_with_feedback("Image file", path, selected_handler)

        return self.open_non_modal_file_picker(title, directory, wrapped, dialog_attr_name, self.IMAGE_NAME_FILTERS)

    def _ensure_file_drop_state(self):
        if not hasattr(self, "_file_drop_targets"):
            self._file_drop_targets = set()
        if not hasattr(self, "_file_drop_handlers"):
            self._file_drop_handlers = {}
        if not hasattr(self, "_file_drop_image_handler"):
            self._file_drop_image_handler = None
        if not hasattr(self, "_file_drop_text_handler"):
            self._file_drop_text_handler = None

    def install_local_file_drop(self, targets, image_handler=None, text_handler=None):
        self._ensure_file_drop_state()
        self._file_drop_targets.clear()
        self._file_drop_handlers.clear()
        self._file_drop_image_handler = image_handler
        self._file_drop_text_handler = text_handler

        for target in targets:
            if target is None:
                continue
            self._register_file_drop_target(target, image_handler=image_handler, text_handler=text_handler)

    def install_local_file_drop_target(self, target, image_handler=None, text_handler=None):
        self._ensure_file_drop_state()
        self._register_file_drop_target(target, image_handler=image_handler, text_handler=text_handler)

    def eventFilter(self, watched, event):
        if self.FILE_DROP_DEBUG:
            if event.type() in (qtc.QEvent.DragEnter, qtc.QEvent.DragMove, qtc.QEvent.Drop):
                self._debug_file_drop_event(watched, event, "global-event")

        if watched in getattr(self, "_file_drop_targets", set()):
            if event.type() in (qtc.QEvent.DragEnter, qtc.QEvent.DragMove):
                self._debug_file_drop_event(watched, event, "eventFilter-drag")
                if self._mime_has_local_urls(event.mimeData()):
                    event.acceptProposedAction()
                    return True
            elif event.type() == qtc.QEvent.Drop:
                self._debug_file_drop_event(watched, event, "eventFilter-drop")
                return self._handle_local_file_drop(watched, event)

        return super().eventFilter(watched, event)

    def _register_file_drop_target(self, widget, image_handler=None, text_handler=None):
        candidates = [widget]
        if hasattr(widget, "viewport"):
            viewport = widget.viewport()
            if viewport is not None:
                candidates.append(viewport)
        candidates.extend(widget.findChildren(qtw.QWidget))

        for target in candidates:
            if target in self._file_drop_targets:
                continue
            target.setAcceptDrops(True)
            target.installEventFilter(self)
            self._file_drop_targets.add(target)
            self._file_drop_handlers[target] = (image_handler, text_handler)

    def _handle_local_file_drop(self, watched, event):
        file_path = self.first_local_drop_path(event.mimeData())
        if not file_path:
            event.ignore()
            return True

        image_handler, text_handler = self._file_drop_handlers.get(
            watched,
            (self._file_drop_image_handler, self._file_drop_text_handler),
        )

        if self.is_image_file(file_path) and image_handler:
            self.run_file_handler_with_feedback("Image file", file_path, image_handler)
            event.acceptProposedAction()
            return True

        if self.is_text_file(file_path) and text_handler:
            self.run_file_handler_with_feedback("Text file", file_path, text_handler)
            event.acceptProposedAction()
            return True

        event.ignore()
        return True

    def _debug_file_drop_event(self, watched, event, stage):
        if not self.FILE_DROP_DEBUG:
            return
        mime_data = event.mimeData()
        urls = []
        if mime_data.hasUrls():
            urls = [url.toLocalFile() if url.isLocalFile() else url.toString() for url in mime_data.urls()]
        object_name = watched.objectName() if hasattr(watched, "objectName") else ""
        message = (
            f"[{datetime.now().isoformat(timespec='seconds')}] [FILE DROP DEBUG] "
            f"{stage} widget={watched.__class__.__name__} "
            f"name={object_name!r} hasUrls={mime_data.hasUrls()} urls={urls}"
        )
        print(message)
        try:
            with open(self.FILE_DROP_DEBUG_LOG, "a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except OSError:
            pass

    @classmethod
    def is_image_file(cls, file_path):
        return os.path.splitext(file_path)[1].lower() in cls.IMAGE_EXTENSIONS

    @classmethod
    def is_text_file(cls, file_path):
        return os.path.splitext(file_path)[1].lower() in cls.TEXT_EXTENSIONS

    @staticmethod
    def first_local_drop_path(mime_data):
        for url in mime_data.urls():
            if url.isLocalFile():
                return url.toLocalFile()
        return ""

    @staticmethod
    def _mime_has_local_urls(mime_data):
        if not mime_data.hasUrls():
            return False
        return any(url.isLocalFile() for url in mime_data.urls())
