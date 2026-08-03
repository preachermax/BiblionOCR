import csv
import sqlite3
import re

txtfile = open('Workflow/4-PostProcess/test.txt', 'w')
csvfile = open("/home/max/Projects/Python/SQLite/csv/FromvsDiacritics.csv")
csv_f = csv.reader(csvfile, delimiter = "\t")


conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRBibleWords.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, Word, NormWord, LcWord, NoDiaWord FROM Bible")
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
                word = wline[1]
                normword = wline[2]
                lcword = wline[3]
                nodiaword = wline[4]
                #lcword = normword.lower()

                # search each word-line(wline) to find matches to current cfind value
                repword = nodiaword.replace(cfind, creplace)
                #lcword = repword.lower()

                if repword != nodiaword:
                        # monitor data output
                        print(word," ", cfind," ", creplace," ", lcword," ", repword," ", nodiaword)
                        # update database
                        sql_qry = '''UPDATE Bible SET NoDiaWord = ? WHERE ID = ?'''
                        data = (repword, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                
                nodiaword = repword
                
conn_TW.close()                  
txtfile.close()
csvfile.close()        
