import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma FROM Bible")
wlines = cursor_TW.fetchall()


        
for wline in wlines:
        
        
        # assign FROMVS field variables
        id = wline[0]
        flinenum = wline[1]
        fwordnum = wline[2]
        fword = wline[3]
        fnodiaword = wline[4]
        fstrong = wline[5]
        frmac = wline[6]
        flemma = wline[7]

        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        
        cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM IntBibleWords WHERE Line=?", (flinenum,))

        twordloop = cursor_TW.fetchall()
        # print(twordloop)              
        
        for tword in twordloop:
                
                # assign TRa field variables
                tline = tword[1]
                twordnum = tword[2]
                twword = tword[3]
                tnodiaword = tword[4]
                tnodialemma = tword[5]
                tstrong = tword[6]
                trmac = tword[7]
                tlemma = tword[8]


                # search each word-line(wline) to find matches to current cfind value
                
                #repstrong = nodialemma.replace(cfind, creplace)
                #lcword = repword.lower()

                if fword == twword or fnodiaword == tnodiaword or fnodiaword[:-1] == tnodiaword:
                #if fnodiaword == tnodiaword and fstrong != tstrong:
                #if fnodiaword == tnodiaword and frmac != trmac:
                        # monitor data output
                        print(flinenum, " ", fwordnum," ", fnodiaword," ", fstrong," ", frmac," ", flemma," ", tline," ", twordnum," ", tnodiaword," ", tnodialemma," ", tstrong," ", trmac," ", tlemma)
                        
                        # check for multiple matches
                        
                        # update database
                        sql_qry = '''UPDATE Bible SET Lemma = ?, NoDiaLemma = ? WHERE ID = ?'''
                        data = (tlemma, tnodialemma, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                        fstrong = tstrong
        
conn_TW.close()                          
