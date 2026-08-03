import csv
import sqlite3
import re


conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, Line, WordNum, Word, NormWord, NoDiaWord, VarWord, Strong, RMAC, English FROM Bible")
wlines = cursor_TW.fetchall()
       
for wline in wlines:
               
        # assign FROMVS field variables
        id = wline[0]
        flinenum = wline[1]
        fwordnum = wline[2]
        fnormword = wline[4] 
        fnodiaword = wline[5]
        fvarword = wline[6]
        fstrong = wline[7]
        frmac = wline[8]
        fenglish = wline[9]
        #print(flinenum)
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRSBible WHERE Line=?", (flinenum,))
        
        cursor_TW.execute("SELECT DISTINCT ID,NormWord,NoDiaWord,English FROM IntBibleWords WHERE Line=?", (flinenum,))
        englishquery = "SELECT ID,NormWord,NoDiaWord,English FROM IntBibleWords WHERE Line = ? AND NoDiaWord = ? AND English NOTNULL"
        engdata = (flinenum,fvarword)
        cursor_TW.execute(englishquery,engdata)
        
        twordloop = cursor_TW.fetchall()
        #print(twordloop)              
        
        for tword in twordloop:
                
                # assign TRa field variables
                tnormword = tword[1]
                tnodiaword = tword[2]
                tenglish = tword[3]
                
                if str(tenglish) == "None":
                    tenglish = ""

                #if not fenglish and fvarword == tnodiaword:
                if fvarword == tnodiaword:
                #if not fenglish and fvarword == tnodiaword:
                    print(flinenum, " ", fwordnum," ", fnodiaword," ", fvarword," ", fstrong," ", frmac," ", fenglish," ", tnodiaword," ", tenglish)
                    
                    # update database
                    sql_qry = "UPDATE Bible SET English = ? WHERE ID = ?"
                    data = (tenglish, id)
                    cursor_TW.execute(sql_qry, data)
                    conn_TW.commit()   
conn_TW.close() 