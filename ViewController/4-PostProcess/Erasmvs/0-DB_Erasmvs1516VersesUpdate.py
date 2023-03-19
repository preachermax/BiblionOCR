import csv
import sqlite3
import re

txtfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_verses/Erasmus1516NT_Verses.txt')
#csvfile = open("/home/max/Projects/Python/EstablishTruth/Greek completed text/Erasmus1516NT_Verses.csv")
csv_f = csv.reader(txtfile, delimiter = "\t")
#print(csv_f)

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/Erasmvs1516.db')
print ("Opened the ERASMVS1516 database successfully")

cursor_TW = conn_TW.cursor()

# deprecated approach
cursor_TW.execute("DELETE FROM Bible")
conn_TW.commit()
print ("Deleted all of the ERASMVS1516 records successfully")

for row in csv_f:
        rowline = row[0]
        textline = rowline.replace("\n","")
        #fbook, fchapt, fverse, fscrip  = (row[0], row[1], row[2], row[3])
        pattern = re.compile('(\w+\s)(\d+:)(\d+\s)(.*)')
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