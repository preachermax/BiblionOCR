from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


class ImagePreviewDialog(qtw.QDialog):
    """Interactive QImage preview dialog for crop/processing tests.

    The dialog shows the original image on the left and the processed result on
    the right. It always re-renders from the original QImage so zooming never
    compounds scaling artifacts and crop coordinates are stored in original
    image coordinates.
    """

    def __init__(self, qimage=None, processor=None, params=None, parent=None,
                 initial_params=None, **kwargs):
        """Create a preview dialog.

        Supported call forms are intentionally broad while MyServer/MyPixler are
        being stabilized:

        * ImagePreviewDialog(qimage, processor, parent)
        * ImagePreviewDialog(qimage, processor, params, parent)
        * ImagePreviewDialog(parent, qimage, processor)
        * ImagePreviewDialog(original_qimage=qimage, processor=processor,
          parent=parent, params=params)
        """
        qimage, processor, params, parent = self._normalize_constructor_args(
            qimage, processor, params, parent, kwargs
        )

        super().__init__(parent)

        if initial_params is None:
            initial_params = kwargs.get("initial_params")
        if initial_params is None:
            initial_params = kwargs.get("params")
        if initial_params is None:
            initial_params = params

        self.original = qimage
        self.processor = processor or self._identity_processor
        self.params = dict(initial_params or {})
        self.zoom_factor = 1.0
        self.origin = qtc.QPoint()
        self.crop_drawing_active = False
        self.crop_rect = qtc.QRect()
        self._crop_handles = {}
        self._active_handle = None
        self._handle_start_global = qtc.QPoint()
        self._handle_start_rect = qtc.QRect()
        self._last_processed_result = qtg.QImage()
        self._last_preview_result = qtg.QImage()

        self.setWindowTitle("Preview")
        self.resize(1200, 700)

        self._build_ui()
        self.update_preview()

    @staticmethod
    def _normalize_constructor_args(qimage, processor, params, parent, kwargs):
        if qimage is None:
            qimage = kwargs.get("original_qimage")
        if processor is None:
            processor = kwargs.get("processor")
        if parent is None:
            parent = kwargs.get("parent")

        # Legacy positional form: (parent, qimage, processor).
        if isinstance(qimage, qtw.QWidget) and hasattr(processor, "isNull") and callable(params):
            old_parent = qimage
            qimage = processor
            processor = params
            params = None
            parent = old_parent

        # Common transitional form: (qimage, processor, parent).
        if isinstance(params, qtw.QWidget) and parent is None:
            parent = params
            params = None

        return qimage, processor, params, parent

    def _build_ui(self):
        layout = qtw.QVBoxLayout(self)

        image_layout = qtw.QHBoxLayout()
        self.left_label = qtw.QLabel()
        self.right_label = qtw.QLabel()
        self.left_label.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.right_label.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.left_label.setMouseTracking(True)

        self.left_scroll = qtw.QScrollArea()
        self.right_scroll = qtw.QScrollArea()
        self.left_scroll.setWidget(self.left_label)
        self.right_scroll.setWidget(self.right_label)
        self.left_scroll.setWidgetResizable(False)
        self.right_scroll.setWidgetResizable(False)
        image_layout.addWidget(self.left_scroll)
        image_layout.addWidget(self.right_scroll)
        layout.addLayout(image_layout, stretch=1)

        zoom_layout = qtw.QHBoxLayout()
        self.zoom_label = qtw.QLabel("Zoom: 100%")
        self.zoom_slider = qtw.QSlider(qtc.Qt.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setSingleStep(1)
        self.zoom_slider.setPageStep(10)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        layout.addLayout(zoom_layout)

        self.controls_layout = qtw.QHBoxLayout()
        layout.addLayout(self.controls_layout)

        button_layout = qtw.QHBoxLayout()
        self.apply_btn = qtw.QPushButton("Apply")
        self.cancel_btn = qtw.QPushButton("Cancel")
        self.apply_btn.clicked.connect(self._hide_crop_overlay)
        self.apply_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self._hide_crop_overlay)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch(1)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.rubberBand = qtw.QRubberBand(qtw.QRubberBand.Rectangle, self.left_label)
        self._build_crop_handles()
        self.left_label.installEventFilter(self)

    def _build_crop_handles(self):
        cursor_map = {
            "nw": qtc.Qt.SizeFDiagCursor,
            "n": qtc.Qt.SizeVerCursor,
            "ne": qtc.Qt.SizeBDiagCursor,
            "e": qtc.Qt.SizeHorCursor,
            "se": qtc.Qt.SizeFDiagCursor,
            "s": qtc.Qt.SizeVerCursor,
            "sw": qtc.Qt.SizeBDiagCursor,
            "w": qtc.Qt.SizeHorCursor,
        }

        for name, cursor in cursor_map.items():
            handle = qtw.QFrame(self.left_label)
            handle.setObjectName("previewCropGrip_{}".format(name))
            handle.setFixedSize(8, 8)
            handle.setCursor(cursor)
            handle.setStyleSheet(
                "QFrame { background-color: #87cefa; border: 1px solid #1e90ff; }"
                "QFrame:hover { background-color: #bfefff; border: 1px solid #0066cc; }"
            )
            handle.setToolTip("Drag to resize crop ({})".format(name))
            handle.installEventFilter(self)
            handle.hide()
            self._crop_handles[name] = handle

    def _set_handles_visible(self, visible):
        for handle in self._crop_handles.values():
            handle.setVisible(visible)

    def _raise_crop_overlay(self):
        self.rubberBand.raise_()
        for handle in self._crop_handles.values():
            handle.raise_()

    def _position_crop_handles(self):
        if not self._crop_handles or self.crop_rect.isNull():
            return

        rect = self.crop_rect.normalized()
        size = 8
        half = size // 2
        cx = rect.left() + rect.width() // 2
        cy = rect.top() + rect.height() // 2

        positions = {
            "nw": (rect.left() - half, rect.top() - half),
            "n": (cx - half, rect.top() - half),
            "ne": (rect.right() - half, rect.top() - half),
            "e": (rect.right() - half, cy - half),
            "se": (rect.right() - half, rect.bottom() - half),
            "s": (cx - half, rect.bottom() - half),
            "sw": (rect.left() - half, rect.bottom() - half),
            "w": (rect.left() - half, cy - half),
        }

        bounds = self.left_label.rect()
        for name, (x, y) in positions.items():
            x = max(bounds.left(), min(x, bounds.right() - size + 1))
            y = max(bounds.top(), min(y, bounds.bottom() - size + 1))
            self._crop_handles[name].move(x, y)

    def _show_crop_overlay(self, rect):
        self.crop_rect = rect.normalized()
        self.rubberBand.setGeometry(self.crop_rect)
        self.rubberBand.show()
        self._position_crop_handles()
        self._set_handles_visible(True)
        self._raise_crop_overlay()
        print("[PREVIEW CROP] RubberBand shown with {} grip handles".format(len(self._crop_handles)))

    def _hide_crop_overlay(self):
        self.rubberBand.hide()
        self._set_handles_visible(False)

    def _clamp_display_rect(self, rect):
        rect = rect.normalized()
        pixmap = self.left_label.pixmap()
        max_w = pixmap.width() if pixmap is not None and not pixmap.isNull() else self.left_label.width()
        max_h = pixmap.height() if pixmap is not None and not pixmap.isNull() else self.left_label.height()

        if rect.left() < 0:
            rect.setLeft(0)
        if rect.top() < 0:
            rect.setTop(0)
        if rect.right() >= max_w:
            rect.setRight(max_w - 1)
        if rect.bottom() >= max_h:
            rect.setBottom(max_h - 1)

        min_size = 8
        if rect.width() < min_size:
            if self._active_handle and "w" in self._active_handle:
                rect.setLeft(rect.right() - min_size + 1)
            else:
                rect.setRight(rect.left() + min_size - 1)
        if rect.height() < min_size:
            if self._active_handle and "n" in self._active_handle:
                rect.setTop(rect.bottom() - min_size + 1)
            else:
                rect.setBottom(rect.top() + min_size - 1)

        return rect.normalized()

    def _preview_crop_rect(self, rect):
        rect = self._clamp_display_rect(rect)
        self._show_crop_overlay(rect)
        if self._set_crop_from_display_rect(rect):
            self.update_preview()
            self._show_crop_overlay(rect)

    def add_slider(self, name, min_val, max_val, default):
        label = qtw.QLabel("{}: {}".format(name, default))
        slider = qtw.QSlider(qtc.Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)

        def on_change(value):
            self.params[name] = value
            label.setText("{}: {}".format(name, value))
            self.update_preview()

        slider.valueChanged.connect(on_change)
        self.controls_layout.addWidget(label)
        self.controls_layout.addWidget(slider)
        self.params[name] = default

    def eventFilter(self, obj, event):
        handle_name = None
        for name, handle in self._crop_handles.items():
            if obj is handle:
                handle_name = name
                break

        if handle_name is not None:
            if event.type() == qtc.QEvent.MouseButtonPress and event.button() == qtc.Qt.LeftButton:
                self._active_handle = handle_name
                self._handle_start_global = event.globalPos()
                self._handle_start_rect = qtc.QRect(self.crop_rect)
                print("[PREVIEW CROP] Grip press: {}".format(handle_name))
                event.accept()
                return True

            if event.type() == qtc.QEvent.MouseMove and self._active_handle:
                delta = event.globalPos() - self._handle_start_global
                rect = qtc.QRect(self._handle_start_rect)
                if "n" in self._active_handle:
                    rect.setTop(rect.top() + delta.y())
                if "s" in self._active_handle:
                    rect.setBottom(rect.bottom() + delta.y())
                if "w" in self._active_handle:
                    rect.setLeft(rect.left() + delta.x())
                if "e" in self._active_handle:
                    rect.setRight(rect.right() + delta.x())
                self._show_crop_overlay(self._clamp_display_rect(rect))
                event.accept()
                return True

            if event.type() == qtc.QEvent.MouseButtonRelease and self._active_handle:
                print("[PREVIEW CROP] Grip release: {}".format(self._active_handle))
                self._active_handle = None
                self._preview_crop_rect(self.crop_rect)
                event.accept()
                return True

            return super().eventFilter(obj, event)

        if obj == self.left_label:
            if event.type() == qtc.QEvent.MouseButtonPress and event.button() == qtc.Qt.LeftButton:
                self.crop_drawing_active = True
                self.origin = event.pos()
                self._show_crop_overlay(qtc.QRect(self.origin, qtc.QSize()))
                return True

            if event.type() == qtc.QEvent.MouseMove and self.crop_drawing_active:
                rect = qtc.QRect(self.origin, event.pos()).normalized()
                self._show_crop_overlay(rect)
                return True

            if event.type() == qtc.QEvent.MouseButtonRelease and self.crop_drawing_active:
                self.crop_drawing_active = False
                rect = qtc.QRect(self.origin, event.pos()).normalized()
                self._preview_crop_rect(rect)
                return True

        return super().eventFilter(obj, event)

    def on_zoom_changed(self, value):
        self.zoom_factor = max(0.01, value / 100.0)
        self.zoom_label.setText("Zoom: {}%".format(value))
        self.update_preview()

    def update_preview(self):
        if self.original is None or self.original.isNull():
            print("[PREVIEW] No valid original image")
            return

        processed = self._process()
        if processed is None or processed.isNull():
            print("[PREVIEW] Processor returned no valid image")
            return

        original_pixmap = qtg.QPixmap.fromImage(self.original)
        processed_pixmap = qtg.QPixmap.fromImage(processed)
        if original_pixmap.isNull() or processed_pixmap.isNull():
            print("[PREVIEW] Null pixmap after image conversion")
            return

        original_scaled = self._scaled_pixmap(original_pixmap)
        processed_scaled = self._scaled_pixmap(processed_pixmap)

        self._last_processed_result = qtg.QImage(processed)
        self._last_preview_result = processed_scaled.toImage()
        self._copy_image_resolution(processed, self._last_preview_result)

        self.left_label.setPixmap(original_scaled)
        self.left_label.resize(original_scaled.size())
        self.right_label.setPixmap(processed_scaled)
        self.right_label.resize(processed_scaled.size())

        if self.rubberBand.isVisible() and not self.crop_rect.isNull():
            self._show_crop_overlay(self.crop_rect)

    def get_result(self):
        return self._process()

    def get_preview_result(self):
        """Return the exact QImage currently represented by the right preview.

        This preserves the user-visible preview dimensions/appearance when the
        result is applied back to MyPixler instead of returning the unscaled
        processor output and letting MyPixler rescale it differently.
        """
        if not self._last_preview_result.isNull():
            return qtg.QImage(self._last_preview_result)

        pixmap = self.right_label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            result = pixmap.toImage()
            if not self._last_processed_result.isNull():
                self._copy_image_resolution(self._last_processed_result, result)
            return result

        return self.get_result()

    @staticmethod
    def _copy_image_resolution(source, target):
        if source is None or target is None or source.isNull() or target.isNull():
            return

        target.setDotsPerMeterX(source.dotsPerMeterX())
        target.setDotsPerMeterY(source.dotsPerMeterY())
        target.setDevicePixelRatio(source.devicePixelRatio())

        if hasattr(source, "colorSpace") and hasattr(target, "setColorSpace"):
            try:
                color_space = source.colorSpace()
                if color_space.isValid():
                    target.setColorSpace(color_space)
            except Exception:
                pass

    @staticmethod
    def _identity_processor(qimage, params):
        return qimage

    def _process(self):
        try:
            result = self.processor(self.original, self.params)
        except Exception as exc:
            print("[PREVIEW ERROR] {}".format(exc))
            return None

        if isinstance(result, qtg.QPixmap):
            result = result.toImage()

        self._copy_image_resolution(self.original, result)
        return result

    def _scaled_pixmap(self, pixmap):
        if pixmap.isNull():
            return pixmap

        width = max(1, int(round(pixmap.width() * self.zoom_factor)))
        height = max(1, int(round(pixmap.height() * self.zoom_factor)))
        return pixmap.scaled(
            qtc.QSize(width, height),
            qtc.Qt.KeepAspectRatio,
            qtc.Qt.SmoothTransformation,
        )

    def _set_crop_from_display_rect(self, rect):
        pixmap = self.left_label.pixmap()
        if pixmap is None or pixmap.isNull():
            print("[CROP] No display pixmap")
            return False

        display_x = max(0, rect.x())
        display_y = max(0, rect.y())
        display_w = min(rect.width(), pixmap.width() - display_x)
        display_h = min(rect.height(), pixmap.height() - display_y)

        if display_w < 5 or display_h < 5:
            print("[CROP] Selection too small")
            return False

        scale = max(0.01, self.zoom_factor)
        x = int(round(display_x / scale))
        y = int(round(display_y / scale))
        w = int(round(display_w / scale))
        h = int(round(display_h / scale))

        image_w = self.original.width()
        image_h = self.original.height()
        x = max(0, min(x, image_w - 1))
        y = max(0, min(y, image_h - 1))
        w = max(1, min(w, image_w - x))
        h = max(1, min(h, image_h - y))

        self.params.update({"x": x, "y": y, "w": w, "h": h})
        print("[CROP] x={}, y={}, w={}, h={}".format(x, y, w, h))
        return True
