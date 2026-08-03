import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TR-Words_Esword.db')
print ("Opened Esword database successfully")

cursor_TW = conn_TW.cursor()

#cursor_TW.execute("SELECT * FROM Bible ")

conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_Esword.db')
print ("Opened Textus Receptus database successfully")

cursor_TR = conn_TR.cursor()

#cursor_TR.execute("SELECT Line,Book,Chapter,Verse,Scripture FROM Bible WHERE Book = 'Mat'")
cursor_TR.execute("SELECT Book,Chapter,Verse,WordNum,Word FROM Bible")

#vlines = cursor_TR.fetchone()
#vlines = cursor_TR.fetchmany(0)
vlines = cursor_TR.fetchall()
#print(vlines)
#line = vlines[0]

#print(line)

for vline in vlines:
       
    booknum = vline[0]
    chpt = vline[1]
    vrse = vline[2]
    wordnum = vline[3]
    word = vline[4]
    testword="Μαχ"
    enctestword = testword.encode('utf-8')
    print(enctestword)
    dectestword = enctestword.decode('unicode-escape')
    print(dectestword)
    print(word)
    uword=re.sub("\?","",word)
    print(uword)
    #uword=re.sub("(\\\\u\d+)(\?)","\1",word)
    #print(vline[4])
    rawword = r"{}".format(uword)
    print(rawword)
    #uword = uword.encode('utf-8').decode('unicode-escape')
    #rawword = uword.encode('utf-8').decode('unicode-escape')
    #print(str(booknum) + " " + str(chpt) + ":" + str(vrse) + ":" + str(wordnum) + " " + vline[4])
    encword = rawword.encode('utf-8')
    print(encword)
    #print(rawword)
    #print(uword)
    #t = word.encode('utf-8').decode('unicode-escape')
    
    #print(str(book) + str(wordnum))
    #print(str(book) + str(wordnum))
    #wordnum += 1
    # Database field separator groups:
    # print(match.group(1) + " " + match.group(3) + " " + match.group(4) + " " + match.group(6) + " " + match.group(7) + " " + match.group(9) + match.group(10) + " " + match.group(12))
    #print(vline)





conn_TR.commit()

conn_TR.close()
conn_TW.close()
