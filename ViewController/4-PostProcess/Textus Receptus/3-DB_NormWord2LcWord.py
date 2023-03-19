import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBibleWords.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT NormWord, LcWord FROM Bible")
cursor_TW.execute('UPDATE Bible SET LcWord = NormWord;')
conn_TW.commit()

'''wlines = cursor_TW.fetchall()
frlist = []


for wline in wlines:

        # assign field variables
        oldword = wline[0]
        normword = wline[1]
        #update NormWord in Bible Table       
        cursor_TW.execute('UPDATE Bible SET LcWord = NormWord;')
        conn_TW.commit()'''
conn_TW.close()