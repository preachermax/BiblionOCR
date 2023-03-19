import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, UnicodeWord FROM Bible")
wlines = cursor_TW.fetchall()
     
for wline in wlines:

        # assign field variables
        id = wline[0]
        uniword = wline[1]
        print(uniword)
        repstr = ""
        lastchr = len(uniword)
        print(lastchr)

        for element in range(0, lastchr):
                hexchr = str(hex(ord(uniword[element])))
                hexchr = hexchr.replace('0x', '')
                repchr = r"\u" + hexchr + "?"
                repstr = repstr + repchr
                print(uniword," ",repstr)
        
        # update database       
        #sql_qry = '''UPDATE Bible SET UnicodeWord = ? WHERE ID = ?'''
        #data = (repstr, id)
        #cursor_TW.execute(sql_qry, data)
        #conn_TW.commit()
                
conn_TW.close()                       
