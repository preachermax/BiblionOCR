import csv
import sqlite3
import re

txtfile = open('/home/max/Projects/Python/EstablishTruth/TR/TRi.txt')
csv_f = csv.reader(txtfile, delimiter = "\t")
#print(csv_f)

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRiBible.db')
print ("Opened the Textus Receptus database successfully")

cursor_TW = conn_TW.cursor()

# deprecated approach
cursor_TW.execute("DELETE FROM Bible")
conn_TW.commit()
print ("Deleted all of the Textus Receptus records successfully")
line = 1

for row in csv_f:
        rowline = row[0]
        textline = rowline.replace("\n","")
        #fbook, fchapt, fverse, fscrip  = (row[0], row[1], row[2], row[3])
        pattern = re.compile('(\d?\s?\w+\s)(\d+:)(\d+\s)(.*)')
        #pattern = re.compile('(^\w+\s+)(\d+:)(\d+\s+)')
        #pattern = re.compile('(^\w+\s+)')
        #pattern = re.compile('(\w+\s+)(\d+:)')
        matches = pattern.finditer(textline)

        for match in matches:
            book = match[1]
            chcolon = match[2]
            chapter = chcolon.replace(":","")
            verse = match[3]
            scripture = match[4]  
            #print(row[0])
            print(line,"\t", book,"\t", chapter,"\t", verse,"\t",scripture)
  
            #print(line,"\t", book,"\t", chapter,"\t", verse)
            #print(line,"\t", book,"\t", chapter)
           
            # then perhaps: Works Great!
            insert_parameters = """INSERT OR REPLACE INTO Bible (Line,Book,Chapter,Verse,Scripture)
                            VALUES ((select Line from Bible WHERE Book=? AND Chapter=? AND Verse=?),?,?,?,?)"""
            insert_data = (book,chapter,verse,book,chapter,verse,scripture)


            cursor_TW.execute(insert_parameters,insert_data)
            line += 1
            conn_TW.commit()