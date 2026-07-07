from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal
import json
from SqliteHelper import *
import time
import UI_Icons
#import Qt5ResolveVariants as resolver

app = QtWidgets.QApplication([])
varui = uic.loadUi("/home/max/Projects/BiblionOCR/ViewController/Application/0-MainUI/QtDesignerUI/VariantsMainForm.ui")

def main():
    print("working")
    loadTableView(0)
    loadVarWordsCombo()
    loadFormView()
    
    varui.VarianceTable.itemSelectionChanged.connect(rowSelectionChanged)
    varui.NextButton.clicked.connect(next)
    varui.PreviousButton.clicked.connect(previous)
    
    varui.PreservedCkBox.stateChanged.connect(VarCodeBuild)
    varui.CorrectedCkBox.stateChanged.connect(VarCodeBuild)
    varui.ErrorCkBox.stateChanged.connect(VarCodeBuild)
    varui.VarianceCkBox.stateChanged.connect(VarCodeBuild)
    varui.ContextCkBox.stateChanged.connect(VarCodeBuild)
    varui.InflectionCkBox.stateChanged.connect(VarCodeBuild)
    varui.ErrorCodeCombo.currentTextChanged.connect(VarCodeBuild)

    varui.VarWordSelCombo.currentTextChanged.connect(selectVarWordsCombo)

    varui.UpdateButton.clicked.connect(updateone)
    #varui.UpdateButton.clicked.connect(startProgressBar)
    varui.UpdateSimButton.clicked.connect(updatesim)
    varui.UpdateBibleButton.clicked.connect(updatebible)
    varui.ResolveButton.clicked.connect(resolved)
    varui.unresRadButton.clicked.connect(loadTableView)
    varui.presRadButton.clicked.connect(loadTableView)
    varui.corrRadButton.clicked.connect(loadTableView)
    varui.allRadButton.clicked.connect(loadTableView)

def loadTableView(rowid):
    helper = SqliteHelper("/home/max/Projects/BiblionOCR/Model/Data/SQLite/FROMVS.db")
    
    varui.VarianceTable.setRowCount(0)
    
    if  varui.presRadButton.isChecked():
        variants = helper.select("SELECT ID,Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,ErrorCode,VarCode,Description,Preserved,Corrected,Error,Variance,Context,Inflection,Resolved FROM Variants WHERE Preserved = '1'")
    elif  varui.corrRadButton.isChecked():
        variants = helper.select("SELECT ID,Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,ErrorCode,VarCode,Description,Preserved,Corrected,Error,Variance,Context,Inflection,Resolved FROM Variants WHERE Corrected = '1'")   
    elif varui.unresRadButton.isChecked():
        variants = helper.select("SELECT ID,Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,ErrorCode,VarCode,Description,Preserved,Corrected,Error,Variance,Context,Inflection,Resolved FROM Variants WHERE Strong IS NULL and VarWord IS NULL Order By Line")
        #variants = helper.select("SELECT ID,Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma FROM Bible WHERE Strong IS NULL")
    else:
        variants = helper.select("SELECT ID,Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,ErrorCode,VarCode,Description,Preserved,Corrected,Error,Variance,Context,Inflection,Resolved FROM Variants")
    
    for row_number,variant in enumerate(variants):
        varui.VarianceTable.insertRow(row_number)
        for column_number,data in enumerate(variant):
            #print(row_number,"\t",column_number,"\t",str(data))
            row = QtWidgets.QTableWidgetItem(str(data))
            #print(cell)
            varui.VarianceTable.setItem(row_number,column_number,row)
            if rowid:
                varui.VarianceTable.selectRow(rowid)
            else:
                varui.VarianceTable.selectRow(0)

def loadVarWordsCombo():
    #helper = SqliteHelper("/home/max/Projects/Python/SQLite/TRBibleWords.db")
    helper = SqliteHelper("/home/max/Projects/BiblionOCR/Model/Data/SQLite/TRiBibleWords.db")
    varwords = helper.select("SELECT DISTINCT NoDiaWord FROM Bible ORDER BY NoDiaWord")
    #print(varwords)

    for varword in varwords:
        varui.VarWordSelCombo.addItem(varword[0])
    
    selectVarWordsCombo()

