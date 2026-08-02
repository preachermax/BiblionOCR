import sqlite3
import re

conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
print ("Opened the database successfully")

cursor_TR = conn_TR.cursor()

cursor_TR.execute('''SELECT Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,VarCode FROM Bible
                        WHERE VarWord IS NULL AND Strong IS NULL OR VarWord == "" AND Strong == ""
                                            ''')

#vlines = cursor_TR.fetchone()
#vlines = cursor_TR.fetchmany(0)
vlines = cursor_TR.fetchall()

#cursor_TR.execute("DELETE FROM Variants")
conn_TR.commit()

for vline in vlines:
    line = vline[0]
    book = vline[1]
    chapter = vline[2]
    verse = vline[3]
    wordnum = vline[4]
    word = vline[5]
    nodiaWord = vline[6]
    varword = vline[7]
    strong = vline[8]
    rmac = vline[9]
    lemma = vline[10]
    varcode = vline[11]

    cursor_TR.execute("SELECT * FROM Variants")
    insert_parameters = """INSERT INTO Variants (Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,VarCode)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
    insert_data = (line,book,chapter,verse,wordnum,word,nodiaWord,varword,strong,rmac,lemma,varcode)
    
    
    '''insert_parameters = """INSERT OR REPLACE INTO Variants (Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,VarCode)
                            VALUES ((select Line from Variants WHERE Book=? AND Chapter=? AND Verse=?),?,?,?,?,?,?,?,?,?,?,?)"""
    insert_data = (book,chapter,verse,book,chapter,verse,wordnum,word,nodiaWord,varword,strong,rmac,lemma,varcode)'''

    cursor_TR.execute(insert_parameters,insert_data)
    conn_TR.commit()
    print(line,"\t",book,"\t",chapter,"\t",verse,"\t",wordnum,"\t",word,"\t",nodiaWord,"\t",varword,"\t",strong)
conn_TR.close()