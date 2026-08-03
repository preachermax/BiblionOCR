import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
#cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, Lemma FROM Bible")
cursor_TW.execute("Select f.ID, f.Line, f.Book, f.Chapter, f.Verse, i.WordNum,f.WordNum, i.Word,f.Word, i.NoDiaWord,f.NoDiaWord, i.Strong,f.Strong, i.RMAC,f.RMAC, i.Lemma, f.Lemma, i.English, f.English from Bible as f Left Join IntBibleWords as i on f.Line == i.Line and f.NoDiaWord == i. NoDiaWord")

#cursor_TW.execute("SELECT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, English FROM Bible")
wlines = cursor_TW.fetchall()

        
for wline in wlines:
        
        
        # assign FROMVS field variables
        id = wline[0]
        flinenum = wline[1]
        fwordnum = wline[6]
        inodiaword = wline[9]
        fnodiaword = wline[10]
        istrong = wline[11]
        fstrong = wline[12]
        irmac = wline[13]
        frmac = wline[14]
        ilemma = wline[15]
        flemma = wline[16]
        ienglish = wline[17]
        fenglish = wline[18]
        #print(flinenum)
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRSBible WHERE Line=?", (flinenum,))
        
        '''cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, Strong, RMAC, English FROM IntBibleWords WHERE Line=?", (flinenum,))
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
                #tlemma = tword[8]
                tenglish = tword[7]


                # search each word-line(wline) to find matches to current cfind value
                
                #repstrong = nodialemma.replace(cfind, creplace)
                #lcword = repword.lower()

                if fnodiaword == tnodiaword:
                #if fnodiaword == tnodiaword and fstrong != tstrong:
                #if fnodiaword == tnodiaword and frmac != trmac:
                        # monitor data output
                        print(flinenum, " ", fwordnum," ", fnodiaword," ", fstrong," ", frmac," ", fenglish," ", tline," ", twordnum," ", tnodiaword," ", tstrong," ", trmac," ", tenglish)
                        
                        # check for multiple matches
                        
                        # update database
                        sql_qry = "UPDATE Bible SET Strong = ?, RMAC = ?, English = ? WHERE ID = ?"
                        data = (tstrong, trmac, tenglish, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                        fstrong = tstrong'''
        
        print(id," ", flinenum, " ", fwordnum," ", fnodiaword," ", fstrong," ", frmac," ", flemma," ", ilemma," ", fenglish," ",inodiaword," ", istrong," ", irmac," ", ienglish)

                        
        # update database
        sql_qry = "UPDATE Bible SET Strong = ?, RMAC = ?,Lemma = ?, English = ? WHERE ID = ?"
        data = (istrong, irmac, ilemma, ienglish, id)
        cursor_TW.execute(sql_qry, data)
        conn_TW.commit()       
conn_TW.close()                          
