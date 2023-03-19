import csv
import sqlite3
import re

engopen = r"{\super\cf9 "
engclose = r"}{\super  }"
strongopen = r"{\super\cf11 "
strongclose = r"}{\super  }"
RMACopen = r"{\super\cf2 "
RMACclose = r"}"

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
#cursor_TW.execute("SELECT Word, UnicodeWord FROM Bible")
sql_qry = '''UPDATE Bible SET StrongOpen = ?, StrongClose = ?, RMACOpen = ?, RMACClose = ?, EnglishOpen = ?, EnglishClose = ?'''
data = (strongopen,strongclose,RMACopen,RMACclose,engopen,engclose)
cursor_TW.execute(sql_qry, data)
conn_TW.commit()
conn_TW.close()