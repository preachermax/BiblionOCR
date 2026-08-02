import csv
import sqlite3
import re

txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
csvfile = open("/home/max/Projects/Python/SQLite/FROMVS_PUA_norm.csv")
csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_TW.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, Word, NormWord FROM Bible")
wlines = cursor_TW.fetchall()
frlist = []

for row in csv_f:
        cfind, creplace = (row[2], row[3])
        #print(cfind,creplace)
        #frlist.append(cfind, creplace)
        print(frlist)
        
        for wline in wlines:
        
                # assign field variables
                id = wline[0]
                word = wline[1]
                normword = wline[2]
                #lcword = normword.lower()

                # search each word-line(wline) to find matches to current cfind value
                repword = normword.replace(cfind, creplace)
                #lcword = repword.lower()

                if repword != normword:
                        # monitor data output
                        print(word," ", cfind," ", creplace," ", normword," ", repword)
                        # update database
                        sql_qry = '''UPDATE Bible SET NormWord = ? WHERE ID = ?'''
                        data = (repword, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                
                normword = repword
                
conn_TW.close()                  
txtfile.close()
csvfile.close()        
