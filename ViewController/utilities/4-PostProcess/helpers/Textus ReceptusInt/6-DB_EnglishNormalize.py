import csv
import sqlite3
import re

csvfile = open("/home/max/Projects/Python/SQLite/csv/EnglishProperNames.csv")
csv_f = csv.reader(csvfile, delimiter = "\t")

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRiBibleWords.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, English, EnglishPunc FROM Bible WHERE English<>''")
wlines = cursor_TW.fetchall()
frlist = []
        
def depunctualize():

        for wline in wlines:

                # assign field variables
                id = wline[0]
                english = wline[1].strip()
                englishpunc = wline[2]
                ienglish = wline[1].lower().strip()
                
                lastchar = ienglish[-1] 
                #print(lastchar)
                if lastchar == "." or lastchar == "?" or lastchar == "!" or lastchar == "," or lastchar == ";" or lastchar == ":":
                        englishpunc = lastchar
                        english = ienglish[:-1]
                else:
                        englishpunc = ""
                        english = ienglish
                
                print(id," ",english," ",englishpunc)

                sql_qry = "UPDATE Bible SET English = ?, EnglishPunc = ? WHERE ID = ?"
                data = (english, englishpunc, id)
                cursor_TW.execute(sql_qry, data)
                conn_TW.commit()
        
def normalize():       
        for wline in wlines:

                # assign field variables
                id = wline[0]
                #english = wline[1].strip()
                englishpunc = wline[2]
                ienglish = wline[1].lower().strip()
                english = ienglish
                previous = id - 1
                if previous >= 1:
                        cursor_TW.execute("SELECT ID,English,EnglishPunc FROM Bible WHERE ID=?", (previous,))
                        prevrec = cursor_TW.fetchone()
                        prevenglish = prevrec[1]
                        prevpunc = prevrec[2]
                        if prevrec[2]=="." or prevrec[2]=="!" or prevrec[2]=="?":
                                english = ienglish.replace(ienglish[0],ienglish[0].upper(),1)              
                        #print(prevpunc," ",prevenglish," ",english)
                        print(prevpunc,"\t",prevenglish,"\t",english)
                
                # update database
                sql_qry = "UPDATE Bible SET English = ? WHERE ID = ?"
                data = (english, id)
                cursor_TW.execute(sql_qry, data)
                conn_TW.commit()

def propernames():
        for row in csv_f:
                        cfind, creplace = (row[0].lower(), row[0])
                        #cfind, creplace = ("disObed", "disobed")
                        print(cfind,creplace)

                        for wline in wlines:
                                # assign field variables
                                id = wline[0]
                                english = wline[1].strip()
                                # search each word-line(wline) to find matches to current cfind value
                                repword = english.replace(cfind, creplace)
                                if repword != english:
                                        english = repword
                                        print(id," ", cfind," ", creplace," ", english)
                                        sql_qry = "UPDATE Bible SET English = ? WHERE ID = ?"
                                        data = (english, id)
                                        cursor_TW.execute(sql_qry, data)
                                        conn_TW.commit()
#depunctualize()
#normalize()
propernames()   
                
                
conn_TW.close()                  
csvfile.close()        
