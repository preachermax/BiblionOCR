# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/QtDesignerUI/chrRefDialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!
# Python imports
import csv
import json
import os
import re
from pathlib import Path
import fontTools
from fontTools.ttLib import ttFont
from ast import literal_eval

# import glob
import shutil
import sys
import time
# import pyautogui
# from tempfile import NamedTemporaryFile
import pandas as pd
import json
import platform

# from ImageQt import ImageQt
import cv2
import numpy as np
import pytesseract
import qimage2ndarray
import tiffcapture
# from subprocess import Popen, PIPE, CalledProcessError

from PIL import Image, ImageDraw, ImageFont, ImageQt

# PyQt5 imports
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
from PyQt5.QtWidgets import QSpinBox, QRubberBand, QWidget, QHBoxLayout, QSizeGrip, QMenu, QFrame, QProgressBar
from PyQt5.QtCore import QPoint, QRect, QSize, Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush
from ChrReferenceDialog import Ui_CharRef


class CharacterReference(qtw.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_CharRef()
        self.ui.setupUi(self)
        self.ucoderange = []
        self.fontpath = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS.ttf'
        self.xmlpath = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS.xml'
        fontxml = ttFont.TTFont(self.fontpath)
        # fontxml.saveXML(self.xmlpath)
        print(f'FROMVS.xml => {fontxml}')
        # Set json key values
        self.initUCodeRangeCombo()
        self.ui.uCodeRangeComboBox.currentTextChanged.connect(self.on_combo_select)
        self.ui.uCodeStartRangeComboBox.currentTextChanged.connect(self.on_range_select)
        self.ui.uCodeEndRangeComboBox.currentTextChanged.connect(self.on_range_select)
        self.ui.chrTableWidget.selectionModel().selectionChanged.connect(self.on_item_select)
        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)
        self.ui.chrSelectedFontSize.valueChanged.connect(self.on_chrfont_update)
        #self.ui.OCRlangComboBox.currentTextChanged.connect(self.on_language_select)
    
    #def on_language_select(self):
    


    def initUCodeRangeCombo(self):
        # Opening JSON file
        with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/ProjectUnicodeRanges.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
            # Iterating through the json
            for category in data:
                #print(category['category'])
                #lang = self.ui.OCRlangComboBox.currentText()
                self.ui.uCodeRangeComboBox.addItem(category['category'])

        # Closing file
        f.close()
        self.on_combo_select()

    def on_combo_select(self):
        self.ucoderange = self.ui.uCodeRangeComboBox.currentText()
        # self.ui.uCodeRangeComboBox.setEditText(self.ucoderange)
        # Reopening JSON file
        with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/ProjectUnicodeRanges.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

            # Iterating through the json
            # list
            for category in data:
                #print(category['category'])
                if category['category'] == self.ucoderange:
                    decrange = category['range'].split(",")
                    hexrange = category['hexrange'].split(",")
                    print(f'Hex Range from json: {hexrange} Range: {decrange}')
                    self.hs = hexrange[0].replace('[','')
                    self.he = hexrange[1].replace(']','')
                    self.ds = decrange[0].replace('[','')
                    self.de = decrange[1].replace(']','')
                    print(
                        f'Hex Range Start: {self.hs} End: {self.he}, Dec Range Start: {self.ds} End: {self.de}')
                    start = int(self.ds)
                    end = int(self.de)
                    # Initialize start and end comboboxes
                    # self.rowcount = 0
                    self.ui.uCodeStartRangeComboBox.clear()
                    self.ui.uCodeEndRangeComboBox.clear()
                    for startcode in range(start, end+1):
                        endcode = end
                        if self.ui.hexRadioButton.isChecked():
                            if startcode % 16 == 0:
                                rowendcode = hex(int(startcode) + 15)
                                rowstartcode = hex(int(startcode))
                                startcode = hex(int(startcode))
                                endcode = hex(int(endcode))
                                self.ui.uCodeStartRangeComboBox.addItem(rowstartcode)
                                self.ui.uCodeEndRangeComboBox.addItem(rowendcode)
                                # self.rowcount += 1
                        else:
                            if startcode % 10 == 0:
                                rowendcode =  int(startcode) + 9
                                rowstartcode = int(startcode)
                                startcode = int(startcode)
                                endcode = int(endcode)
                                self.ui.uCodeStartRangeComboBox.addItem(str(rowstartcode))
                                self.ui.uCodeEndRangeComboBox.addItem(str(rowendcode))
                                # self.rowcount += 1
                    endcount = self.ui.uCodeStartRangeComboBox.count()-1
                    self.ui.uCodeStartRangeComboBox.setCurrentIndex(0)
                    self.ui.uCodeEndRangeComboBox.setCurrentIndex(endcount)
                    starttext = self.ui.uCodeStartRangeComboBox.currentText()
                    endtext = self.ui.uCodeEndRangeComboBox.currentText()
                    self.showChrRefTable(start, end)

        # Closing file
        f.close()

    def on_range_select(self):
        start = self.ui.uCodeStartRangeComboBox.currentText()
        end = self.ui.uCodeEndRangeComboBox.currentText()
        print(f'start type: {type(start)} end type: {type(end)}')
        start = literal_eval(start)
        end = literal_eval(end)

        self.showChrRefTable(start, end)

    def showChrRefTable(self, start, end):
        self.ui.chrTableWidget.clear()
        self.ui.chrTableWidget.horizontalHeader().hide()
        self.ui.chrTableWidget.verticalHeader().hide()
        print(f'Show Character Reference Table from: {str(start)} to: {str(end)} ')
        delta = end - start
        if self.ui.hexRadioButton.isChecked():
            rowcount = int(delta/16) + 1
        else:
            rowcount = int(delta/10) + 1 
        #rowcount = self.ui.uCodeStartRangeComboBox.count()
        self.ui.chrTableWidget.setRowCount(rowcount)
        chartext = ''
        if self.ui.hexRadioButton.isChecked():
            colcount = 17
        else:
            colcount = 11
        self.ui.chrTableWidget.setColumnCount(colcount)
        for row in range(rowcount):
            print(f'Current Row: {row}')
            for column in range(0,colcount):
                print(f'Current Column: {column}')
                if column == 0:
                    #start += 1
                    if self.ui.hexRadioButton.isChecked():
                        chartext = hex(start)
                    else:
                        chartext = str(start)
                    print(f'Start Column Code: {chartext}')
                else:
                    ucode = start + column - 1
                    print(f'UCode: {ucode} Text: {chr(ucode)}')
                    chartext = chr(ucode)
                # set font and fontsize for chartext in table widget
                charItem = qtw.QTableWidgetItem(chartext)
                self.ui.chrTableWidget.setItem(row,column,charItem)
            if self.ui.hexRadioButton.isChecked():
                start += 16
            else:
                start += 10
        self.ui.chrTableWidget.resizeColumnsToContents()
        self.ui.chrTableWidget.resizeRowsToContents()

    def get_glyphname(self, glyphcode):
        print(f'Glyph Code: {glyphcode}')
        glyphname = ""
        with open('/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS_cmap.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
            # Iterating through the json
            # list
            for code in data:
                #print(category['category'])
                if code["code"] == str(glyphcode):
                    print("JSON code:" + code["code"])
                    print("JSON name:" + code["name"])
                    glyphname = code["name"]
                    print(f'Glyph Name: {glyphname}')
                    self.ui.GlyphNameLE.setText(glyphname)
                
                # Is the loop running twice? This breaks the code:
                #elif code["code"] != str(glyphcode):
                    #self.ui.GlyphNameLE.clear()
                    

    def on_item_select(self):
        #print('Item selected ...')
        chrselected = self.ui.chrTableWidget.currentItem().text()
        self.ui.chrSelected.setText(chrselected)
        hex_chrselected = hex(ord(chrselected))
        if self.ui.hexRadioButton.isChecked():
            chrselected = hex(ord(chrselected))
        else:
            chrselected = str(ord(chrselected))
        self.ui.uCodeSelectedLE.setText(chrselected)
        self.ui.chrString.insert(self.ui.chrTableWidget.currentItem().text() + " ")
        self.on_chrfont_update()
        self.get_glyphname(hex_chrselected)

    def on_chrfont_update(self):
        # update font to selection and size       
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.chrSelectedFontSize.value())
        self.ui.chrSelected.setFont(font)
    
    def on_font_update(self):
        # update font to selection and size       
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        self.ui.chrString.setFont(font)
        self.ui.chrTableWidget.setFont(font)
        self.ui.chrTableWidget.resizeColumnsToContents()
        self.ui.chrTableWidget.resizeRowsToContents()

# Only run this code if I am actually running this script
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = CharacterReference()
    w.show()
    app.exec()
