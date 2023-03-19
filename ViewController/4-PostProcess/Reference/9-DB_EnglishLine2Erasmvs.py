import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
#cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma FROM Bible")
cursor_TW.execute("SELECT ID, Line, WordNum, Word, NormWord, NoDiaWord, VarWord, Strong, RMAC, English FROM Bible")
wlines = cursor_TW.fetchall()

'''conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBibleWords.db')
print ("Opened Textus Receptus database successfully")
cursor_TR = conn_TR.cursor()'''
        
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
        
        #flemma = wline[7]
        fenglish = wline[9]
        #print(flinenum)
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRSBible WHERE Line=?", (flinenum,))
        
        cursor_TW.execute("SELECT DISTINCT ID,NormWord,NoDiaWord,English FROM IntBibleWords WHERE Line=?", (flinenum,))
        twordloop = cursor_TW.fetchall()
        #print(twordloop)              
        
        for tword in twordloop:
                
                # assign TRa field variables
                #tline = tword[1]
                #twordnum = tword[2]
                tnormword = tword[1]
                tnodiaword = tword[2]
                #tnodialemma = tword[5]
                #tstrong = tword[5]
                #trmac = tword[6]
                #tlemma = tword[8]
                tenglish = tword[3]


                # search each word-line(wline) to find matches to current cfind value
                
                #repstrong = nodialemma.replace(cfind, creplace)
                #lcword = repword.lower()
                if not fenglish and fvarword == tnormword or fnormword == tnormword:
                #if not fenglish and fnormword == tnormword:
                #if fnodiaword == tnodiaword and fstrong != tstrong:
                #if fnodiaword == tnodiaword and frmac != trmac:
                        # monitor data output
                        #print(flinenum, " ", fwordnum," ", fnodiaword," ", fstrong," ", frmac," ", fenglish," ", tline," ", twordnum," ", tnodiaword," ", tstrong," ", trmac," ", tenglish)
                        print(flinenum, " ", fwordnum," ", fnodiaword," ", fvarword," ", fstrong," ", frmac," ", fenglish," ", tnodiaword," ", tenglish)
                        # check for multiple matches
                        
                        # update database
                        sql_qry = "UPDATE Bible SET English = ? WHERE ID = ?"
                        data = (tenglish, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()    
conn_TW.close()                          
