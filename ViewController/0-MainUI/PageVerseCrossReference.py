import json
import pandas as pd
import sys

from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5 import QtWidgets as qtw
from PyQt5.QtWidgets import QApplication, QTableView

from Dialogs.PageVerseXrefDialog import Ui_PageVerseXrefDialog

df = pd.read_json('/home/max/Projects/BiblionOCR/Model/Project/Data/json/PageVerseCrossReference.json')

class DateTimeDelegate(qtw.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(DateTimeDelegate, self).initStyleOption(option, index)
        value = index.data()
        option.text = qtc.QDateTime.fromMSecsSinceEpoch(value).toString("dd.MM.yyyy")

class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class Ui_MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.ui = Ui_Grounder()
        #self.ui.setupUi(self)  
        print("Page Verse Cross Reference Dialog")
        # usage: tr.renumberimages(source, destination)
        self.PageVerseXrefDialog = qtw.QDialog()
        self.ui  = Ui_PageVerseXrefDialog()
        self.ui.setupUi(self.PageVerseXrefDialog)
        
        self.ui.LinefindPushButton.clicked.connect(self.linefind(self.ui.PagecomboBox.currentText(), self.ui.LinecomboBox.currentText()))
        self.ui.VersefindPushButton.clicked.connect(self.versefind(self.ui.StartbookComboBox.currentText(), self.ui.StartchapterComboBox.currentText(), self.ui.StartverseComboBox))

    def linefind(self, page, line):

    def versefind(self, book, chapter, verse):



if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    
    model = pandasModel(df)
    
    #w = Ui_MainWindow()
    #w.show()
   
    view = QTableView()
    view.setModel(model)
    view.resize(800, 600)
    # view.show()
    sys.exit(app.exec_())






'''if __name__ == "__main__":
    import sys

    app = qtw.QApplication(sys.argv)

    with open('/home/max/Projects/BiblionOCR/Model/Project/Data/json/PageVerseCrossReference.json') as f:
        data = json.load(f)
        #print(data)

    df = pd.DataFrame(data)
    keys = df.columns
    #print(keys[1])
    #df.columns
    d = json.loads(data)
    #print(df.head())
    #keys = ["Date", "Type", "Published", "Sent"]
    labels = keys + ["ID"]
    print(labels)

    w = qtw.QTableWidget(0, len(labels))
    delegate = DateTimeDelegate(w)
    w.setItemDelegateForColumn(0, delegate)
    w.setColumnHidden(4, True)
    w.setHorizontalHeaderLabels(labels)

    for i, (key, value) in enumerate(d["events"].items()):
        rows = [
            value[k]
            if k != "Date"
            else qtc.QDateTime.fromString(value[k], "dd.MM.yyyy").toMSecsSinceEpoch()
            for k in keys
        ] + [key]
        w.insertRow(w.rowCount())
        for j, v in enumerate(rows):
            it = qtw.QTableWidgetItem()
            it.setData(qtc.Qt.DisplayRole, v)
            w.setItem(i, j, it)
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())'''