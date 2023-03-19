import sqlite3
import re

txtfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/Esword/ERASMS1516+Int.txt', 'w')

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened The FROMVS database successfully")

cursor_TW = conn_TW.cursor()

cursor_TW.execute("SELECT Line FROM Bible WHERE ID = (SELECT MAX(ID) FROM Bible)")
lines = cursor_TW.fetchone()
lastline = lines[0]
#print(lastline)
loopcount = 1

while loopcount <= lastline:
    cursor_TW.execute("SELECT Line,Book,Chapter,Verse,Word,Strong,RMAC,English,WordPunc,EnglishPunc FROM Bible WHERE Line = " + str(loopcount))
    vwords = cursor_TW.fetchall()
    lineverse = ""
        
    for vword in vwords:

        linenum = vword[0]
        book = vword[1]
        chpt = vword[2]
        vrse = vword[3]
        word = vword[4]
        strong = vword[5]
        RMAC = vword[6]
        english = vword[7]
        punc = vword[8]
        engpunc = vword[9]

        if str(english) == "None":
            english = ""

        if str(engpunc) == "None":
            engpunc = ""


        # print(str(linenum) + " " + str(book) + " " + str(chpt) + ":" + str(vrse) + " " + str(word) + str(punc) + " " + str(strong) + " " + str(RMAC) + " " + str(english) + str(engpunc))
        linegroup = str(book) + str(chpt) + ":" + str(vrse) + " "
        wordgroup = str(word) + str(punc) + " " + str(english) + str(engpunc) + " " + str(strong) + " " + str(RMAC) 
        
        lineverse = lineverse + wordgroup + "  "
        
    txtfile.write(linegroup + lineverse + "\n")
    print(linegroup + lineverse)
    loopcount += 1

conn_TW.close()
txtfile.close()
