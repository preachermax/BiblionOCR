import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT NoDiaWord, VarianceForm FROM Variants")
wlines = cursor_TW.fetchall()
frlist = []

for wline in wlines:

        # assign field variables
        nodiaword = wline[0]
        varform = wline[1]
        print(nodiaword,"\t",varform)
        #update NormWord in Bible Table       
        cursor_TW.execute('UPDATE Variants SET VarianceForm = 2;')
        conn_TW.commit()
conn_TW.close()