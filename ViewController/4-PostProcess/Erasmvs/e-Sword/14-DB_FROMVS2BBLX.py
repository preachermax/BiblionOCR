import csv
import sqlite3
import re

#txtfile = open('/home/max/Projects/Python/Esword/ERASMS1516-MatInt.rtf', 'w')

# Connect to erasmus.bblx
conn_BB = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Text/Esword/Erasmvs1516.bblx')
print ("Opened The ESword database successfully")
cursor_BB = conn_BB.cursor()
cursor_BB.execute("DELETE FROM Bible")
conn_BB.commit()
print ("Deleted all of the ESword records successfully")

# Connect to FROMVS.db
conn_FR = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened The FROMVS database successfully")
cursor_FR = conn_FR.cursor()

cursor_FR.execute("SELECT Line FROM Bible WHERE ID = (SELECT MAX(ID) FROM Bible)")
numlines = cursor_FR.fetchone()
lastline = numlines[0]
loopcount = 1

while loopcount <= lastline:   
    cursor_FR.execute("SELECT Line,BookNum,Book,Chapter,Verse,Word,UnicodeWord,WordPunc FROM Bible WHERE Line = " + str(loopcount))
    vwords = cursor_FR.fetchall()
    lineverse = ""

    for vword in vwords:

        linenum = vword[0]
        booknum = vword[1]
        book = vword[2]
        chpt = vword[3]
        vrse = vword[4]
        word = vword[5]
        uniword = vword[6]
        punc = vword[7]
        
        # print(str(linenum) + " " + str(book) + " " + str(chpt) + ":" + str(vrse) + " " + str(word) + str(punc) + " " + str(strong) + " " + str(RMAC) + " " + str(english) + str(engpunc))
        linegroup = str(book) + " " + str(chpt) + ":" + str(vrse) + " "
        # wordgroup = str(uniword) + str(punc) + " " + str(engopen) + str(english) + str(engpunc) + str(engclose) + " " + str(strongopen) + str(strong) + str(strongclose) + " " + str(RMACopen) + str(RMAC) + str(RMACclose)
        wordgroup = str(uniword) + str(punc)
        lineverse = lineverse + wordgroup + " "
        lineverse = lineverse.replace('None','')
    #txtfile.write(linegroup + lineverse + "\n")
    loopcount += 1
    script = lineverse
    print(linegroup + lineverse)

    sql_qry = '''INSERT INTO Bible (Book,Chapter,Verse,Scripture) VALUES (?,?,?,?)'''
    data = (booknum, chpt, vrse, script)
    cursor_BB.execute(sql_qry, data)
    conn_BB.commit()

conn_FR.close()
conn_BB.close()
