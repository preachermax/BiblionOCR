class ImagePreviewDialog(qtw.QDialog):
    def __init__(self, parent, qimage, processor, initial_params=None):
        super().__init__(parent)

        self.setWindowTitle("Preview")
        self.resize(1200, 600)

        self.original = qimage
        self.processor = processor
        self.params = initial_params or {}

        # -------------------------
        # Layout
        # -------------------------
        layout = qtw.QVBoxLayout(self)

        # Image views
        views = qtw.QHBoxLayout()

        self.left_label = qtw.QLabel()
        self.right_label = qtw.QLabel()

        self.left_label.setAlignment(qtc.Qt.AlignCenter)
        self.right_label.setAlignment(qtc.Qt.AlignCenter)

        views.addWidget(self.left_label)
        views.addWidget(self.right_label)

        layout.addLayout(views)

        # Controls
        self.controls_layout = qtw.QHBoxLayout()
        layout.addLayout(self.controls_layout)

        # Buttons
        btns = qtw.QHBoxLayout()
        self.apply_btn = qtw.QPushButton("Apply")
        self.cancel_btn = qtw.QPushButton("Cancel")

        btns.addWidget(self.apply_btn)
        btns.addWidget(self.cancel_btn)

        layout.addLayout(btns)

        # -------------------------
        # Signals
        # -------------------------
        self.apply_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Initial render
        self.update_preview()

    # -------------------------
    # Public: add slider
    # -------------------------
    def add_slider(self, name, min_val, max_val, default):
        slider = qtw.QSlider(qtc.Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)

        label = qtw.QLabel(f"{name}: {default}")

        def on_change(val):
            self.params[name] = val
            label.setText(f"{name}: {val}")
            self.update_preview()

        slider.valueChanged.connect(on_change)

        self.controls_layout.addWidget(label)
        self.controls_layout.addWidget(slider)

        self.params[name] = default

    # -------------------------
    # Preview update
    # -------------------------
    def update_preview(self):
        # Left = original
        self.left_label.setPixmap(qtg.QPixmap.fromImage(self.original))

        # Right = processed
        processed = self.processor(self.original, self.params)

        if processed is not None:
            self.right_label.setPixmap(qtg.QPixmap.fromImage(processed))

    # -------------------------
    # Result getter
    # -------------------------
    def get_result(self):
        return self.processor(self.original, self.params)