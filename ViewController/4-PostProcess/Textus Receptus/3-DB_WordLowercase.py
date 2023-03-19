import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBibleWords.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, NormWord, LcWord FROM Bible")
wlines = cursor_TW.fetchall()
frlist = []

for wline in wlines:

        # assign field variables
        id = wline[0]
        normword = wline[1]
        lcword = wline[2].lower()
        

        if lcword != normword:
                # monitor data output
                print(normword," ", lcword)
                # update database
                sql_qry = '''UPDATE Bible SET LcWord = ? WHERE ID = ?'''
                data = (lcword, id)
                cursor_TW.execute(sql_qry, data)
                conn_TW.commit()
        
                        
conn_TW.close()                         
