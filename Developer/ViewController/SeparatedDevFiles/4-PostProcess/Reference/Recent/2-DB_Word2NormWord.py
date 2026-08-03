import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute('UPDATE Bible SET NormWord = Word;')
conn_TW.commit()

'''cursor_TW.execute("SELECT Word, NormWord FROM Bible")
wlines = cursor_TW.fetchall()


for wline in wlines:

        # assign field variables
        oldword = wline[0]
        normword = wline[1]
        #update NormWord in Bible Table       
        cursor_TW.execute('UPDATE Bible SET NormWord = Word;')
        conn_TW.commit()'''

conn_TW.close()