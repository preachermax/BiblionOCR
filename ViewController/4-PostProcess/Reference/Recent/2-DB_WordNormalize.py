import csv
import sqlite3
import re

loopcount = 1
        
while loopcount < 6:

        csvfile = open("/home/max/Projects/BiblionOCR/Model/Project/Data/csv/ERASMVS_PUA_norm.csv")
        #csv_f = csv.reader(csvfile, delimiter = "\t")
        csv_f = csv.reader(csvfile)


        conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
        print ("Opened TheWord database successfully")
        cursor_TW = conn_TW.cursor()
        cursor_TW.execute("SELECT ID, Word, NormWord FROM Bible")
        wlines = cursor_TW.fetchall()
        frlist = []

        for row in csv_f:
                cfind, creplace = (row[4], row[3])
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
                        
                        
                        # replace final sigma
                        # isfinalsigma = repword.rfind("σ")
                        lastchar = repword[-1]
                        if lastchar == "ς":
                                remsigma = repword[:-1]
                                repword = remsigma + "σ"  
                        
                        '''
                        if isfinalsigma:
                                newword = repword[:isfinalsigma] + "ς" + repword[isfinalsigma+1:]
                                if repword != newword:
                                        repword = newword   
                        
                        
                        finalsigma = "ς"
                        lastchar = repword[-1]
                        if lastchar == "σ":
                                repword = repword.replace(repword[-1],finalsigma)'''


                        if repword != normword:
                                # monitor data output
                                print(loopcount," ",id," ",word," ", cfind," ", creplace," ", normword," ", repword)
                                # update database
                                sql_qry = '''UPDATE Bible SET NormWord = ? WHERE ID = ?'''
                                data = (repword, id)
                                cursor_TW.execute(sql_qry, data)
                                conn_TW.commit()
                        
                        normword = repword
        loopcount += 1
                
        conn_TW.close()                  
        csvfile.close()        
