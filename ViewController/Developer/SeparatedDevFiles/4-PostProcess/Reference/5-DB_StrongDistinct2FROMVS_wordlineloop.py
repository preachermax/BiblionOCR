import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma FROM Bible")
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

        #lcword = normword.lower()
        
        cursor_TW.execute("SELECT DISTINCT Strong, RMAC, NoDiaWord, NoDiaLemma, Lemma FROM TRaBible WHERE Line=?", (flinenum,))
        twordloop = cursor_TW.fetchall()
        print(twordloop)              
        for tword in twordloop:
                
                # assign TRa field variables
                tstrong = tword[0]
                trmac = tword[1]
                tnodiaword = tword[2]
                tnodialemma = tword[3]
                tlemma = tword[4]


                # search each word-line(wline) to find matches to current cfind value
                
                #repstrong = nodialemma.replace(cfind, creplace)
                #lcword = repword.lower()

                if fnodiaword == tnodiaword and fstrong != tstrong:
                        # monitor data output
                        print(tnodiaword," ", tnodialemma," ", trmac," ", tlemma," ", tstrong, " ", fstrong," ", fnodiaword)
                        
                        # update database
                        sql_qry = '''UPDATE Bible SET Strong = ?, RMAC = ?, Lemma = ? WHERE ID = ?'''
                        data = (tstrong, trmac, tlemma, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                
                fstrong = tstrong
        
conn_TW.close()                          
