import sqlite3
import re

conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/TRiBibleWords.db')
print ("Opened the database successfully")

cursor_TR = conn_TR.cursor()

cursor_TR.execute('''SELECT Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,Strong,RMAC,Lemma FROM Bible
                        WHERE Lemma IS NULL OR Lemma == "" OR Lemma == "None"
                                            ''')

#vlines = cursor_TR.fetchone()
#vlines = cursor_TR.fetchmany(0)
vlines = cursor_TR.fetchall()

#cursor_TR.execute("DELETE FROM Variants")
#conn_TR.commit()

for vline in vlines:
    line = vline[0]
    book = vline[1]
    chapter = vline[2]
    verse = vline[3]
    wordnum = vline[4]
    word = vline[5]
    nodiaWord = vline[6]
    #varword = vline[7]
    strong = vline[7]
    rmac = vline[8]
    lemma = vline[9]
    #varcode = vline[11]

    cursor_TR.execute("SELECT * FROM Variants")
    insert_parameters = """INSERT INTO Variants (Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,Strong,RMAC,Lemma)
                            VALUES (?,?,?,?,?,?,?,?,?,?)"""
    insert_data = (line,book,chapter,verse,wordnum,word,nodiaWord,strong,rmac,lemma)
    
    
    '''insert_parameters = """INSERT OR REPLACE INTO Variants (Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,Strong,RMAC,Lemma)
                            VALUES ((select Line from Variants WHERE Book=? AND Chapter=? AND Verse=?),?,?,?,?,?,?,?,?,?)"""
    insert_data = (book,chapter,verse,book,chapter,verse,wordnum,word,nodiaWord,strong,rmac,lemma)'''

    cursor_TR.execute(insert_parameters,insert_data)
    conn_TR.commit()
    print(line,"\t",book,"\t",chapter,"\t",verse,"\t",wordnum,"\t",word,"\t",nodiaWord,"\t",lemma)
conn_TR.close()