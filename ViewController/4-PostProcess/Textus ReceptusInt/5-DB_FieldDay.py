import csv
import sqlite3
import re

#txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
#csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
#csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRiBibleWords.db')
print ("Opened FROMVS database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID,Book,Verse,Word,Strong,English FROM Bible")
wlines = cursor_TW.fetchall()


        
for wline in wlines:
        
        # assign FROMVS field variables
        id = wline[0]
        book = wline[1].strip()
        verse = wline[2].strip()
        word = wline[3]
        strong = wline[4].strip()
        '''lowerenglish = wline[5].lower()
        word_list = lowerenglish.split()
        number_of_eng_words = len(word_list)

        if word[0].isupper() and number_of_eng_words == 1:
                english = lowerenglish[:1].upper() + lowerenglish[1:]
        else:
                english = lowerenglish'''

        #cursor_TW.execute("SELECT DISTINCT ID, Line, WordNum, Word, NoDiaWord, NoDiaLemma, Strong, RMAC, Lemma FROM TRaBible")
        
        cursor_TW.execute("SELECT Book,Verse,Strong,English FROM Bible WHERE ID=?", (id,))
        tlist = cursor_TW.fetchone()
        #print(book,"\t",verse,"\t",strong)              
        
        if tlist:
                
                # update database
                sql_qry = "UPDATE Bible SET Book = ?, Verse = ?, Strong = ?"
                data = (book, verse, strong)
                cursor_TW.execute(sql_qry, data)
                conn_TW.commit()
        
conn_TW.close()                          
