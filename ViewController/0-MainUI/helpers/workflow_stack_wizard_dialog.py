import typing as t

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw


class WorkflowStackWizardDialog(qtw.QDialog):
    """Stacked, stage-oriented workflow wizard with macro launch controls."""

    def __init__(
        self,
        title: str,
        intro_text: str,
        stage_plan: t.List[dict],
        run_stage_callback,
        run_all_callback,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 560)
        self.stage_plan = stage_plan
        self.run_stage_callback = run_stage_callback
        self.run_all_callback = run_all_callback

        self._build_ui(intro_text)
        self._populate_stage_pages()

    def _build_ui(self, intro_text: str):
        root_layout = qtw.QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        intro_label = qtw.QLabel(intro_text)
        intro_label.setWordWrap(True)
        root_layout.addWidget(intro_label)

        body_layout = qtw.QHBoxLayout()
        body_layout.setSpacing(8)
        root_layout.addLayout(body_layout, 1)

        self.stage_nav = qtw.QListWidget(self)
        self.stage_nav.setMinimumWidth(220)
        body_layout.addWidget(self.stage_nav)

        self.stage_stack = qtw.QStackedWidget(self)
        body_layout.addWidget(self.stage_stack, 1)

        self.stage_nav.currentRowChanged.connect(self.stage_stack.setCurrentIndex)

        footer_layout = qtw.QHBoxLayout()
        footer_layout.addStretch(1)

        self.run_all_button = qtw.QPushButton("Run Full Macro")
        self.run_all_button.clicked.connect(self._run_all)
        footer_layout.addWidget(self.run_all_button)

        self.close_button = qtw.QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_button)

        root_layout.addLayout(footer_layout)

    def _populate_stage_pages(self):
        for stage in self.stage_plan:
            stage_title = stage.get("title", "Stage")
            description = stage.get("description", "")
            steps = stage.get("steps", [])

            self.stage_nav.addItem(stage_title)

            page = qtw.QWidget(self)
            layout = qtw.QVBoxLayout(page)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)

            title_label = qtw.QLabel(stage_title)
            title_font = title_label.font()
            title_font.setBold(True)
            title_font.setPointSize(max(10, title_font.pointSize()))
            title_label.setFont(title_font)
            layout.addWidget(title_label)

            desc_label = qtw.QLabel(description)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

            step_list = qtw.QListWidget(page)
            for step in steps:
                step_list.addItem(f"{step.get('module', 'Module')}: {step.get('label', '')}")
            layout.addWidget(step_list, 1)

            run_stage_button = qtw.QPushButton(f"Run {stage_title} Macro")
            run_stage_button.clicked.connect(
                lambda _checked=False, stage_key=stage.get("key", ""): self._run_stage(stage_key)
            )
            layout.addWidget(run_stage_button)

            self.stage_stack.addWidget(page)

        if self.stage_nav.count() > 0:
            self.stage_nav.setCurrentRow(0)

    def _run_stage(self, stage_key: str):
        if not stage_key:
            return
        self.run_stage_callback(stage_key)

    def _run_all(self):
        self.run_all_callback()
