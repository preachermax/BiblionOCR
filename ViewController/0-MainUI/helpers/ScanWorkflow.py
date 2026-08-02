from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw


class ScanWizardLoadWorker(qtc.QObject):
    finished = qtc.pyqtSignal(object)
    error = qtc.pyqtSignal(str)

    def __init__(self, scan_manager, request=None, load_backend_options=False, discover_devices=False):
        super().__init__()
        self.scan_manager = scan_manager
        self.request = request or {}
        self.load_backend_options = load_backend_options
        self.discover_devices = discover_devices

    def run(self):
        try:
            payload = {}
            if self.load_backend_options:
                payload["backend_options"] = self.scan_manager.backend_options()
            if self.discover_devices:
                payload["request"] = dict(self.request)
                payload["devices"] = self.scan_manager.discover_devices(self.request)
            self.finished.emit(payload)
        except Exception as exc:
            self.error.emit(str(exc))


class ScanWizardDialog(qtw.QDialog):

    def __init__(self, scan_manager, default_destination, parent=None, initial_request=None):
        super().__init__(parent)
        self.scan_manager = scan_manager
        self.default_destination = default_destination
        self.initial_request = self.scan_manager.default_request(default_destination)
        self.initial_request.update(initial_request or {})
        self._backend_options_cache = []
        self._backend_options_by_value = {}
        self._loading_backends = False
        self._loading_devices = False
        self._device_request_token = 0
        self._backend_loader_thread = None
        self._backend_loader_worker = None
        self._device_loader_thread = None
        self._device_loader_worker = None
        self._page_titles = [
            "Step 1 of 2: Scan source",
            "Step 2 of 2: Scan options",
        ]
        self.setWindowTitle("Scan Image")
        self.setModal(True)
        self.resize(640, 420)
        self._build_ui()
        self._apply_initial_request()
        self._start_backend_load()
        self._update_page_state()

    def _build_ui(self):
        layout = qtw.QVBoxLayout(self)
        layout.setSpacing(10)

        intro_label = qtw.QLabel(
            "Choose a scan backend, review the destination, and dispatch a normalized scan request into the Core scanner workflow."
        )
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        self.page_title_label = qtw.QLabel("")
        layout.addWidget(self.page_title_label)

        self.page_stack = qtw.QStackedWidget(self)
        layout.addWidget(self.page_stack, 1)

        source_page = qtw.QWidget()
        source_layout = qtw.QVBoxLayout(source_page)
        source_layout.setSpacing(10)
        source_layout.addWidget(qtw.QLabel("Backend selection"))

        self.backend_combo = qtw.QComboBox()
        self.backend_combo.addItem("Loading scanner backends...", None)
        self.backend_combo.setEnabled(False)
        source_layout.addWidget(self.backend_combo)

        self.loading_label = qtw.QLabel("Loading scanner backends...")
        self.loading_label.setWordWrap(True)
        source_layout.addWidget(self.loading_label)

        self.loading_progress = qtw.QProgressBar()
        self.loading_progress.setRange(0, 0)
        source_layout.addWidget(self.loading_progress)

        self.allow_network_fallback_checkbox = qtw.QCheckBox("Allow AirScan fallback while testing SANE")
        self.allow_network_fallback_checkbox.setChecked(bool(self.initial_request.get("allow_network_fallback", True)))
        source_layout.addWidget(self.allow_network_fallback_checkbox)

        source_layout.addWidget(qtw.QLabel("Device name (optional)"))
        self.device_name_edit = qtw.QLineEdit()
        self.device_name_edit.setPlaceholderText("Leave blank to use backend default device, or enter an AirScan IP/URL")
        source_layout.addWidget(self.device_name_edit)

        source_layout.addWidget(qtw.QLabel("Detected devices"))
        self.detected_devices_label = qtw.QLabel("Scanner discovery has not completed yet.")
        self.detected_devices_label.setWordWrap(True)
        source_layout.addWidget(self.detected_devices_label)
        source_layout.addStretch(1)
        self.page_stack.addWidget(source_page)

        options_page = qtw.QWidget()
        options_layout = qtw.QVBoxLayout(options_page)
        options_layout.setSpacing(10)
        options_layout.addWidget(qtw.QLabel("Destination folder"))

        self.destination_edit = qtw.QLineEdit(self.initial_request["destination_folder"])
        options_layout.addWidget(self.destination_edit)

        grid = qtw.QGridLayout()
        grid.addWidget(qtw.QLabel("Mode"), 0, 0)
        self.mode_combo = qtw.QComboBox()
        self.mode_combo.addItems(["color", "grayscale", "mono"])
        grid.addWidget(self.mode_combo, 0, 1)

        grid.addWidget(qtw.QLabel("DPI"), 1, 0)
        self.dpi_combo = qtw.QComboBox()
        self.dpi_combo.addItems(["150", "300", "600"])
        self.dpi_combo.setCurrentText("300")
        grid.addWidget(self.dpi_combo, 1, 1)

        grid.addWidget(qtw.QLabel("Source type"), 2, 0)
        self.source_type_combo = qtw.QComboBox()
        self.source_type_combo.addItems(["flatbed", "adf"])
        grid.addWidget(self.source_type_combo, 2, 1)

        grid.addWidget(qtw.QLabel("Persist format"), 3, 0)
        self.persist_format_combo = qtw.QComboBox()
        self.persist_format_combo.addItems(["tiff"])
        grid.addWidget(self.persist_format_combo, 3, 1)
        options_layout.addLayout(grid)

        self.duplex_checkbox = qtw.QCheckBox("Use duplex when supported")
        options_layout.addWidget(self.duplex_checkbox)

        options_layout.addWidget(qtw.QLabel("Review"))
        self.review_label = qtw.QLabel("")
        self.review_label.setWordWrap(True)
        options_layout.addWidget(self.review_label)

        self.status_label = qtw.QLabel("")
        self.status_label.setWordWrap(True)
        options_layout.addWidget(self.status_label)
        options_layout.addStretch(1)
        self.page_stack.addWidget(options_page)

        button_row = qtw.QHBoxLayout()
        self.back_button = qtw.QPushButton("Back")
        self.back_button.clicked.connect(self._go_back)
        button_row.addWidget(self.back_button)

        self.next_button = qtw.QPushButton("Next")
        self.next_button.clicked.connect(self._go_next)
        button_row.addWidget(self.next_button)

        button_row.addStretch(1)
        self.cancel_button = qtw.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_button)

        self.scan_button = qtw.QPushButton("Start Scan")
        self.scan_button.clicked.connect(self._attempt_accept)
        button_row.addWidget(self.scan_button)
        layout.addLayout(button_row)

        self.backend_combo.currentTextChanged.connect(self._update_validation_state)
        self.backend_combo.currentIndexChanged.connect(self._refresh_detected_devices)
        self.backend_combo.currentIndexChanged.connect(self._sync_backend_specific_controls)
        self.device_name_edit.textChanged.connect(self._update_validation_state)
        self.destination_edit.textChanged.connect(self._update_validation_state)
        self.mode_combo.currentTextChanged.connect(self._update_validation_state)
        self.dpi_combo.currentTextChanged.connect(self._update_validation_state)
        self.source_type_combo.currentTextChanged.connect(self._update_validation_state)
        self.persist_format_combo.currentTextChanged.connect(self._update_validation_state)
        self.duplex_checkbox.toggled.connect(self._update_validation_state)
        self.allow_network_fallback_checkbox.toggled.connect(self._refresh_detected_devices)
        self.allow_network_fallback_checkbox.toggled.connect(self._update_validation_state)

    def _populate_backend_options(self):
        self.backend_combo.clear()
        for option in self._backend_options_cache:
            label = option["label"]
            if not option.get("available", False):
                reason = option.get("unavailable_reason")
                if reason and option["label"] == "TWAIN":
                    label = f"{label} (unavailable on this system)"
                else:
                    label = f"{label} (unavailable)"
            self.backend_combo.addItem(label, option["value"])

    def _refresh_detected_devices(self):
        if self._loading_backends:
            return
        request = {
            "backend_preference": self.backend_combo.currentData() or self.initial_request.get("backend_preference"),
            "allow_network_fallback": self.allow_network_fallback_checkbox.isChecked(),
        }
        self._start_device_load(request)

    def _apply_initial_request(self):
        backend_index = self.backend_combo.findData(self.initial_request.get("backend_preference", "auto"))
        if backend_index >= 0:
            self.backend_combo.setCurrentIndex(backend_index)

        self.device_name_edit.setText(self.initial_request.get("device_name", ""))
        self.destination_edit.setText(self.initial_request.get("destination_folder", self.default_destination))

        mode = self.initial_request.get("mode", "color")
        if self.mode_combo.findText(mode) >= 0:
            self.mode_combo.setCurrentText(mode)

        dpi = str(self.initial_request.get("dpi", 300))
        if self.dpi_combo.findText(dpi) >= 0:
            self.dpi_combo.setCurrentText(dpi)

        source_type = self.initial_request.get("source_type", "flatbed")
        if self.source_type_combo.findText(source_type) >= 0:
            self.source_type_combo.setCurrentText(source_type)

        persist_format = self.initial_request.get("persist_format", "tiff")
        if self.persist_format_combo.findText(persist_format) >= 0:
            self.persist_format_combo.setCurrentText(persist_format)

        self.duplex_checkbox.setChecked(bool(self.initial_request.get("duplex", False)))
        self.allow_network_fallback_checkbox.setChecked(bool(self.initial_request.get("allow_network_fallback", True)))

    def _sync_backend_specific_controls(self):
        is_sane_backend = self.backend_combo.currentData() == "SaneScanner"
        self.allow_network_fallback_checkbox.setEnabled(is_sane_backend)
        if is_sane_backend:
            self.allow_network_fallback_checkbox.setText("Allow AirScan fallback while testing SANE")
        else:
            self.allow_network_fallback_checkbox.setText("AirScan fallback applies only to the SANE backend")

    def _go_back(self):
        index = self.page_stack.currentIndex()
        if index > 0:
            self.page_stack.setCurrentIndex(index - 1)
            self._update_page_state()

    def _go_next(self):
        index = self.page_stack.currentIndex()
        if index < self.page_stack.count() - 1:
            self.page_stack.setCurrentIndex(index + 1)
            self._update_page_state()

    def _update_page_state(self):
        index = self.page_stack.currentIndex()
        self.page_title_label.setText(self._page_titles[index])
        self.back_button.setEnabled(index > 0)
        self.next_button.setVisible(index < self.page_stack.count() - 1)
        self.scan_button.setVisible(index == self.page_stack.count() - 1)
        self._update_validation_state()

    def _update_validation_state(self):
        request = self.get_request()
        if not request["destination_folder"].strip():
            self.status_label.setText("Destination folder is required before the scan can start.")
            self.status_label.setStyleSheet("color: #9f3a38;")
            self.scan_button.setEnabled(False)
        elif self._loading_backends or self._loading_devices:
            self.status_label.setText("Loading scanner backends and devices. Please wait.")
            self.status_label.setStyleSheet("color: #8a6d1d;")
            self.scan_button.setEnabled(False)
        else:
            backend_option = self._backend_options_by_value.get(request["backend_preference"])
            if backend_option is None:
                self.status_label.setText("Select a valid scan backend before starting.")
                self.status_label.setStyleSheet("color: #9f3a38;")
                self.scan_button.setEnabled(False)
            elif not backend_option.get("available", False):
                unavailable_reason = backend_option.get("unavailable_reason")
                if unavailable_reason:
                    self.status_label.setText(unavailable_reason)
                else:
                    self.status_label.setText(
                        f"{backend_option['label']} is not available on this system. Choose another backend to test."
                    )
                self.status_label.setStyleSheet("color: #9f3a38;")
                self.scan_button.setEnabled(False)
            else:
                self.status_label.setText("Review the scan request and start when ready.")
                self.status_label.setStyleSheet("color: #2f6b3b;")
                self.scan_button.setEnabled(True)

        review_lines = [
            f"Backend: {self.backend_combo.currentText()}",
            f"Device: {request['device_name'] or 'Default device'}",
            f"Allow AirScan fallback: {'Yes' if request['allow_network_fallback'] else 'No'}",
            f"Destination: {request['destination_folder']}",
            f"Mode: {request['mode']}",
            f"DPI: {request['dpi']}",
            f"Source type: {request['source_type']}",
            f"Duplex: {'Yes' if request['duplex'] else 'No'}",
            f"Persist format: {request['persist_format']}",
        ]
        self.review_label.setText("\n".join(review_lines))

    def _attempt_accept(self):
        if not self.destination_edit.text().strip():
            self._update_validation_state()
            return
        self.accept()

    def get_request(self):
        return {
            "destination_folder": self.destination_edit.text().strip(),
            "backend_preference": self.backend_combo.currentData(),
            "device_name": self.device_name_edit.text().strip(),
            "allow_network_fallback": self.allow_network_fallback_checkbox.isChecked(),
            "mode": self.mode_combo.currentText(),
            "dpi": int(self.dpi_combo.currentText()),
            "source_type": self.source_type_combo.currentText(),
            "duplex": self.duplex_checkbox.isChecked(),
            "persist_format": self.persist_format_combo.currentText(),
        }

    def _format_detected_devices(self, devices, request):
        if not devices:
            if request["backend_preference"] == "ESCLScanner":
                return "No AirScan devices were discovered automatically. Enter a scanner IP or URL above to connect directly."
            if request["backend_preference"] == "SaneScanner" and not request.get("allow_network_fallback", True):
                return "No native SANE devices were reported by scanimage -L. AirScan fallback is currently disabled for this test."
            return "No devices reported by the current backend selection."
        if request["backend_preference"] == "SaneScanner":
            legend_lines = [
                "[native SANE] = reported directly by scanimage -L via local SANE backend",
                "[AirScan fallback] = network fallback path, not native USB SANE",
            ]
            return "\n".join(legend_lines + [""] + [str(device) for device in devices])
        return "\n".join(str(device) for device in devices)

    def _set_loading_state(self, message, active):
        self.loading_label.setText(message)
        self.loading_label.setVisible(active)
        self.loading_progress.setVisible(active)
        self._update_validation_state()

    def _start_backend_load(self):
        if self._backend_loader_thread is not None:
            return
        self._loading_backends = True
        self._set_loading_state("Loading scanner backends...", True)
        self.detected_devices_label.setText("Scanner discovery will start after the backend list loads.")

        self._backend_loader_thread = qtc.QThread(self)
        self._backend_loader_worker = ScanWizardLoadWorker(
            self.scan_manager,
            load_backend_options=True,
        )
        self._backend_loader_worker.moveToThread(self._backend_loader_thread)
        self._backend_loader_thread.started.connect(self._backend_loader_worker.run)
        self._backend_loader_worker.finished.connect(self._on_backend_load_finished)
        self._backend_loader_worker.error.connect(self._on_backend_load_error)
        self._backend_loader_worker.finished.connect(self._backend_loader_thread.quit)
        self._backend_loader_worker.error.connect(self._backend_loader_thread.quit)
        self._backend_loader_thread.finished.connect(self._cleanup_backend_loader)
        self._backend_loader_thread.start()

    def _on_backend_load_finished(self, payload):
        self._loading_backends = False
        self._backend_options_cache = payload.get("backend_options", [])
        self._backend_options_by_value = {
            option["value"]: option for option in self._backend_options_cache
        }
        self.backend_combo.blockSignals(True)
        self._populate_backend_options()
        self.backend_combo.setEnabled(bool(self._backend_options_cache))

        backend_value = self.initial_request.get("backend_preference", "auto")
        backend_index = self.backend_combo.findData(backend_value)
        if backend_index < 0 and self.backend_combo.count() > 0:
            backend_index = 0
        if backend_index >= 0:
            self.backend_combo.setCurrentIndex(backend_index)
        self.backend_combo.blockSignals(False)
        self._sync_backend_specific_controls()

        self._set_loading_state("", False)
        self._refresh_detected_devices()
        self._update_validation_state()

    def _on_backend_load_error(self, message):
        self._loading_backends = False
        self.backend_combo.clear()
        self.backend_combo.addItem("Scanner backends unavailable", None)
        self.backend_combo.setEnabled(False)
        self.detected_devices_label.setText(f"Device discovery unavailable: {message}")
        self._set_loading_state("Failed to load scanner backends.", False)
        self._update_validation_state()

    def _cleanup_backend_loader(self):
        finished_thread = self.sender()
        if self._backend_loader_worker is not None:
            self._backend_loader_worker.deleteLater()
            self._backend_loader_worker = None
        if finished_thread is not None:
            finished_thread.deleteLater()
        if self._backend_loader_thread is finished_thread:
            self._backend_loader_thread = None

    def _start_device_load(self, request):
        if self._device_loader_thread is not None and self._device_loader_thread.isRunning():
            return

        self._device_request_token += 1
        request_payload = dict(request)
        request_payload["_token"] = self._device_request_token
        self._loading_devices = True
        self.detected_devices_label.setText("Detecting devices for the selected backend...")
        self._set_loading_state("Detecting scanner devices...", True)

        self._device_loader_thread = qtc.QThread(self)
        self._device_loader_worker = ScanWizardLoadWorker(
            self.scan_manager,
            request=request_payload,
            discover_devices=True,
        )
        self._device_loader_worker.moveToThread(self._device_loader_thread)
        self._device_loader_thread.started.connect(self._device_loader_worker.run)
        self._device_loader_worker.finished.connect(self._on_device_load_finished)
        self._device_loader_worker.error.connect(self._on_device_load_error)
        self._device_loader_worker.finished.connect(self._device_loader_thread.quit)
        self._device_loader_worker.error.connect(self._device_loader_thread.quit)
        self._device_loader_thread.finished.connect(self._cleanup_device_loader)
        self._device_loader_thread.start()

    def _on_device_load_finished(self, payload):
        request = payload.get("request", {})
        if request.get("_token") != self._device_request_token:
            return
        self._loading_devices = False
        visible_request = dict(request)
        visible_request.pop("_token", None)
        devices = payload.get("devices", [])
        self.detected_devices_label.setText(self._format_detected_devices(devices, visible_request))
        self._set_loading_state("", False)
        self._update_validation_state()

    def _on_device_load_error(self, message):
        self._loading_devices = False
        self.detected_devices_label.setText(f"Device discovery unavailable: {message}")
        self._set_loading_state("", False)
        self._update_validation_state()

    def _cleanup_device_loader(self):
        finished_thread = self.sender()
        if self._device_loader_worker is not None:
            self._device_loader_worker.deleteLater()
            self._device_loader_worker = None
        if finished_thread is not None:
            finished_thread.deleteLater()
        if self._device_loader_thread is finished_thread:
            self._device_loader_thread = None

    def closeEvent(self, event):
        for thread in (self._backend_loader_thread, self._device_loader_thread):
            if thread is not None and thread.isRunning():
                thread.quit()
                thread.wait(1000)
        super().closeEvent(event)