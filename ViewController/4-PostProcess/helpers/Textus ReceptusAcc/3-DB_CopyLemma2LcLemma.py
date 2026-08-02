import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_TW.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT Lemma, LcLemma FROM Bible")
wlines = cursor_TW.fetchall()
frlist = []

for wline in wlines:

        # assign field variables
        lemma = wline[0]
        lclemma = wline[1]
        #update NormWord in Bible Table       
        cursor_TW.execute('UPDATE Bible SET LcLemma = Lemma;')
        conn_TW.commit()
conn_TW.close()