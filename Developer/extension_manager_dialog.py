from __future__ import annotations

import sys

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from .extension_registry import ExtensionRegistry


class DeveloperExtensionManagerDialog(qtw.QDialog):
    def __init__(self, registry=None, parent=None):
        super().__init__(parent)
        self.registry = registry or ExtensionRegistry()
        self._service_dialogs = []
        self.setWindowTitle("Developer Extensions")
        self.resize(760, 460)

        layout = qtw.QVBoxLayout(self)
        splitter = qtw.QSplitter(self)
        self.extension_list = qtw.QListWidget(splitter)
        self.service_list = qtw.QListWidget(splitter)
        splitter.addWidget(self.extension_list)
        splitter.addWidget(self.service_list)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        self.description_label = qtw.QLabel(self)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        buttons = qtw.QDialogButtonBox(self)
        self.install_button = buttons.addButton("Install", qtw.QDialogButtonBox.ActionRole)
        self.uninstall_button = buttons.addButton("Uninstall", qtw.QDialogButtonBox.ActionRole)
        self.open_button = buttons.addButton("Open Service", qtw.QDialogButtonBox.ActionRole)
        close_button = buttons.addButton(qtw.QDialogButtonBox.Close)
        layout.addWidget(buttons)

        self.extension_list.currentRowChanged.connect(self._refresh_selection)
        self.service_list.currentRowChanged.connect(self._refresh_buttons)
        self.install_button.clicked.connect(self._install_selected)
        self.uninstall_button.clicked.connect(self._uninstall_selected)
        self.open_button.clicked.connect(self._open_selected_service)
        close_button.clicked.connect(self.reject)
        self.refresh()

    def refresh(self) -> None:
        selected_id = self._selected_extension_id()
        self.extension_list.clear()
        for extension in self.registry.bundled_extensions():
            status = "Installed" if self.registry.is_installed(extension.extension_id) else "Available"
            item = qtw.QListWidgetItem(f"{extension.name}  [{status}]")
            item.setData(qtc.Qt.UserRole, extension.extension_id)
            self.extension_list.addItem(item)
            if extension.extension_id == selected_id:
                self.extension_list.setCurrentItem(item)
        if self.extension_list.currentRow() < 0 and self.extension_list.count():
            self.extension_list.setCurrentRow(0)
        self._refresh_selection()

    def _selected_extension_id(self):
        item = self.extension_list.currentItem()
        return item.data(qtc.Qt.UserRole) if item is not None else None

    def _selected_service_id(self):
        item = self.service_list.currentItem()
        return item.data(qtc.Qt.UserRole) if item is not None else None

    def _refresh_selection(self, _row=-1) -> None:
        self.service_list.clear()
        extension_id = self._selected_extension_id()
        if not extension_id:
            self.description_label.clear()
            self._refresh_buttons()
            return
        extension = self.registry.bundled_extension(extension_id)
        self.description_label.setText(extension.description)
        if self.registry.is_installed(extension_id):
            for service in self.registry.installed_extension(extension_id).services:
                item = qtw.QListWidgetItem(service.name)
                item.setToolTip(service.description)
                item.setData(qtc.Qt.UserRole, service.service_id)
                self.service_list.addItem(item)
        if self.service_list.count():
            self.service_list.setCurrentRow(0)
        self._refresh_buttons()

    def _refresh_buttons(self, _row=-1) -> None:
        extension_id = self._selected_extension_id()
        installed = bool(extension_id and self.registry.is_installed(extension_id))
        self.install_button.setEnabled(bool(extension_id and not installed))
        self.uninstall_button.setEnabled(installed)
        self.open_button.setEnabled(bool(installed and self._selected_service_id()))

    def _install_selected(self) -> None:
        extension_id = self._selected_extension_id()
        if extension_id:
            self.registry.install(extension_id)
            self.refresh()

    def _uninstall_selected(self) -> None:
        extension_id = self._selected_extension_id()
        if extension_id:
            self.registry.uninstall(extension_id)
            self.refresh()

    def _open_selected_service(self) -> None:
        extension_id = self._selected_extension_id()
        service_id = self._selected_service_id()
        if not extension_id or not service_id:
            return
        service_class = self.registry.load_service(extension_id, service_id)
        dialog = service_class(parent=self)
        self._service_dialogs.append(dialog)
        dialog.finished.connect(lambda _result, current=dialog: self._service_dialogs.remove(current))
        dialog.show()


def main() -> int:
    application = qtw.QApplication.instance() or qtw.QApplication(sys.argv)
    dialog = DeveloperExtensionManagerDialog()
    dialog.show()
    return application.exec_()


if __name__ == "__main__":
    raise SystemExit(main())