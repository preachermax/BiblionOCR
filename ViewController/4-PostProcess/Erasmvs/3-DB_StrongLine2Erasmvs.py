import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
#cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma, English FROM Bible WHERE Line>1071")
cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma, English FROM Bible")

wlines = cursor_TW.fetchall()

        
for wline in wlines:
        
        
        # assign FROMVS field variables
        id = wline[0]
        flinenum = wline[1]
        fwordnum = wline[2]
        fnodiaword = wline[4]
        fstrong = wline[5]
        frmac = wline[6]
        flemma = wline[7]
        fenglish = wline[8]
        #print(flinenum)
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRSBible WHERE Line=?", (flinenum,))
        
        cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma, English FROM IntBibleWords WHERE Line=?", (flinenum,))
        twordloop = cursor_TW.fetchall()
        #print(twordloop)              
        
        for tword in twordloop:
                
                # assign TRa field variables
                tline = tword[1]
                twordnum = tword[2]
                tnodiaword = tword[4]
                #tnodialemma = tword[5]
                tstrong = tword[5]
                trmac = tword[6]
                tlemma = tword[7]
                tenglish = tword[8]

                # search each word-line(wline) to find matches to current cfind value
                
                #repstrong = nodialemma.replace(cfind, creplace)
                #lcword = repword.lower()

                if fnodiaword == tnodiaword:
                #if fnodiaword == tnodiaword and fstrong != tstrong:
                #if fnodiaword == tnodiaword and frmac != trmac:
                        # monitor data output
                        print(flinenum, " ", fwordnum," ", fnodiaword," ", fstrong," ", frmac," ", flemma," ", fenglish," ", tline," ", twordnum," ", tnodiaword," ", tstrong," ", trmac," ", tlemma," ", tenglish)
                        
                        # check for multiple matches
                        
                        # update database
                        sql_qry = "UPDATE Bible SET Strong = ?, RMAC = ?,Lemma = ?, English = ? WHERE ID = ?"
                        data = (tstrong, trmac, tlemma, tenglish, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                        fstrong = tstrong        
conn_TW.close()                          
