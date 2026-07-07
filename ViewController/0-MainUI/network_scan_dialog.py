from PyQt5.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from Core.Scanner import NetworkScanner


class NetworkScanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Network Scanner")
        self.resize(600, 400)

        self.layout = QVBoxLayout(self)

        self.statusLabel = QLabel("Ready")
        self.layout.addWidget(self.statusLabel)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["IP", "MAC"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.scanButton = QPushButton("Start Scan")
        self.layout.addWidget(self.scanButton)

        self.scanner = None
        self.scanButton.clicked.connect(self.startScan)

    def startScan(self):
        if self.scanner and self.scanner.isRunning():
            self.scanner.stop()
            self.scanner.wait()

        self.scanner = NetworkScanner()
        self.scanner.deviceFound.connect(self.onDeviceFound)
        self.scanner.progress.connect(self.onProgress)
        self.scanner.finished.connect(self.onFinished)

        self.table.setRowCount(0)
        self.statusLabel.setText("Scanning...")
        self.scanner.start()

    def onDeviceFound(self, device):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(device["ip"]))
        self.table.setItem(row, 1, QTableWidgetItem(device["mac"]))

    def onProgress(self, value):
        self.statusLabel.setText(f"Scanning... {value}%")

    def onFinished(self):
        self.statusLabel.setText("Scan complete")