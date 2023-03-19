# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Variants.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 539)

        font = QtGui.QFont("FROMVS", 12)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.BookLabel = QtWidgets.QLabel(self.centralwidget)
        self.BookLabel.setGeometry(QtCore.QRect(170, 10, 67, 17))
        self.BookLabel.setObjectName("BookLabel")

        self.BookLE = QtWidgets.QLineEdit(self.centralwidget)
        self.BookLE.setGeometry(QtCore.QRect(170, 30, 113, 25))
        self.BookLE.setObjectName("BookLE")
        self.BookLE.setFont(font)
        self.BookLE.setPlaceholderText("Book")
        self.BookLE.setReadOnly(True)
        
        self.ChapterLabel = QtWidgets.QLabel(self.centralwidget)
        self.ChapterLabel.setGeometry(QtCore.QRect(330, 10, 67, 17))
        self.ChapterLabel.setObjectName("ChapterLabel")

        self.ChapterLE = QtWidgets.QLineEdit(self.centralwidget)
        self.ChapterLE.setGeometry(QtCore.QRect(330, 30, 113, 25))
        self.ChapterLE.setObjectName("ChapterLE")
        self.ChapterLE.setFont(font)
        self.ChapterLE.setPlaceholderText("Chapter")
        self.ChapterLE.setReadOnly(True)
        
        self.VerseLabel = QtWidgets.QLabel(self.centralwidget)
        self.VerseLabel.setGeometry(QtCore.QRect(490, 10, 67, 17))
        self.VerseLabel.setObjectName("VerseLable")

        self.VerseLE = QtWidgets.QLineEdit(self.centralwidget)
        self.VerseLE.setGeometry(QtCore.QRect(490, 30, 113, 25))
        self.VerseLE.setObjectName("VerseLE")
        self.VerseLE.setFont(font)
        self.VerseLE.setPlaceholderText("Verse")
        self.VerseLE.setReadOnly(True)

        self.WordLabel = QtWidgets.QLabel(self.centralwidget)
        self.WordLabel.setGeometry(QtCore.QRect(170, 70, 67, 17))
        self.WordLabel.setObjectName("WordLabel")

        self.WordLE = QtWidgets.QLineEdit(self.centralwidget)
        self.WordLE.setGeometry(QtCore.QRect(170, 90, 113, 25))
        self.WordLE.setObjectName("WordLE")
        self.WordLE.setFont(font)
        self.WordLE.setPlaceholderText("Word")
        self.WordLE.setReadOnly(True)

        self.NoDiaWordLabel = QtWidgets.QLabel(self.centralwidget)
        self.NoDiaWordLabel.setGeometry(QtCore.QRect(330, 70, 81, 17))
        self.NoDiaWordLabel.setObjectName("NoDiaWordLabel")

        self.NoDiaWordLE = QtWidgets.QLineEdit(self.centralwidget)
        self.NoDiaWordLE.setGeometry(QtCore.QRect(330, 90, 113, 25))
        self.NoDiaWordLE.setObjectName("NoDiaWordLE")
        self.NoDiaWordLE.setFont(font)
        self.NoDiaWordLE.setPlaceholderText("NoDiaWord")
        self.NoDiaWordLE.setReadOnly(True)

        self.VarWordSelLabel = QtWidgets.QLabel(self.centralwidget)
        self.VarWordSelLabel.setGeometry(QtCore.QRect(490, 70, 135, 17))
        self.VarWordSelLabel.setObjectName("VarWordSelLabel")
        
        self.VarWordSelCombo = QtWidgets.QComboBox(self.centralwidget)
        self.VarWordSelCombo.setGeometry(QtCore.QRect(490, 90, 160, 25))
        self.VarWordSelCombo.setObjectName("VarWordSelCombo")
        self.VarWordSelCombo.setFont(font)

        self.FormLabel = QtWidgets.QLabel(self.centralwidget)
        self.FormLabel.setGeometry(QtCore.QRect(170, 130, 67, 17))
        self.FormLabel.setObjectName("FormLabel")

        self.PreservedCkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.PreservedCkBox.setGeometry(QtCore.QRect(170, 150, 111, 23))
        self.PreservedCkBox.setObjectName("PreservedCkBox")
        
        self.CriticalCkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.CriticalCkBox.setGeometry(QtCore.QRect(170, 180, 92, 23))
        self.CriticalCkBox.setObjectName("CriticalCkBox")
        
        self.TypeLabel = QtWidgets.QLabel(self.centralwidget)
        self.TypeLabel.setGeometry(QtCore.QRect(330, 130, 67, 17))
        self.TypeLabel.setObjectName("TypeLabel")
        
        self.ErrorCkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.ErrorCkBox.setGeometry(QtCore.QRect(330, 150, 92, 23))
        self.ErrorCkBox.setObjectName("ErrorCkBox")
        
        self.VarianceCkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.VarianceCkBox.setGeometry(QtCore.QRect(330, 180, 101, 23))
        self.VarianceCkBox.setObjectName("VarianceCkBox")
        
        self.ImpactLabel = QtWidgets.QLabel(self.centralwidget)
        self.ImpactLabel.setGeometry(QtCore.QRect(490, 130, 67, 17))
        self.ImpactLabel.setObjectName("ImpactLabel")
        
        self.ContextCkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.ContextCkBox.setGeometry(QtCore.QRect(490, 150, 92, 23))
        self.ContextCkBox.setObjectName("ContextCkBox")
        
        self.InflectionCkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.InflectionCkBox.setGeometry(QtCore.QRect(490, 180, 101, 23))
        self.InflectionCkBox.setObjectName("InflectionCkBox")

        self.PreviousButton = QtWidgets.QPushButton(self.centralwidget)
        self.PreviousButton.setGeometry(QtCore.QRect(50, 200, 89, 25))
        self.PreviousButton.setFont(QtGui.QFont('FROMVS', 8))
        self.PreviousButton.setIcon(QtGui.QIcon.fromTheme("previous"))
        self.PreviousButton.setObjectName("PreviousButton")
        
        self.NextButton = QtWidgets.QPushButton(self.centralwidget)
        self.NextButton.setGeometry(QtCore.QRect(650, 200, 89, 25))
        self.NextButton.setFont(QtGui.QFont('FROMVS', 8))
        self.NextButton.setIcon(QtGui.QIcon.fromTheme("next"))
        self.NextButton.setObjectName("NextButton")
        
        self.ErrorCodeLabel = QtWidgets.QLabel(self.centralwidget)
        self.ErrorCodeLabel.setGeometry(QtCore.QRect(170, 240, 81, 17))
        self.ErrorCodeLabel.setObjectName("ErrorCodeLabel")
        
        self.ErrorCodeCombo = QtWidgets.QComboBox(self.centralwidget)
        self.ErrorCodeCombo.setGeometry(QtCore.QRect(170, 260, 111, 25))
        self.ErrorCodeCombo.setObjectName("ErrorCodeCombo")

        self.VarianceCodeLabel = QtWidgets.QLabel(self.centralwidget)
        self.VarianceCodeLabel.setGeometry(QtCore.QRect(170, 300, 120, 17))
        self.VarianceCodeLabel.setObjectName("VarianceCodeLabel")

        self.VarianceCodeLE = QtWidgets.QLineEdit(self.centralwidget)
        self.VarianceCodeLE.setGeometry(QtCore.QRect(170, 320, 113, 25))
        self.VarianceCodeLE.setObjectName("VarianceCodeLE")
        self.VarianceCodeLE.setFont(font)
        self.VarianceCodeLE.setPlaceholderText("Variance Code")
        self.VarianceCodeLE.setReadOnly(True)
        
        self.DescriptionTextEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.DescriptionTextEdit.setGeometry(QtCore.QRect(330, 260, 301, 81))
        self.DescriptionTextEdit.setObjectName("DescriptionTextEdit")
        self.DescriptionTextEdit.setFont(font)

        self.DescriptionLabel = QtWidgets.QLabel(self.centralwidget)
        self.DescriptionLabel.setGeometry(QtCore.QRect(330, 240, 81, 17))
        self.DescriptionLabel.setObjectName("DescriptionLabel")
        
        self.StrongsLabel = QtWidgets.QLabel(self.centralwidget)
        self.StrongsLabel.setGeometry(QtCore.QRect(170, 370, 67, 17))
        self.StrongsLabel.setObjectName("StrongsLabel")

        self.StrongsLE = QtWidgets.QLineEdit(self.centralwidget)
        self.StrongsLE.setGeometry(QtCore.QRect(170, 390, 113, 25))
        self.StrongsLE.setObjectName("StrongsLE")
        self.StrongsLE.setPlaceholderText("Strong's")
        self.StrongsLE.setReadOnly(True)
        
        self.LemmaLabel = QtWidgets.QLabel(self.centralwidget)
        self.LemmaLabel.setGeometry(QtCore.QRect(330, 370, 67, 17))
        self.LemmaLabel.setObjectName("LemmaLabel")

        self.LemmaLE = QtWidgets.QLineEdit(self.centralwidget)
        self.LemmaLE.setGeometry(QtCore.QRect(330, 390, 113, 25))
        self.LemmaLE.setObjectName("LemmaLE")
        self.LemmaLE.setFont(font)
        self.LemmaLE.setPlaceholderText("Lemma")
        self.LemmaLE.setReadOnly(True)
        
        self.RMACLabel = QtWidgets.QLabel(self.centralwidget)
        self.RMACLabel.setGeometry(QtCore.QRect(490, 370, 67, 17))
        self.RMACLabel.setObjectName("RMACLabel")

        self.RMACLE = QtWidgets.QLineEdit(self.centralwidget)
        self.RMACLE.setGeometry(QtCore.QRect(490, 390, 113, 25))
        self.RMACLE.setObjectName("RMACLE")
        self.RMACLE.setPlaceholderText("RMAC")
        self.RMACLE.setReadOnly(True)
    
        self.UpdateButton = QtWidgets.QPushButton(self.centralwidget)
        self.UpdateButton.setGeometry(QtCore.QRect(290, 450, 89, 25))
        self.UpdateButton.setFont(QtGui.QFont('FROMVS', 8))
        self.UpdateButton.setIcon(QtGui.QIcon.fromTheme("up"))
        self.UpdateButton.setObjectName("UpdateButton")
        
        self.UpdateAllButton = QtWidgets.QPushButton(self.centralwidget)
        self.UpdateAllButton.setGeometry(QtCore.QRect(420, 450, 89, 25))
        self.UpdateAllButton.setFont(QtGui.QFont('FROMVS', 8))
        self.UpdateAllButton.setIcon(QtGui.QIcon.fromTheme("top"))
        self.UpdateAllButton.setObjectName("UpdateAllButton")
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        #self.OCRbutton.setFont(QtGui.QFont('FROMVS', 8))
        #self.OCRbutton.setIcon(QtGui.QIcon.fromTheme("gtk-execute"))

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        
        self.BookLabel.setText(_translate("MainWindow", "Book"))
        self.ChapterLabel.setText(_translate("MainWindow", "Chapter"))
        self.VerseLabel.setText(_translate("MainWindow", "Verse"))
     
        self.WordLabel.setText(_translate("MainWindow", "Word"))
        self.NoDiaWordLabel.setText(_translate("MainWindow", "NoDiaWord"))
        self.VarWordSelLabel.setText(_translate("MainWindow", "Variant Word Select"))

        self.FormLabel.setText(_translate("MainWindow", "Form"))
        self.PreservedCkBox.setText(_translate("MainWindow", "Preserved(P)"))
        self.CriticalCkBox.setText(_translate("MainWindow", "Critical(C)"))

        self.TypeLabel.setText(_translate("MainWindow", "Type"))
        self.ErrorCkBox.setText(_translate("MainWindow", "Error(E)"))
        self.VarianceCkBox.setText(_translate("MainWindow", "Variance(V)"))
        
        self.ImpactLabel.setText(_translate("MainWindow", "Impact"))
        self.ContextCkBox.setText(_translate("MainWindow", "Context(C)"))
        self.InflectionCkBox.setText(_translate("MainWindow", "Inflection(I)"))

        self.PreviousButton.setText(_translate("MainWindow", "Previous"))
        self.NextButton.setText(_translate("MainWindow", "Next"))
        
        self.ErrorCodeLabel.setText(_translate("MainWindow", "Error Select"))
        self.VarianceCodeLabel.setText(_translate("MainWindow", "Variance Code"))
        self.DescriptionLabel.setText(_translate("MainWindow", "Description"))

        self.StrongsLabel.setText(_translate("MainWindow", "Strong\'s"))
        self.LemmaLabel.setText(_translate("MainWindow", "Lemma"))
        self.RMACLabel.setText(_translate("MainWindow", "RMAC"))
        
        self.UpdateButton.setText(_translate("MainWindow", "Update"))
        self.UpdateAllButton.setText(_translate("MainWindow", "Update All"))



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

