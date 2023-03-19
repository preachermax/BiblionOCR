import csv
import sqlite3
import re


csvfile = open("/home/max/Projects/BiblionOCR/Model/Project/Data/csv/BooksAbbrName.csv")
csv_f = csv.reader(csvfile)


conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()

for row in csv_f:
        abbr = row[0]
        name = row[1]
        bookno = row[2]
                        
        print(name,"\t",abbr,"\t",bookno)
        sql_qry = "UPDATE Bible SET BookNum = ? WHERE Book = ?"
        data = (bookno, abbr)
        cursor_TW.execute(sql_qry, data)
        conn_TW.commit()
                
        
conn_TW.close()                  
csvfile.close()        
