import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_TW.db')
print ("Opened TheWord database successfully")

cursor_TW = conn_TW.cursor()

#cursor_TW.execute("SELECT * FROM Bible ")

conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa_csv.db')
print ("Opened Textus Receptus database successfully")

cursor_TR = conn_TR.cursor()

#cursor_TR.execute("SELECT Line,Book,Chapter,Verse,Scripture FROM Bible WHERE Book = 'Mat'")
cursor_TR.execute("SELECT Line,Book,Chapter,Verse,Scripture FROM Bible")

#vlines = cursor_TR.fetchone()
#vlines = cursor_TR.fetchmany(50)
vlines = cursor_TR.fetchall()
#line = vlines[0]

#print(line)

for vline in vlines:
    pattern = re.compile('(<wt>)(\w+)(<)(W)(G\d+)(>)(<W)(\w+-?\w+?-?\w+?-?\w+?)(\s)(l=)(\w+)(>)([,.;]?)')
    #pattern = re.compile('(\d+)(,)(<wt>)(\w+)(<)(W)(G\d+)(>)(<W)(\w+-\w+?-?\w+?)(\s)(l=)(\w+)(>)([,.;]?)')
    matches = pattern.finditer(str(vline))
    linenum = vline[0]
    book = vline[1]
    chpt = vline[2]
    vrse = vline[3]
    wordnum = 1

    for match in matches:
        #print(match)"
        mstr = match.group(0)
        word_open = match.group(1)
        word = match.group(2)
        word_close = match.group(3)
        strong_open = match.group(4)
        strong = match.group(5)
        strong_close = match.group(6)
        rmac_open = match.group(7)
        rmac = match.group(8)
        rmac_close = match.group(9)
        lemma_open = match.group(10)
        lemma = match.group(11)
        lemma_close = match.group(12)
        punc = match.group(13)
      
        insert_parameters = """INSERT INTO Bible 
                            (Line,Book,Chapter,Verse,WordNum,WordOpen,Word,WordClose,StrongOpen,Strong,StrongClose,RMACOpen,RMAC,RMACClose,LemmaOpen,Lemma,LemmaClose,WordPunc)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_data = (linenum,book,chpt,vrse,wordnum,word_open,word,word_close,strong_open,strong,strong_close,rmac_open,rmac,rmac_close,lemma_open,lemma,lemma_close,punc)
        cursor_TW.execute(insert_parameters,insert_data)
        conn_TW.commit()

        # Database field search groups:
        #print(Book,Chapter,Verse)
        #if linenum == 250:
        print(str(linenum) + " " + str(book) + " " + str(chpt) + ":" + str(vrse) + ":" + str(wordnum) + " " + match.group(2) + " " + match.group(5) + " " + match.group(8) + " " + match.group(11)+ " " + match.group(13))
        #print(str(book) + str(wordnum))
        wordnum += 1
        # Database field separator groups:
        # print(match.group(1) + " " + match.group(3) + " " + match.group(4) + " " + match.group(6) + " " + match.group(7) + " " + match.group(9) + match.group(10) + " " + match.group(12))
    
    #print(vline)





conn_TR.commit()

conn_TR.close()
conn_TW.close()
