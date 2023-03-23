# -*- coding: utf-8 -*-

import sys
import os
import json

from PyQt5 import QtPrintSupport
#from PyQt5 import QPrintPreviewDialog, QPrintDialog
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import Qt

from ext import *

from MyWriterUI import Ui_MyWriterUI

class Main(qtw.QMainWindow):
    def __init__(self,parent=None):
        qtw.QMainWindow.__init__(self,parent)

        self.txtpath = ""
        self.txtdir = ""
        self.filename = ""
        self.iconsfolder = "ViewController/0-MainUI/Icons"
        self.changesSaved = True

        self.ui = Ui_MyWriterUI()
        self.ui.setupUi(self)
        self.initUI()
        
        self.ui.TextDocument = qtg.QTextDocument(self.ui.textEdit)
        self.font = qtg.QFont()
        self.font.setFamily("FROMVS [MAXR]")
        self.font.setPointSize(20)
        self.ui.TextDocument.setDefaultFont(self.font)
        self.ui.TextBlockFormat = qtg.QTextBlockFormat()
        #self.ui.TextFormat = qtg.QTextFormat()
        self.ui.TextCursor = qtg.QTextCursor(self.ui.TextDocument)
        #self.ui.textEdit.setDocument(self.ui.TextDocument)'''

        #self.show()

    def get_session_settings(self):
        # get session settings
        # Define json data        
        print("loading session")
        with open('Model/Project/Data/json/Session.json') as f:
            # returns JSON object as a dictionary
            data = json.load(f)
            
            # Set json key values
            bookabbr_key = r"self.bookabbr"
            chapter_key = r"self.chapter"
            verse_key = r"self.verse"
            word_key = r"self.word"
            chr_key = r"self.chr"
            font_key = r"self.font"
            fontsize_key = r"self.fontsize"
            linespacing_key = r"self.verselinespacing"
            reflinespacing_key = r"self.reflinespacing"
            source_book_markdown_key = r"self.sourcebookmarkdown"
            greek_book_markdown_key = r"self.greekbookmarkdown"
            latin_book_markdown_key = r"self.latinbookmarkdown"
            txtpath_key = r"self.txtpath"
            txtdir_key = r"self.txtdir"
            txtfileList_key = r"self.txtfileList"
            reftxtpath_key = r"self.reftxtpath"
            reftxtdir_key = r"self.reftxtdir"
            reftxtfileList_key = r"self.reftxtfileList"

            print(bookabbr_key,chapter_key)
            # Find the json key values using 'in' operator
            # Define session variables from json key values
            for Setting in data:
                print('Setting: ',Setting['Setting'],Setting['CurrentValue'])
                
                if Setting['Setting'] == bookabbr_key:  
                    self.bookabbr = Setting['CurrentValue']
                    #self.ui.bookComboBox.setCurrentText(self.bookabbr)            
                elif Setting['Setting'] == chapter_key:  
                    self.chapter = Setting['CurrentValue']          
                elif Setting['Setting'] == verse_key:
                    self.verse = Setting['CurrentValue']
                elif Setting['Setting'] == word_key:
                    self.word = Setting['CurrentValue'] 
                elif Setting['Setting'] == chr_key:
                    self.chr = Setting['CurrentValue']
                elif Setting['Setting'] == font_key:
                    self.font = Setting['CurrentValue']
                elif Setting['Setting'] == fontsize_key:
                    self.fontsize = Setting['CurrentValue']
                    #  self.ui.fontSizeBox.setValue(int(self.fontsize))           
                elif Setting['Setting'] == source_book_markdown_key:  
                    self.sourcebookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == greek_book_markdown_key:  
                    self.greekbookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == latin_book_markdown_key:  
                    self.latinbookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == txtpath_key:  
                    self.txtpath = Setting['CurrentValue'] 
                elif Setting['Setting'] == txtdir_key:  
                    self.txtdir = Setting['CurrentValue']
                elif Setting['Setting'] == reftxtpath_key:  
                    self.reftxtpath = Setting['CurrentValue'] 
                elif Setting['Setting'] == reftxtdir_key:  
                    self.reftxtdir = Setting['CurrentValue']
                
                print('New Setting: ',Setting['Setting'],Setting['CurrentValue'])
            f.close()
   
    def initToolbar(self):
        # new widgets       
        self.textLineEdit = qtw.QLineEdit(self)
        self.textLineEdit.setEnabled(True)
        self.textLineEdit.setFixedSize(300, 25)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(11)
        self.textLineEdit.setFont(font)
        self.textLineEdit.setMaxLength(32767)
        self.textLineEdit.setAlignment(qtc.Qt.AlignCenter)
        self.textLineEdit.setObjectName("textLineEdit")
        self.textLineEdit.setPlaceholderText(os.path.basename(self.txtpath))
        
        # add widgets
        self.ui.toolbar.addWidget(self.textLineEdit)
        
        # signals(slots)
        self.ui.actionImport.triggered.connect(self.importfile)
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpenFile.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.saveastextDialog)
        self.ui.actionSave_As.triggered.connect(self.saveastextDialog)
        self.ui.actionFind_Replace.triggered.connect(find.Find(self).show)
        self.ui.actionCut.triggered.connect(self.ui.textEdit.cut)
        self.ui.actionCopy.triggered.connect(self.ui.textEdit.copy)
        self.ui.actionPaste.triggered.connect(self.ui.textEdit.paste)
        self.ui.actionUndo.triggered.connect(self.ui.textEdit.undo)
        self.ui.actionRedo.triggered.connect(self.ui.textEdit.redo)
        self.ui.actionDateTime.triggered.connect(datetime.DateTime(self).show)
        self.ui.actionWordcount.triggered.connect(self.wordCount)
        self.ui.actionInsertTable.triggered.connect(table.Table(self).show)
        #self.ui.actionInsertImage.triggered.connect(self.insertImage)
        self.ui.actionBulletList.triggered.connect(self.bulletList)
        self.ui.actionNumberedList.triggered.connect(self.numberList)

    def initFormatbar(self):
        # new widgets
        self.LHlineEdit = qtw.QLineEdit(self)
        self.LHlineEdit.setEnabled(True)
        self.LHlineEdit.setFixedSize(41, 25)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(11)
        self.LHlineEdit.setFont(font)
        self.LHlineEdit.setMaxLength(32767)
        self.LHlineEdit.setAlignment(qtc.Qt.AlignCenter)
        self.LHlineEdit.setObjectName("LHlineEdit")
        self.LHlineEdit.setPlaceholderText(str(self.ui.LHslider.value()))

        # add widgets        
        self.ui.formatbar.addWidget(self.LHlineEdit)
       
        # signals(slots)
        self.ui.actionHighlightText.triggered.connect(self.highlight)
        self.ui.actionLeftJustify.triggered.connect(self.alignLeft)
        self.ui.actionCenterAlign.triggered.connect(self.alignCenter)
        self.ui.actionRightJustify.triggered.connect(self.alignRight)
        self.ui.actionJustify.triggered.connect(self.alignJustify)
        self.ui.actionIndent.triggered.connect(self.indent)
        self.ui.actionOutdent.triggered.connect(self.dedent)

        self.ui.actionLineSpacing.triggered.connect(self.GetLineSpacing)
        self.ui.LHslider.valueChanged.connect(self.SetLineSpacing)
        self.ui.LHslider.sliderReleased.connect(self.DisableLHSlider)
        self.ui.LHslider.hide()
        self.LHlineEdit.textChanged.connect(self.MoveLHSlider)

    def initFontbar(self):
        # new widgets
        self.fontBox = qtw.QFontComboBox(self)
        #self.fontBox.currentFontChanged.connect(lambda font: self.ui.textEdit.setCurrentFont(qtg.QFont(self.font)))
        self.fontSize = qtw.QSpinBox(self)
        # Will display " pt" after each value
        self.fontSize.setSuffix(" pt")
        self.fontSize.setValue(20)

        # add widgets
        self.ui.fontbar.addWidget(self.fontBox)
        self.ui.fontbar.addWidget(self.fontSize)

        # signals(slots)
        self.fontBox.currentFontChanged.connect(self.on_font_update)
        self.fontSize.valueChanged.connect(lambda size: self.ui.textEdit.setFontPointSize(size))

    def initMarkupbar(self):
        # signals(slots)
        self.ui.actionFontColor.triggered.connect(self.fontColorChanged)
        self.ui.actionBold.triggered.connect(self.bold)
        self.ui.actionItalic.triggered.connect(self.italic)
        self.ui.actionUnderline.triggered.connect(self.underline)
        self.ui.actionStrikeThrough.triggered.connect(self.strike)
        self.ui.actionSuperscript.triggered.connect(self.superScript)
        self.ui.actionSubscript.triggered.connect(self.subScript)

    def initMenubar(self):

        # Toggling actions for the various bars
        filebarAction = qtw.QAction("Toggle Filebar",self)
        filebarAction.triggered.connect(self.toggleFilebar)

        editbarAction = qtw.QAction("Toggle Filebar",self)
        editbarAction.triggered.connect(self.toggleEditbar)
        
        formatbarAction = qtw.QAction("Toggle Formatbar",self)
        formatbarAction.triggered.connect(self.toggleFormatbar)

        fontbarAction = qtw.QAction("Toggle Fontbar",self)
        fontbarAction.triggered.connect(self.toggleFontbar)

        markupbarAction = qtw.QAction("Toggle Fontbar",self)
        markupbarAction.triggered.connect(self.toggleMarkupbar)

        statusbarAction = qtw.QAction("Toggle Statusbar",self)
        statusbarAction.triggered.connect(self.toggleStatusbar)

    def initUI(self):

        #self.ui.textEdit = qtw.QTextEdit(self)

        # Set the tab stop width to around 33 pixels which is
        # more or less 8 spaces
        self.ui.textEdit.setTabStopWidth(33)
        self.get_session_settings()        
        self.initMenubar()
        self.initToolbar()
        self.initFormatbar()
        self.initFontbar()
        self.initMarkupbar()


        # If the cursor position changes, call the function that displays
        # the line and column number
        self.ui.textEdit.cursorPositionChanged.connect(self.cursorPosition)

        # We need our own context menu for tables
        self.ui.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.textEdit.customContextMenuRequested.connect(self.context)

        self.ui.textEdit.textChanged.connect(self.changed)

        self.setGeometry(100,100,1030,800)
        '''self.setWindowTitle("My Writer")
        self.setWindowIcon(qtg.QIcon(self.iconsfolder + "/icon.png"))'''

        self.get_session_settings()
        if self.txtpath != "":
            self.importfile()

    def changed(self):
        self.changesSaved = False

    def closeEvent(self,event):

        if self.changesSaved:

            event.accept()

        else:
        
            popup = qtw.QMessageBox(self)

            popup.setIcon(qtw.QMessageBox.Warning)
            
            popup.setText("The document has been modified")
            
            popup.setInformativeText("Do you want to save your changes?")
            
            popup.setStandardButtons(qtw.QMessageBox.Save   |
                                      qtw.QMessageBox.Cancel |
                                      qtw.QMessageBox.Discard)
            
            popup.setDefaultButton(qtw.QMessageBox.Save)

            answer = popup.exec_()

            if answer == qtw.QMessageBox.Save:
                self.save()

            elif answer == qtw.QMessageBox.Discard:
                event.accept()

            else:
                event.ignore()

    def context(self,pos):

        # Grab the cursor
        cursor = self.ui.textEdit.textCursor()

        # Grab the current table, if there is one
        table = cursor.currentTable()

        # Above will return 0 if there is no current table, in which case
        # we call the normal context menu. If there is a table, we create
        # our own context menu specific to table interaction
        if table:

            menu = qtg.QMenu(self)

            appendRowAction = qtw.QAction("Append row",self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))

            appendColAction = qtw.QAction("Append column",self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))


            removeRowAction = qtw.QAction("Remove row",self)
            removeRowAction.triggered.connect(self.removeRow)

            removeColAction = qtw.QAction("Remove column",self)
            removeColAction.triggered.connect(self.removeCol)


            insertRowAction = qtw.QAction("Insert row",self)
            insertRowAction.triggered.connect(self.insertRow)

            insertColAction = qtw.QAction("Insert column",self)
            insertColAction.triggered.connect(self.insertCol)


            mergeAction = qtw.QAction("Merge cells",self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))

            # Only allow merging if there is a selection
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)


            splitAction = qtw.QAction("Split cells",self)

            cell = table.cellAt(cursor)

            # Only allow splitting if the current cell is larger
            # than a normal cell
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:

                splitAction.triggered.connect(lambda: table.splitCell(cell.row(),cell.column(),1,1))

            else:
                splitAction.setEnabled(False)


            menu.addAction(appendRowAction)
            menu.addAction(appendColAction)

            menu.addSeparator()

            menu.addAction(removeRowAction)
            menu.addAction(removeColAction)

            menu.addSeparator()

            menu.addAction(insertRowAction)
            menu.addAction(insertColAction)

            menu.addSeparator()

            menu.addAction(mergeAction)
            menu.addAction(splitAction)

            # Convert the widget coordinates into global coordinates
            pos = self.mapToGlobal(pos)

            # Add pixels for the tool and formatbars, which are not included
            # in mapToGlobal(), but only if the two are currently visible and
            # not toggled by the user

            if self.filebar.isVisible():
                pos.setY(pos.y() + 45)

            if self.formatbar.isVisible():
                pos.setY(pos.y() + 45)
                
            # Move the menu to the new position
            menu.move(pos)

            menu.show()

        else:

            event = qtg.QContextMenuEvent(qtg.QContextMenuEvent.Mouse,qtc.QPoint())

            self.ui.textEdit.contextMenuEvent(event)

    def removeRow(self):

        # Grab the cursor
        cursor = self.ui.textEdit.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Delete the cell's row
        table.removeRows(cell.row(),1)

    def removeCol(self):

        # Grab the cursor
        cursor = self.ui.textEdit.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Delete the cell's column
        table.removeColumns(cell.column(),1)

    def insertRow(self):

        # Grab the cursor
        cursor = self.ui.textEdit.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Insert a new row at the cell's position
        table.insertRows(cell.row(),1)

    def insertCol(self):

        # Grab the cursor
        cursor = self.ui.textEdit.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Insert a new row at the cell's position
        table.insertColumns(cell.column(),1)

    def toggleFilebar(self):

        state = self.ui.filebar.isVisible()

        # Set the visibility to its inverse
        self.ui.filebar.setVisible(not state)

    def toggleEditbar(self):

        state = self.ui.editbar.isVisible()

        # Set the visibility to its inverse
        self.editbar.ui.setVisible(not state)

    def toggleFormatbar(self):

        state = self.ui.formatbar.isVisible()

        # Set the visibility to its inverse
        self.ui.formatbar.setVisible(not state)

    def toggleFontbar(self):
        state = self.ui.fontbar.isVisible()

        # Set the visibility to its inverse
        self.ui.fontbar.setVisible(not state)

    def toggleMarkupbar(self):

        state = self.ui.markupbar.isVisible()

        # Set the visibility to its inverse
        self.ui.markupbar.setVisible(not state)

    def toggleStatusbar(self):

        state = self.statusbar.isVisible()

        # Set the visibility to its inverse
        self.statusbar.setVisible(not state)

    def new(self):

        spawn = Main()

        spawn.show()

    def importfile(self):
        print("Importing current text")
        if self.txtpath:
            print(self.txtpath)
            self.filename = self.txtpath

            with open(self.filename) as file:
                self.ui.textEdit.setText(file.read())
            
            self.on_font_update()
            #if self.font:
                #self.ui.textEdit.setCurrentFont(qtg.QFont(self.font))
 
    def open(self):

        # Get filename and show only .writer files
        #PYQT5 Returns a tuple in PyQt5, we only need the filename
        self.filename = qtw.QFileDialog.getOpenFileName(self, 'Open File',".","(*.txt *.csv *.writer)")[0]

        if self.filename:
            with open(self.filename,"rt", encoding='UTF-8') as file:
                self.ui.textEdit.setText(file.read())
        self.on_font_update()

    def save(self):

        # Only open dialog if there is no filename yet
        #PYQT5 Returns a tuple in PyQt5, we only need the filename

        if self.txtpath:
            self.filename = self.txtpath
            # Append extension if not there yet
            '''if not self.filename.endswith(".writer"):
              self.filename += ".writer"'''
            # We just store the contents of the text file along with the
            # format in html, which Qt does in a very nice way for us
            '''with open(self.filename,"wt") as file:
                file.write(self.ui.textEdit.toHtml())'''
            with open(self.filename,"w") as file:
                self.changesSaved = True
                print(self.filename + "was overwritten")
        else:
            self.filename = qtw.QFileDialog.getSaveFileName(self, 'Save File')[0]
            self.changesSaved = True
            print(self.txtpath + "was saved as " + self.filename)

    def saveastextDialog(self):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.textEdit.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        #self.ui.TextLE.setText(filename)
        file.close()

    def savetextDialog(self):
        
        #if self.txtdir:
            #defaultdir = self.txtdir
        #else:
            #defaultdir = r"c:/users/max/Projects/Python/EstablishTruth/Greek_txt_pages/"
        
        defaultdir = self.txtdir + r"/" 
        defaultfile = self.filename

        if defaultfile:
            path = defaultdir + defaultfile
            print(path)
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.textEdit.toPlainText()
            file.write(my_CorrectedText)
        
        #self.ui.TextLE.setText(filename)
        file.close()

    def preview(self):

        # Open preview dialog
        preview = QtPrintSupport.QPrintPreviewDialog()

        # If a print is requested, open print dialog
        preview.paintRequested.connect(lambda p: self.ui.textEdit.print_(p))

        preview.exec_()

    def printHandler(self):

        # Open printing dialog
        dialog = QtPrintSupport.QPrintDialog()

        if dialog.exec_() == qtw.QDialog.Accepted:
            self.ui.textEdit.document().print_(dialog.printer())

    def cursorPosition(self):

        cursor = self.ui.textEdit.textCursor()

        # Mortals like 1-indexed things
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()

        self.ui.statusbar.showMessage("Line: {} | Column: {}".format(line,col))

    def wordCount(self):

        wc = wordcount.WordCount(self)

        wc.getText()

        wc.show()

    def insertImage(self):

        # Get image file name
        #PYQT5 Returns a tuple in PyQt5
        filename = qtw.QFileDialog.getOpenFileName(self, 'Insert image',".","Images (*.png *.xpm *.jpg *.bmp *.gif)")[0]

        if filename:
            
            # Create image object
            image = qtg.QImage(filename)

            # Error if unloadable
            if image.isNull():

                popup = qtw.QMessageBox(qtw.QMessageBox.Critical,
                                          "Image load error",
                                          "Could not load image file!",
                                          qtw.QMessageBox.Ok,
                                          self)
                popup.show()

            else:

                cursor = self.ui.textEdit.textCursor()

                cursor.insertImage(image,filename)

    def fontColorChanged(self):

        # Get a color from the text dialog
        color = qtw.QColorDialog.getColor()

        # Set it as the new text color
        self.ui.textEdit.setTextColor(color)

    def highlight(self):

        color = qtw.QColorDialog.getColor()

        self.ui.textEdit.setTextBackgroundColor(color)

    def bold(self):

        if self.ui.textEdit.fontWeight() == qtg.QFont.Bold:

            self.ui.textEdit.setFontWeight(qtg.QFont.Normal)

        else:

            self.ui.textEdit.setFontWeight(qtg.QFont.Bold)

    def italic(self):

        state = self.ui.textEdit.fontItalic()

        self.ui.textEdit.setFontItalic(not state)

    def underline(self):

        state = self.ui.textEdit.fontUnderline()

        self.ui.textEdit.setFontUnderline(not state)

    def strike(self):

        # Grab the text's format
        fmt = self.ui.textEdit.currentCharFormat()

        # Set the fontStrikeOut property to its opposite
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())

        # And set the next char format
        self.ui.textEdit.setCurrentCharFormat(fmt)

    def superScript(self):

        # Grab the current format
        fmt = self.ui.textEdit.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == qtg.QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(qtg.QTextCharFormat.AlignSuperScript)

        else:

            fmt.setVerticalAlignment(qtg.QTextCharFormat.AlignNormal)

        # Set the new format
        self.ui.textEdit.setCurrentCharFormat(fmt)

    def subScript(self):

        # Grab the current format
        fmt = self.ui.textEdit.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == qtg.QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(qtg.QTextCharFormat.AlignSubScript)

        else:

            fmt.setVerticalAlignment(qtg.QTextCharFormat.AlignNormal)

        # Set the new format
        self.ui.textEdit.setCurrentCharFormat(fmt)

    def alignLeft(self):
        self.ui.textEdit.setAlignment(Qt.AlignLeft)

    def alignRight(self):
        self.ui.textEdit.setAlignment(Qt.AlignRight)

    def alignCenter(self):
        self.ui.textEdit.setAlignment(Qt.AlignCenter)

    def alignJustify(self):
        self.ui.textEdit.setAlignment(Qt.AlignJustify)

    def indent(self):

        # Grab the cursor
        cursor = self.ui.textEdit.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's end
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = qtg.QTextCursor.Up if diff > 0 else qtg.QTextCursor.Down

            # Iterate over lines (diff absolute value)
            for n in range(abs(diff) + 1):

                # Move to start of each line
                cursor.movePosition(qtg.QTextCursor.StartOfLine)

                # Insert tabbing
                cursor.insertText("\t")

                # And move back up
                cursor.movePosition(direction)

        # If there is no selection, just insert a tab
        else:

            cursor.insertText("\t")

    def handleDedent(self,cursor):

        cursor.movePosition(qtg.QTextCursor.StartOfLine)

        # Grab the current line
        line = cursor.block().text()

        # If the line starts with a tab character, delete it
        if line.startswith("\t"):

            # Delete next character
            cursor.deleteChar()

        # Otherwise, delete all spaces until a non-space character is met
        else:
            for char in line[:8]:

                if char != " ":
                    break

                cursor.deleteChar()

    def dedent(self):

        cursor = self.ui.textEdit.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's last line
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = qtg.QTextCursor.Up if diff > 0 else qtg.QTextCursor.Down

            # Iterate over lines
            for n in range(abs(diff) + 1):

                self.handleDedent(cursor)

                # Move up
                cursor.movePosition(direction)

        else:
            self.handleDedent(cursor)

    def bulletList(self):

        cursor = self.ui.textEdit.textCursor()

        # Insert bulleted list
        cursor.insertList(qtg.QTextListFormat.ListDisc)

    def numberList(self):

        cursor = self.ui.textEdit.textCursor()

        # Insert list with numbers
        cursor.insertList(qtg.QTextListFormat.ListDecimal)

    def GetLineSpacing(self):

        #self.ui.LHlineEdit.setEnabled(True)
        #self.ui.LHlineEdit.show()
        self.LHlineEdit.setPlaceholderText(str(self.ui.LHslider.value()))
        self.ui.LHslider.setEnabled(True)
        self.ui.LHslider.show()

    def DisableLHSlider(self):
        self.ui.LHslider.hide()
        self.ui.LHslider.setEnabled(False)

    def MoveLHSlider(self):
        self.ui.LHslider.setEnabled(True)
        self.ui.LHslider.setValue(int(self.LHlineEdit.text()))
    
    def SetLineSpacing(self):

        lineSpacing = self.ui.LHslider.value()
        self.LHlineEdit.setText(str(lineSpacing))
            
        cursor = self.ui.textEdit.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.TextCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.TextBlockFormat.ProportionalHeight) 
        cursor.mergeBlockFormat(bf)
    
    def on_font_update(self):
        # update font to selection and size       
        font = qtg.QFont(self.fontBox.currentFont())
        font.setPointSize(self.fontSize.value())
        
        self.ui.textEdit.setFont(font)

def main():
    app = qtw.QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
