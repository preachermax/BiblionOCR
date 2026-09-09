from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from Core.source_documents import assemble_image_folder


class ImageFolderAssemblyWorker(qtc.QObject):
    finished = qtc.pyqtSignal(str)
    failed = qtc.pyqtSignal(str)

    def __init__(self, source_dir, destination_path, assembler=None):
        super().__init__()
        self.source_dir = source_dir
        self.destination_path = destination_path
        self.assembler = assembler or assemble_image_folder

    @qtc.pyqtSlot()
    def run(self):
        try:
            output_path = self.assembler(self.source_dir, self.destination_path)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(output_path)


def start_image_folder_assembly(
    owner,
    source_dir,
    destination_path,
    on_finished,
    on_failed,
    assembler=None,
):
    if getattr(owner, "_document_assembly_thread", None) is not None:
        qtw.QMessageBox.information(
            owner,
            "Assembly In Progress",
            "Wait for the current document assembly to finish.",
        )
        return False

    progress = qtw.QProgressDialog(
        "Assembling multipage document...",
        "",
        0,
        0,
        owner,
    )
    progress.setCancelButton(None)
    progress.setWindowTitle("Assemble Image Folder")
    progress.setWindowModality(qtc.Qt.NonModal)
    progress.setMinimumDuration(0)

    thread = qtc.QThread(owner)
    worker = ImageFolderAssemblyWorker(
        source_dir,
        destination_path,
        assembler=assembler,
    )
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)

    action = getattr(getattr(owner, "ui", None), "actionAssembleImageFolder", None)
    if action is not None:
        action.setEnabled(False)

    def cleanup():
        progress.close()
        progress.deleteLater()
        if action is not None:
            action.setEnabled(True)
        owner._document_assembly_worker = None
        owner._document_assembly_thread = None
        owner._document_assembly_progress = None

    thread.finished.connect(cleanup)
    thread.finished.connect(thread.deleteLater)
    owner._document_assembly_thread = thread
    owner._document_assembly_worker = worker
    owner._document_assembly_progress = progress
    progress.show()
    thread.start()
    return True
