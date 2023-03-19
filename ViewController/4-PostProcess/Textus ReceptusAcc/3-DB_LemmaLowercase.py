import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_TW.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, Lemma, LcLemma FROM Bible")
wlines = cursor_TW.fetchall()
frlist = []

for wline in wlines:

        # assign field variables
        id = wline[0]
        lemma = wline[1]
        lclemma = wline[2].lower()
        

        if lclemma != lemma:
                # monitor data output
                print(lemma," ", lclemma)
                # update database
                sql_qry = '''UPDATE Bible SET LcLemma = ? WHERE ID = ?'''
                data = (lclemma, id)
                cursor_TW.execute(sql_qry, data)
                conn_TW.commit()
        
                        
conn_TW.close()                         