def selectVarWordsCombo():
    
    selvarword = varui.VarWordSelCombo.currentText()
    #helper = SqliteHelper("/home/max/Projects/Python/SQLite/TRBibleWords.db")
    helper = SqliteHelper("/home/max/Projects/BiblionOCR/Model/Data/SQLite/TRiBibleWords.db")
    varwords = helper.select("SELECT DISTINCT NoDiaWord,Strong,RMAC,Lemma FROM Bible WHERE NoDiaWord =" + "'" + selvarword + "'")
    
    # This is only a partial solution.  It locks onto the first match only.
    
    varfields = varwords[0]

    print(varfields[0])
    
    #varword = varfields[0]
    varui.StrongsLE.setText(varfields[1])
    varui.RMACLE.setText(varfields[2])
    #varui.LemmaLE.setText(varfields[3])
    varui.LemmaLE.setText(varfields[3])
    
def resolved():
    conn_TR = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Data/SQLite/FROMVS.db')
    print ("Opened the database successfully")

    cursor_TR = conn_TR.cursor()

    cursor_TR.execute("DELETE FROM Resolved")
    
    cursor_TR.execute('''SELECT * FROM Variants WHERE VarWord IS NOT NULL AND Strong IS NOT NULL''')

    #vlines = cursor_TR.fetchone()
    #vlines = cursor_TR.fetchmany(0)
    vlines = cursor_TR.fetchall()

    #cursor_TR.execute("DELETE FROM Variants")
    #conn_TR.commit()
    
    for vline in vlines:
        line = vline[1]
        book = vline[2]
        chapter = vline[3]
        verse = vline[4]
        wordnum = vline[5]
        word = vline[6]
        nodiaWord = vline[7]
        varword = vline[8]
        strong = vline[9]
        rmac = vline[10]
        lemma = vline[11]
        varform = vline[12]
        vartype = vline[13]
        impactcode = vline[14]
        errorcode = vline[15]
        varcode = vline[16]
        desc = vline[17]
        preserved = vline[18]
        corrected = vline[19]
        error = vline[20]
        variance = vline[21]
        context = vline[22]
        inflection = vline[23]
        resolved = True

        #cursor_TR.execute("SELECT * FROM Resolved")
        
        insert_parameters = """INSERT OR REPLACE INTO Resolved (Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,
                                Strong,RMAC,Lemma,VarianceForm,VarianceType,ImpactCode,ErrorCode,VarCode,Description,
                                Preserved,Corrected,Error,Variance,Context,Inflection,Resolved)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_data = (line,book,chapter,verse,wordnum,word,nodiaWord,varword,strong,rmac,lemma,varform,vartype,impactcode,errorcode,varcode,desc,preserved,corrected,error,variance,context,inflection,resolved)

        cursor_TR.execute(insert_parameters,insert_data)
        conn_TR.commit()
        print(line,"\t",book,"\t",chapter,"\t",verse,"\t",wordnum,"\t",word,"\t",nodiaWord,"\t",varword,"\t",strong)
    conn_TR.close()

def VarCodeBuild():  
    print("Preserve Toggled)")
    if varui.PreservedCkBox.isChecked():
        f1 = "P"
    else:
        f1 = ""
    
    if varui.CorrectedCkBox.isChecked():
        f2 = "C"
    else:
        f2 = ""

    if varui.ErrorCkBox.isChecked():
        f3 = "E"
    else:
        f3 = ""

    if varui.VarianceCkBox.isChecked():
        f4 = "V"
    else:
        f4 = ""
    
    if varui.ContextCkBox.isChecked():
        f5 = "C"
    else:
        f5 = ""

    if varui.InflectionCkBox.isChecked():
        f6 = "I"
    else:
        f6 = ""
    
    # get the length of string
    length = len(varui.ErrorCodeCombo.currentText())
    # Get last character of string i.e. char at index position len -1
    if varui.ErrorCodeCombo.currentText() == 'None':
        errorcode = ""
    else:
        errorcode = varui.ErrorCodeCombo.currentText()[length -1]
    print('Last character : ', errorcode)
    
    varcode = f1+f2,"-",f3+f4,"-",f5+f6,"-",errorcode
    print(varcode)

    varui.VarianceCodeLE.setText(varcode[0]+varcode[1]+varcode[2]+varcode[3]+varcode[4]+varcode[5]+varcode[6])

def DescBuild():
    pass

def next():
    varui.VarianceTable.selectRow(varui.VarianceTable.currentRow()+1)
    loadFormView()
    
def previous():
    varui.VarianceTable.selectRow(varui.VarianceTable.currentRow()-1)
    loadFormView()
    
def updateone():
    line = varui.LineLE.text()
    word = varui.WordLE.text()
    wordnum = varui.WordNumLE.text()
    varword = varui.VarWordSelCombo.currentText()
    strong = varui.StrongsLE.text()
    rmac = varui.RMACLE.text()
    lemma = varui.LemmaLE.text()
    varcode = varui.VarianceCodeLE.text()
    errorcode = varui.ErrorCodeCombo.currentText()
    desc = varui.DescriptionTextEdit.toPlainText()
    
    if varui.PreservedCkBox.isChecked():
        preserved = 1
        pckvar="P"
    else:
        preserved = 0
        pckvar="" 
    if varui.CorrectedCkBox.isChecked():
        Corrected = 1
        cckvar = "C"
    else:
        Corrected= 0
        cckvar = "" 
    if varui.ErrorCkBox.isChecked():
        error = 1
        eckvar = "E"
    else:
        error = 0
        eckvar = ""
    if varui.VarianceCkBox.isChecked():
        variance = 1
        vckvar = "V"
    else:
        variance = 0 
        vckvar = ""
    if varui.ContextCkBox.isChecked():
        context = 1
        tckvar = "C"
    else:
        context = 0
        tckvar = "" 
    if varui.InflectionCkBox.isChecked():
        inflection = 1
        ickvar = "I"
    else:
        inflection = 0
        ickvar = ""

    varform = pckvar + cckvar
    vartype = eckvar + vckvar
    impactcode = tckvar + ickvar

    if varword or varui.ResolvedCkBox.isChecked:
        resolved = 1
    
    rownum = getSelectedRowId() +1

    helper = SqliteHelper("/home/max/Projects/BiblionOCR/Model/Data/SQLite/FROMVS.db")
    # varwords = helper.select("SELECT * FROM Variants")
    
    print(varword,"\t",strong,"\t",rmac,"\t",lemma,"\t",varcode,"\t",rownum)
    
    query = """UPDATE Variants SET Word = ?, VarWord = ?,Strong = ?,RMAC = ?,Lemma = ?,VarCode = ?, ErrorCode = ?, Description = ?, VarianceForm = ?, VarianceType = ?, ImpactCode = ?, Preserved = ?, Corrected = ?, Error = ?, Variance = ?, Context = ?, Inflection = ?, Resolved = ?
                            WHERE Line = ? and WordNum = ?"""
    data = (word,varword,strong,rmac,lemma,varcode,errorcode,desc,varform,vartype,impactcode,preserved,Corrected,error,variance,context,inflection,resolved,line,wordnum)
    #startProgressBar()
    helper.update(query,data)
    rowid = varui.VarianceTable.currentRow()
    loadTableView(rowid)
    loadFormView()

def updatesim():
    varword = varui.VarWordSelCombo.currentText()
    nodiaword = varui.NoDiaWordLE.text()
    strong = varui.StrongsLE.text()
    rmac = varui.RMACLE.text()
    lemma = varui.LemmaLE.text()
    varcode = varui.VarianceCodeLE.text()
    errorcode = varui.ErrorCodeCombo.currentText()
    desc = varui.DescriptionTextEdit.toPlainText()
    
    if varui.PreservedCkBox.isChecked():
        preserved = 1
        pckvar="P"
    else:
        preserved = 0
        pckvar="" 
    if varui.CorrectedCkBox.isChecked():
        Corrected = 1
        cckvar = "C"
    else:
        Corrected= 0
        cckvar = "" 
    if varui.ErrorCkBox.isChecked():
        error = 1
        eckvar = "E"
    else:
        error = 0
        eckvar = ""
    if varui.VarianceCkBox.isChecked():
        variance = 1
        vckvar = "V"
    else:
        variance = 0 
        vckvar = ""
    if varui.ContextCkBox.isChecked():
        context = 1
        tckvar = "C"
    else:
        context = 0
        tckvar = "" 
    if varui.InflectionCkBox.isChecked():
        inflection = 1
        ickvar = "I"
    else:
        inflection = 0
        ickvar = ""

    varform = pckvar + cckvar
    vartype = eckvar + vckvar
    impactcode = tckvar + ickvar

    if varword or varui.ResolvedCkBox.isChecked:
        resolved = 1
    
    rownum = getSelectedRowId() +1

    helper = SqliteHelper("/home/max/Projects/BiblionOCR/Model/Data/SQLite/FROMVS.db")
    # varwords = helper.select("SELECT * FROM Variants")
    
    print(varword,"\t",strong,"\t",rmac,"\t",lemma,"\t",varcode,"\t",rownum)
    
    query = """UPDATE Variants SET VarWord = ?,Strong = ?,RMAC = ?,Lemma = ?,VarCode = ?, ErrorCode = ?, Description = ?, VarianceForm = ?, VarianceType = ?, ImpactCode = ?, Preserved = ?, Corrected = ?, Error = ?, Variance = ?, Context = ?, Inflection = ?, Resolved = ?
                            WHERE NoDiaWord = ?"""
    data = (varword,strong,rmac,lemma,varcode,errorcode,desc,varform,vartype,impactcode,preserved,Corrected,error,variance,context,inflection,resolved,nodiaword)
    helper.update(query,data)
    rowid = varui.VarianceTable.currentRow()
    loadTableView(rowid)
    loadFormView()

def updatebible():
    updateone()
    helper = SqliteHelper("/home/max/Projects/BiblionOCR/Model/Data/SQLite/FROMVS.db")
    #helper = SqliteHelper("/home/max/Projects/Python/SQLite/TRiBibleWords.db")
   
    query = '''SELECT Line,WordNum,NoDiaWord,VarWord,Strong,RMAC,Lemma,VarCode FROM Variants WHERE Preserved = "1"'''
    variants = helper.select(query)
    
    
    
    for variant in variants:
        if variant[2]:    
            
            line = variant[0]
            wordnum = variant[1]
            nodiaword = variant[2]
            varword = variant[3]
            strong = variant[4]
            rmac = variant[5]
            lemma = variant[6]
            varcode = variant[7]
       

            '''englishquery = "SELECT English FROM IntBibleWords WHERE Line = ? AND NoDiaWord = ?"
            engdata = (line,varword)
            english = helper.selectone(englishquery,engdata)
            if englishtup:
                #try:
                
                for val in englishtup:
                    if len(val)>0:
                        english = val
                #except:
                else:
                    english = ""
                
            english = ''.join(englishtup)

            if str(english) == "None":'''
            english = ""
            
            print(line,"\t",varword,"\t",strong,"\t",rmac,"\t",lemma,"\t",english,"\t",varcode)
            
            query = """UPDATE Bible SET VarWord = ?,Strong = ?,RMAC = ?,Lemma = ?,English = ?,VarCode = ?  WHERE Line = ? and NoDiaWord = ? and Strong IS NULL"""
            data = (varword,strong,rmac,lemma,english,varcode,line,nodiaword)
            helper.update(query,data)

    #loadTableView()
    #loadFormView()

def loadFormView():
    #loadVarWordsCombo()  
    varui.LineLE.setText(varui.VarianceTable.item(getSelectedRowId(),1).text())
    varui.BookLE.setText(varui.VarianceTable.item(getSelectedRowId(),2).text())
    varui.ChapterLE.setText(varui.VarianceTable.item(getSelectedRowId(),3).text())
    varui.VerseLE.setText(varui.VarianceTable.item(getSelectedRowId(),4).text())
    varui.WordNumLE.setText(varui.VarianceTable.item(getSelectedRowId(),5).text())
    varui.WordLE.setText(varui.VarianceTable.item(getSelectedRowId(),6).text())
    varui.NoDiaWordLE.setText(varui.VarianceTable.item(getSelectedRowId(),7).text())
    if varui.VarianceTable.item(getSelectedRowId(),8).text() != "None":
        varui.VarWordSelCombo.setCurrentText(varui.VarianceTable.item(getSelectedRowId(),8).text())
    else:
        varui.VarWordSelCombo.setCurrentText(varui.VarianceTable.item(getSelectedRowId(),7).text()[0:3])
    #varui.VarWordSelCombo.setCurrentText(varui.VarianceTable.item(getSelectedRowId(),8).text())
    #varui.VarWordSelCombo.setCompletionPrefix(varui.NoDiaWordLE.currentText()[0:2])
    #setCompletionPrefix(const QString &prefix)
    varui.StrongsLE.setText(varui.VarianceTable.item(getSelectedRowId(),9).text())
    varui.RMACLE.setText(varui.VarianceTable.item(getSelectedRowId(),10).text())
    varui.LemmaLE.setText(varui.VarianceTable.item(getSelectedRowId(),11).text())
    varui.ErrorCodeCombo.setCurrentText(varui.VarianceTable.item(getSelectedRowId(),12).text())
    varui.VarianceCodeLE.setText(varui.VarianceTable.item(getSelectedRowId(),13).text())
    varui.DescriptionTextEdit.setPlainText(varui.VarianceTable.item(getSelectedRowId(),14).text()) 

    if varui.VarianceTable.item(getSelectedRowId(),15).text() == "1" or varui.VarianceTable.item(getSelectedRowId(),13).text()[0] == "P":
        varui.PreservedCkBox.setChecked(True)
    else:
        varui.PreservedCkBox.setChecked(False)
    if varui.VarianceTable.item(getSelectedRowId(),16).text() == "1" or varui.VarianceTable.item(getSelectedRowId(),13).text()[0] == "C" or varui.VarianceTable.item(getSelectedRowId(),13).text()[1] == "C":
        varui.CorrectedCkBox.setChecked(True)
    else:
        varui.CorrectedCkBox.setChecked(False)
    if varui.VarianceTable.item(getSelectedRowId(),17).text() == "1" or varui.VarianceTable.item(getSelectedRowId(),13).text()[1] == "E" or varui.VarianceTable.item(getSelectedRowId(),13).text()[2] == "E" or varui.VarianceTable.item(getSelectedRowId(),13).text()[3] == "E":
        varui.ErrorCkBox.setChecked(True)
    else:
        varui.ErrorCkBox.setChecked(False)
    if varui.VarianceTable.item(getSelectedRowId(),18).text() == "1" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-2] == "V" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-3] == "V" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-4] == "V":
        varui.VarianceCkBox.setChecked(True)
    else:
        varui.VarianceCkBox.setChecked(False)
    if varui.VarianceTable.item(getSelectedRowId(),19).text() == "1" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-2] == "C" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-3] == "C" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-4] == "C":
        varui.ContextCkBox.setChecked(True)
    else:
        varui.ContextCkBox.setChecked(False)
    if varui.VarianceTable.item(getSelectedRowId(),20).text() == "1" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-2] == "I" or varui.VarianceTable.item(getSelectedRowId(),13).text()[-3] == "I":
        varui.InflectionCkBox.setChecked(True)
    else:
        varui.InflectionCkBox.setChecked(False)
    if varui.VarianceTable.item(getSelectedRowId(),21).text() == "1":
        varui.ResolvedCkBox.setChecked(True)
    else:
        varui.ResolvedCkBox.setChecked(False)
    
def rowSelectionChanged():
    loadFormView()
    #print(getSelectedBook())

def getSelectedRowId():
    #return varui.VarianceTable.selectedItems()
    return varui.VarianceTable.currentRow()

def getSelectedBook():
    return varui.VarianceTable.item(getSelectedRowId(),2).text()
      
'''class MyThread(QThread):
    change_value = pyqtSignal(int)

    def run():
        cnt = 0
        while cnt < 100:
            cnt+=1

            time.sleep(0.3)
            change_value.emit(cnt)'''

'''def startProgressBar():
    thread = MyThread()
    thread.change_value.connect(setProgressVal)
    thread.start()

def setProgressVal(val):
    progressbar.setValue(val)'''

if __name__ == "__main__":
    main()


varui.show()
app.exec()