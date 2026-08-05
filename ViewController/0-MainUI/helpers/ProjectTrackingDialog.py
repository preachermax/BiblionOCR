import os

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from Core.project_tracking import MODULE_SEQUENCE


class ProjectTrackingDialog(qtw.QDialog):
    def __init__(self, tracker, project_root, module_name, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.project_root = project_root
        self.module_name = module_name
        self._row_widgets = {}

        self.setWindowTitle(f"Project Milestones - {module_name}")
        self.resize(760, 420)

        layout = qtw.QVBoxLayout(self)

        self.project_label = qtw.QLabel()
        self.project_label.setWordWrap(True)
        layout.addWidget(self.project_label)

        self.tracking_file_label = qtw.QLabel()
        self.tracking_file_label.setWordWrap(True)
        layout.addWidget(self.tracking_file_label)

        self.table = qtw.QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels([
            "Module",
            "Sequence",
            "Milestone",
            "Weight",
            "Complete",
            "Completed At",
            "Updated By",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(qtw.QAbstractItemView.NoSelection)
        self.table.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, qtw.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, qtw.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, qtw.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, qtw.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, qtw.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, qtw.QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        button_row = qtw.QHBoxLayout()
        self.reload_button = qtw.QPushButton("Reload")
        self.save_button = qtw.QPushButton("Save")
        self.close_button = qtw.QPushButton("Close")
        button_row.addWidget(self.reload_button)
        button_row.addStretch(1)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.reload_button.clicked.connect(self.reload_rows)
        self.save_button.clicked.connect(self.save_rows)
        self.close_button.clicked.connect(self.accept)

        self.reload_rows()

    def reload_rows(self):
        self._row_widgets = {}
        rows = self.tracker.milestone_rows(self.project_root)
        rows = sorted(rows, key=self._milestone_row_sort_key)
        self.table.setRowCount(len(rows))

        self.project_label.setText(f"Project: {os.path.basename(self.project_root)}")
        self.project_label.setToolTip(self.project_root)
        self.tracking_file_label.setText(
            f"Tracking file: {self.tracker.tracking_file_path(self.project_root)}"
        )

        for row_index, row in enumerate(rows):
            module_item = qtw.QTableWidgetItem(str(row.get("module", "Workflow")))
            module_item.setFlags(qtc.Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, module_item)

            sequence_item = qtw.QTableWidgetItem(str(row.get("sequence", row_index + 1)))
            sequence_item.setFlags(qtc.Qt.ItemIsEnabled)
            self.table.setItem(row_index, 1, sequence_item)

            label_item = qtw.QTableWidgetItem(str(row.get("label", row.get("key", ""))))
            label_item.setFlags(qtc.Qt.ItemIsEnabled)
            self.table.setItem(row_index, 2, label_item)

            weight_box = qtw.QSpinBox(self.table)
            weight_box.setRange(1, 1000)
            weight_box.setValue(int(row.get("weight", 1)))
            self.table.setCellWidget(row_index, 3, weight_box)

            complete_box = qtw.QCheckBox(self.table)
            complete_box.setChecked(bool(row.get("complete", False)))
            complete_container = qtw.QWidget(self.table)
            complete_layout = qtw.QHBoxLayout(complete_container)
            complete_layout.setContentsMargins(8, 0, 8, 0)
            complete_layout.addWidget(complete_box)
            complete_layout.addStretch(1)
            self.table.setCellWidget(row_index, 4, complete_container)

            completed_at = qtw.QTableWidgetItem(str(row.get("completed_at") or ""))
            completed_at.setFlags(qtc.Qt.ItemIsEnabled)
            self.table.setItem(row_index, 5, completed_at)

            updated_by = qtw.QTableWidgetItem(str(row.get("updated_by") or ""))
            updated_by.setFlags(qtc.Qt.ItemIsEnabled)
            self.table.setItem(row_index, 6, updated_by)

            self._row_widgets[row.get("key")] = {
                "weight": weight_box,
                "complete": complete_box,
            }

        self.table.resizeRowsToContents()

    def _module_rank(self, module_name):
        module = str(module_name or "").strip()
        if module in MODULE_SEQUENCE:
            return MODULE_SEQUENCE.index(module)
        return len(MODULE_SEQUENCE)

    def _milestone_row_sort_key(self, row_data):
        return (
            self._module_rank(row_data.get("module")),
            int(row_data.get("sequence", 10_000)),
            str(row_data.get("key", "")),
        )

    def save_rows(self):
        updates = {}
        for milestone_key, widgets in self._row_widgets.items():
            updates[milestone_key] = {
                "weight": widgets["weight"].value(),
                "complete": widgets["complete"].isChecked(),
            }

        self.tracker.update_milestones(
            self.project_root,
            updates,
            updated_by=f"{self.module_name}:manual",
        )
        self.reload_rows()
        qtw.QMessageBox.information(self, "Project Milestones", "Project milestone state saved.")