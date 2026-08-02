import csv
import sqlite3
import re

loopcount = 1
        
while loopcount < 5:
        csvfile = open("/home/max/Projects/Python/SQLite/csv/FROMVS_ChrList.csv")
        csv_f = csv.reader(csvfile, delimiter = "\t")


        conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
        print ("Opened TheWord database successfully")
        cursor_TW = conn_TW.cursor()
        cursor_TW.execute("SELECT ID, UnicodeWord FROM Bible")
        wlines = cursor_TW.fetchall()
        frlist = []

        for row in csv_f:
                cfind, creplace = (row[0], row[2])
                #print(cfind,creplace)
                #frlist.append(cfind, creplace)
                #print(frlist)
                
                for wline in wlines:
                
                        # assign field variables
                        id = wline[0]
                        uniword = wline[1]
                        
                        # search each word-line(wline) to find matches to current cfind value
                        repword = uniword.replace(cfind, creplace)

                        if repword != uniword:
                                # monitor data output
                                print(uniword," ", cfind," ", creplace," ", repword)
                                # update database
                                
                                sql_qry = '''UPDATE Bible SET UnicodeWord = ? WHERE ID = ?'''
                                data = (repword, id)
                                cursor_TW.execute(sql_qry, data)
                                conn_TW.commit()
                        
                        uniword = repword
        loopcount += 1
                
        conn_TW.close()                  
        csvfile.close()        
