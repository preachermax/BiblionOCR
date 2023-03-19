import sqlite3
import re

#txtfile = open('/home/max/Projects/Python/EstablishTruth/Greek completed text/Erasmus1516NT_Verses.txt', 'r')
#pattern = re.compile('(^\w+\s)(\d+:)(\d+:\s)(\w+)')


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBibleWords.db')
print ("Opened The Textus Receptus Words database successfully")

cursor_TW = conn_TW.cursor()

# deprecated approach
'''cursor_TW.execute("DELETE FROM Bible")
conn_TW.commit()
print ("Deleted all of the ERASMVS1516 records successfully")'''

#cursor_TW.execute("SELECT * FROM Bible ")

conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBible.db')
print ("Opened the Textus Receptus database successfully")

cursor_TR = conn_TR.cursor()

#cursor_TR.execute("SELECT Line,Book,Chapter,Verse,Scripture FROM Bible WHERE Book = 'Mat'")
cursor_TR.execute("SELECT Line,Book,Chapter,Verse,Scripture FROM Bible")

#vlines = cursor_TR.fetchone()
#vlines = cursor_TR.fetchmany(0)
vlines = cursor_TR.fetchall()
#line = vlines[0]

#print(line)

for vline in vlines:
    #print(vline[4].encode('utf-8'))
    
#If you want to exclude just space and newline characters, then you might want to use r'^[^ \n]*$'
    
    pattern = re.compile('([^ \n,.;]+)([,.;]?)')
    #pattern = re.compile('([^ \n,.;]+)([,.;]?[^ \n\s])')
    #pattern = re.compile('(\w+)([,.;]?)(\s)')
    #pattern = re.compile('(<wt>)(\w+)(<)(W)(G\d+)(>)(<W)(\w+-\w+?-?\w+?)(\s)(l=)(\w+)(>)([,.;]?)')
    #pattern = re.compile('(\d+)(,)(<wt>)(\w+)(<)(W)(G\d+)(>)(<W)(\w+-\w+?-?\w+?)(\s)(l=)(\w+)(>)([,.;]?)')
    matches = pattern.finditer(str(vline[4]))
        
    linenum = vline[0]
    book = vline[1]
    chpt = vline[2]
    vrse = vline[3]
    #print(vline[4])
    wordnum = 1

    for match in matches:
        #print(match)
        mstr = match.group(0)
        #word_open = match.group(1)
        word = match.group(1)
        #print(word)
        '''word_close = match.group(3)
        strong_open = match.group(4)
        strong = match.group(5)
        strong_close = match.group(6)
        rmac_open = match.group(7)
        rmac = match.group(8)
        rmac_close = match.group(9)
        lemma_open = match.group(10)
        lemma = match.group(11)
        lemma_close = match.group(12)'''
        punc = match.group(2)
      
        # deprecated - works well but requires deleting all records, first and completely rebuilding the table
        '''insert_parameters = """INSERT INTO Bible 
                            (Line,Book,Chapter,Verse,WordNum,Word,WordPunc)
                             VALUES (?,?,?,?,?,?,?)"""
        insert_data = (linenum,book,chpt,vrse,wordnum,word,punc)'''
        
        # Works best but still deletes the record before replacing
        insert_parameters = """INSERT OR REPLACE INTO Bible (ID,Line,Book,Chapter,Verse,WordNum,Word,WordPunc)
                            VALUES ((select ID from Bible WHERE Line=? AND WordNum=?),?,?,?,?,?,?,?)"""
        insert_data = (linenum,wordnum,linenum,book,chpt,vrse,wordnum,word,punc)
        
        cursor_TW.execute(insert_parameters,insert_data)
        conn_TW.commit()

        # Database field search groups:
        #print(Book,Chapter,Verse)
        print(str(linenum) + " " + str(book) + " " + str(chpt) + ":" + str(vrse) + ":" + str(wordnum) + " " + str(word) + " " + str(punc))
        
        #open test.txt file
        #encword = word.encode('utf-8').decode('unicode-escape')
        #txtfile.write(str(word) + str(punc) + "\n")
        #txtfile.write(str(linenum) + " " + str(book) + " " + str(chpt) + ":" + str(vrse) + ":" + str(wordnum) + " " + str(word) + str(punc) + "\n")
        #print(str(book) + str(wordnum))
        wordnum += 1
        # Database field separator groups:
        # print(match.group(1) + " " + match.group(3) + " " + match.group(4) + " " + match.group(6) + " " + match.group(7) + " " + match.group(9) + match.group(10) + " " + match.group(12))
    
    #print(vline)





conn_TR.commit()

conn_TR.close()
conn_TW.close()
txtfile.close()
