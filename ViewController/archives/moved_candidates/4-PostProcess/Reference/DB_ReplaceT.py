import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
#cursor_TW.execute("SELECT ID, RMAC FROM Bible")
#cursor_TW.execute("SELECT ID, RMAC FROM Variants")
cursor_TW.execute("SELECT ID, RMAC FROM Resolved")
rmacs = cursor_TW.fetchall()
frlist = []

for rmac in rmacs:

        # assign field variables
        id = rmac[0]
        oldrmac = rmac[1]
        #if oldrmac and oldrmac[0]+oldrmac[1] != "TT":
        #if oldrmac and oldrmac[0] == "-":
        if oldrmac:
                newrmac = oldrmac.replace("T","",1)
                print(oldrmac,"\t\t",newrmac)
                #update RMAC in Bible Table       
                query = '''UPDATE Resolved SET RMAC = ? WHERE ID = ?'''
                data = (newrmac,id)
                cursor_TW.execute(query,data)
                conn_TW.commit()
conn_TW.close() 