import csv
import sqlite3
import re

txtfile = open('/home/max/Projects/Python/EstablishTruth/TR/TR-Verses.txt')
csv_f = csv.reader(txtfile, delimiter = "\t")
#print(csv_f)

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBible.db')
print ("Opened the Textus Receptus database successfully")

cursor_TW = conn_TW.cursor()

# deprecated approach
cursor_TW.execute("DELETE FROM Bible")
conn_TW.commit()
print ("Deleted all of the Textus Receptus records successfully")


for row in csv_f:
        rowline = row[0]
        textline = rowline.replace("\n","")
        #fbook, fchapt, fverse, fscrip  = (row[0], row[1], row[2], row[3])
        pattern = re.compile('(^\w+\s)(\d+:)(\d+\s)(.*)')
        matches = pattern.finditer(textline)  
        for match in matches:
            book = match[1]
            chcolon = match[2]
            chapter = chcolon.replace(":","")
            verse = match[3]
            scripture = match[4]
            #print(row[0])
            print(book,"\t", chapter,"\t", verse,"\t",scripture)
           
            '''# deprecated - works well but requires deleting all records, first and completely rebuilding the table
            insert_parameters = """INSERT INTO Bible 
                            (Book,Chapter,Verse,Scripture)
                             VALUES (?,?,?,?)""" 
            insert_data = (book,chapter,verse,scripture)'''

            '''# web-snippet:
            insert or replace into Book (ID, Name, TypeID, Level, Seen) values
                            ((select ID from Book where Name = "SearchName"), "SearchName", ...);'''

            # then perhaps: Works Great!
            insert_parameters = """INSERT OR REPLACE INTO Bible (Line,Book,Chapter,Verse,Scripture)
                            VALUES ((select Line from Bible WHERE Book=? AND Chapter=? AND Verse=?),?,?,?,?)"""
            insert_data = (book,chapter,verse,book,chapter,verse,scripture)


            cursor_TW.execute(insert_parameters,insert_data)
            conn_TW.commit()