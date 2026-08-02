from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from MorphologyDialogUI import Ui_MorphologyDialog


class MorphologyDialog(qtw.QDialog):
    BILEVEL_DISPLAY_THRESHOLD = 216

    def __init__(self, qimage, processor, params=None, parent=None, preview_max_dimension=1600):
        super().__init__(parent)

        self.ui = Ui_MorphologyDialog()
        self.ui.setupUi(self)

        self.original = qtg.QImage(qimage)
        self.processor = processor
        self.preview_max_dimension = int(preview_max_dimension or 0)
        self.params = {
            "threshold": 0,
            "operator": "threshold",
            "shape": "rect",
            "kernel_x": 3,
            "kernel_y": 3,
            "iterations": 1,
        }
        if params:
            self.params.update(params)

        self.zoom_factor = 1.0
        self._last_processed_result = qtg.QImage()
        self._last_reference_result = qtg.QImage()
        self._preview_update_timer = qtc.QTimer(self)
        self._preview_update_timer.setSingleShot(True)
        self._preview_update_timer.timeout.connect(self._run_scheduled_preview_update)
        self._pending_full_quality_preview = False
        self.preview_source = self._build_preview_source()

        self.left_label = self.ui.leftPreviewLabel
        self.right_label = self.ui.rightPreviewLabel
        self.left_scroll = self.ui.leftScrollArea
        self.right_scroll = self.ui.rightScrollArea
        self.zoom_label = self.ui.zoomLabel
        self.zoom_slider = self.ui.zoomSlider
        self.threshold_value_label = self.ui.thresholdValueLabel
        self.threshold_slider = self.ui.thresholdSlider
        self.operator_combo = self.ui.operatorComboBox
        self.shape_combo = self.ui.shapeComboBox
        self.kernel_x_spin = self.ui.kernelXSpinBox
        self.kernel_y_spin = self.ui.kernelYSpinBox
        self.iterations_spin = self.ui.iterationsSpinBox
        self.summary_label = self.ui.summaryLabel
        self.reset_button = self.ui.resetButton
        self.apply_button = self.ui.applyButton
        self.cancel_button = self.ui.cancelButton

        self.left_label.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.right_label.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)

        self._initialize_controls()
        self.update_preview(force_full_quality=True)

    def _initialize_controls(self):
        self.operator_combo.addItem("Threshold Only", "threshold")
        self.operator_combo.addItem("Erode", "erode")
        self.operator_combo.addItem("Dilate", "dilate")
        self.operator_combo.addItem("Open", "open")
        self.operator_combo.addItem("Close", "close")
        self._set_combo_value(self.operator_combo, self.params["operator"])

        self.shape_combo.addItem("Rectangle", "rect")
        self.shape_combo.addItem("Ellipse", "ellipse")
        self.shape_combo.addItem("Cross", "cross")
        self._set_combo_value(self.shape_combo, self.params["shape"])

        self.threshold_slider.setValue(int(self.params["threshold"]))
        self.kernel_x_spin.setValue(self._normalize_odd(self.params["kernel_x"]))
        self.kernel_y_spin.setValue(self._normalize_odd(self.params["kernel_y"]))
        self.iterations_spin.setValue(int(self.params["iterations"]))

        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        self.zoom_slider.sliderReleased.connect(lambda: self._flush_preview_update(full_quality=True))
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self.threshold_slider.sliderReleased.connect(lambda: self._flush_preview_update(full_quality=True))
        self.operator_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.shape_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.kernel_x_spin.valueChanged.connect(self._on_kernel_changed)
        self.kernel_y_spin.valueChanged.connect(self._on_kernel_changed)
        self.iterations_spin.valueChanged.connect(self._on_iterations_changed)
        self.reset_button.clicked.connect(self._reset_defaults)
        self.apply_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self._refresh_threshold_label()
        self._refresh_summary_label()

    @staticmethod
    def _set_combo_value(combo, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    @staticmethod
    def _create_odd_spinbox(value):
        spin = qtw.QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(99)
        spin.setSingleStep(2)
        spin.setValue(MorphologyDialog._normalize_odd(value))
        return spin

    @staticmethod
    def _normalize_odd(value):
        value = max(1, int(value))
        return value if value % 2 == 1 else value + 1

    def _on_zoom_changed(self, value):
        self.zoom_factor = max(0.1, value / 100.0)
        self.zoom_label.setText("Zoom: {}%".format(value))
        self._schedule_preview_update()

    def _on_threshold_changed(self, value):
        self.params["threshold"] = int(value)
        self._refresh_threshold_label()
        self._schedule_preview_update()

    def _on_combo_changed(self):
        self.params["operator"] = self.operator_combo.currentData()
        self.params["shape"] = self.shape_combo.currentData()
        self._refresh_summary_label()
        self._flush_preview_update(full_quality=True)

    def _on_kernel_changed(self):
        self.params["kernel_x"] = self._normalize_odd(self.kernel_x_spin.value())
        self.params["kernel_y"] = self._normalize_odd(self.kernel_y_spin.value())
        self.kernel_x_spin.blockSignals(True)
        self.kernel_y_spin.blockSignals(True)
        self.kernel_x_spin.setValue(self.params["kernel_x"])
        self.kernel_y_spin.setValue(self.params["kernel_y"])
        self.kernel_x_spin.blockSignals(False)
        self.kernel_y_spin.blockSignals(False)
        self._refresh_summary_label()
        self._schedule_preview_update()

    def _on_iterations_changed(self, value):
        self.params["iterations"] = int(value)
        self._refresh_summary_label()
        self._schedule_preview_update()

    def _refresh_threshold_label(self):
        if int(self.params.get("threshold", 0)) <= 0:
            self.threshold_value_label.setText("Auto threshold (Otsu)")
        else:
            self.threshold_value_label.setText("Manual threshold: {}".format(self.params["threshold"]))

    def _refresh_summary_label(self):
        op_text = self.operator_combo.currentText()
        shape_text = self.shape_combo.currentText()
        self.summary_label.setText(
            "{} with {} kernel {}x{} for {} iteration(s)".format(
                op_text,
                shape_text.lower(),
                self.params["kernel_x"],
                self.params["kernel_y"],
                self.params["iterations"],
            )
        )

    def _reset_defaults(self):
        self.threshold_slider.setValue(0)
        self._set_combo_value(self.operator_combo, "threshold")
        self._set_combo_value(self.shape_combo, "rect")
        self.kernel_x_spin.setValue(3)
        self.kernel_y_spin.setValue(3)
        self.iterations_spin.setValue(1)
        self._on_combo_changed()
        self._flush_preview_update(full_quality=True)

    def _schedule_preview_update(self, delay_ms=20, full_quality=False):
        self._pending_full_quality_preview = self._pending_full_quality_preview or full_quality
        self._preview_update_timer.start(delay_ms)

    def _run_scheduled_preview_update(self):
        full_quality = self._pending_full_quality_preview
        self._pending_full_quality_preview = False
        self.update_preview(force_full_quality=full_quality)

    def _flush_preview_update(self, full_quality=False):
        if self._preview_update_timer.isActive():
            self._preview_update_timer.stop()
        full_quality = full_quality or self._pending_full_quality_preview
        self._pending_full_quality_preview = False
        self.update_preview(force_full_quality=full_quality)

    def _build_preview_source(self):
        if self.original.isNull() or self.preview_max_dimension <= 0:
            return qtg.QImage(self.original)

        width = self.original.width()
        height = self.original.height()
        longest_edge = max(width, height)
        if longest_edge <= self.preview_max_dimension:
            return qtg.QImage(self.original)

        scale = self.preview_max_dimension / float(longest_edge)
        return self.original.scaled(
            max(1, int(width * scale)),
            max(1, int(height * scale)),
            qtc.Qt.KeepAspectRatio,
            qtc.Qt.FastTransformation,
        )

    def _scaled_display_pixmap(self, qimage):
        if qimage is None or qimage.isNull():
            return qtg.QPixmap()

        display_image = qtg.QImage(qimage)
        if self._is_bilevel_image(display_image):
            display_image = self._scale_bilevel_for_display(display_image)
        else:
            scaled_size = qtc.QSize(
                max(1, int(display_image.width() * self.zoom_factor)),
                max(1, int(display_image.height() * self.zoom_factor)),
            )
            display_image = display_image.scaled(
                scaled_size,
                qtc.Qt.KeepAspectRatio,
                qtc.Qt.SmoothTransformation,
            )

        return qtg.QPixmap.fromImage(display_image)

    def _scale_bilevel_for_display(self, qimage):
        grayscale = qimage.convertToFormat(qtg.QImage.Format_Grayscale8)
        scaled_size = qtc.QSize(
            max(1, int(grayscale.width() * self.zoom_factor)),
            max(1, int(grayscale.height() * self.zoom_factor)),
        )
        scaled = grayscale.scaled(
            scaled_size,
            qtc.Qt.KeepAspectRatio,
            qtc.Qt.FastTransformation,
        )
        return self._threshold_grayscale_display_image(scaled)

    def _threshold_grayscale_display_image(self, qimage):
        width = qimage.width()
        height = qimage.height()
        bits = qimage.bits()
        bits.setsize(width * height)
        array = memoryview(bits).tobytes()

        thresholded = bytearray(width * height)
        threshold = self.BILEVEL_DISPLAY_THRESHOLD
        for index, value in enumerate(array):
            thresholded[index] = 255 if value >= threshold else 0

        display = qtg.QImage(bytes(thresholded), width, height, width, qtg.QImage.Format_Grayscale8)
        return display.copy()

    @staticmethod
    def _is_bilevel_image(qimage):
        if qimage is None or qimage.isNull():
            return False
        return qimage.depth() == 1 or qimage.format() in (qtg.QImage.Format_Mono, qtg.QImage.Format_MonoLSB)

    def update_preview(self, force_full_quality=False):
        if self.original.isNull():
            return

        reference_source = qtg.QImage(self.original if force_full_quality else self.preview_source)
        processor_input = qtg.QImage(reference_source)

        processed = self.processor(processor_input, dict(self.params))
        if processed is None or processed.isNull():
            return

        self._last_reference_result = qtg.QImage(reference_source)
        self._last_processed_result = qtg.QImage(processed)

        original_scaled = self._scaled_display_pixmap(reference_source)
        processed_scaled = self._scaled_display_pixmap(processed)
        if original_scaled.isNull() or processed_scaled.isNull():
            return

        self.left_label.setPixmap(original_scaled)
        self.left_label.resize(original_scaled.size())
        self.right_label.setPixmap(processed_scaled)
        self.right_label.resize(processed_scaled.size())

    def get_result(self):
        return self.processor(self.original, dict(self.params))