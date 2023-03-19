import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT DISTINCT NoDiaWord, Strong, RMAC, Lemma FROM Variants")
wlines = cursor_TW.fetchall()


        
for wline in wlines:
        
        # assign FROMVS field variables
        nodiaword = wline[0]
        strong = wline[1]
        rmac = wline[2]
        lemma = wline[3]
        
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        
        cursor_TW.execute("SELECT NoDiaWord, Strong, RMAC, Lemma FROM TRaStrongDistinct WHERE NoDiaWord=?", (nodiaword,))
        tlist = cursor_TW.fetchone()
        # print(tlist)              
        
        if tlist:
                tnodiaword = tlist[0]
                tstrong = tlist[1]
                trmac = tlist[2]
                tlemma = tlist[3]
                varword = tnodiaword
                resolved = True

                # monitor data output
                print(nodiaword,"\t", tstrong,"\t", trmac,"\t", tlemma)
                
                if not strong:
                        # update database
                        sql_qry = "UPDATE Variants SET VarWord = ?, Strong = ?, RMAC = ?, Lemma = ?, Resolved = ? WHERE NoDiaWord = ?"
                        data = (varword, tstrong, trmac, tlemma, resolved, tnodiaword)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
        
conn_TW.close()                          
