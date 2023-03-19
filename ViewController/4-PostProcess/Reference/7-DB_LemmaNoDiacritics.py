import csv
import sqlite3
import re

txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
csvfile = open("/home/max/Projects/Python/SQLite/FromvsDiacritics.csv")
csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, LcLemma, NoDiaLemma FROM Bible")
wlines = cursor_TW.fetchall()
frlist = []

for row in csv_f:
        cfind, creplace = (row[0], row[1])
        #print(cfind,creplace)
        #frlist.append(cfind, creplace)
        print(frlist)
        
        for wline in wlines:
        
                # assign field variables
                id = wline[0]
                lclemma = wline[1]
                nodialemma = wline[2]

                #lcword = normword.lower()

                # search each word-line(wline) to find matches to current cfind value
                replemma = nodialemma.replace(cfind, creplace)
                #lcword = repword.lower()

                if replemma != nodialemma:
                        # monitor data output
                        print(cfind," ", creplace," ", lclemma," ", nodialemma," ", replemma)
                        # update database
                        sql_qry = '''UPDATE Bible SET NoDiaLemma = ? WHERE ID = ?'''
                        data = (replemma, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                
                nodialemma = replemma
                
conn_TW.close()                  
txtfile.close()
csvfile.close()        
