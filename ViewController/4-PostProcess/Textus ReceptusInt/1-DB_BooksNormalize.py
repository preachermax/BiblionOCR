import csv
import sqlite3
import re

txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
csvfile = open("/home/max/Projects/Python/SQLite/csv/BooksAbbrName.csv")
csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRiBible.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT Line, Book FROM Bible")
wlines = cursor_TW.fetchall()
frlist = []

for row in csv_f:
        cfind, creplace = (row[1], row[0])
        #print(cfind,creplace)
        #frlist.append(cfind, creplace)
        print(frlist)
        
        for wline in wlines:
        
                # assign field variables
                line = wline[0]
                bookname = wline[1]
                # search each word-line(wline) to find matches to current cfind value
                book = bookname.replace(cfind, creplace)
                
                if book != bookname:
                        # monitor data output
                        print(line," ",cfind," ", creplace," ", book)
                        # update database
                        sql_qry = "UPDATE Bible SET Book = ? WHERE Line = ?"                
                        data = (book, line)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                
conn_TW.close()                  
txtfile.close()
csvfile.close()        
