import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_TW.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, RMAC FROM Bible")
rmacs = cursor_TW.fetchall()
frlist = []

for rmac in rmacs:

        # assign field variables
        id = rmac[0]
        oldrmac = rmac[1]
        newrmac = oldrmac.replace("T","",1)
        print(oldrmac,"\t\t",newrmac)
        #update RMAC in Bible Table       
        query = '''UPDATE Bible SET RMAC = ? WHERE ID = ?'''
        data = (newrmac,id)
        cursor_TW.execute(query,data)
        conn_TW.commit()
conn_TW.close()