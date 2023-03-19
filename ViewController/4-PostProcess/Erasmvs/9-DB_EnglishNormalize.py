import csv
import sqlite3
import re

csvfile = open("/home/max/Projects/Python/SQLite/csv/EnglishProperNames.csv")
csv_f = csv.reader(csvfile, delimiter = "\t")

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT ID, English, EnglishPunc FROM Bible")
wlines = cursor_TW.fetchall()
#print(wlines)
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
        cursor_TW.execute('''SELECT ID, English, EnglishPunc FROM Bible WHERE EnglishPunc == "." or EnglishPunc == "?" or EnglishPunc == "!"''')
        wlines = cursor_TW.fetchall()
        for wline in wlines:
                id = wline[0]
                cursor_TW.execute("SELECT ID, English FROM Bible WHERE English NOTNULL and ID >" + str(id))
                id,nextenglish = cursor_TW.fetchone()
                if nextenglish:
                        nextengword = nextenglish.split()[0]
                        #print(nextengwords)
                        
                        #print(nextengword)
                        #firstletter = nextengword[0]
                        #repword = re.sub((r"\b"+ cfind +r"\b"),creplace,engword)
                        repword = re.sub(nextengword, nextengword[0].upper()+nextengword[1:],nextengword)
                        #print(repword)
                        repenglish = nextenglish.replace(nextengword,repword)
                        print(id,nextenglish,repenglish)
                        '''
                        # assign field variables
                        #id = wline[0]
                        #english = wline[1].strip()
                        #englishpunc = wline[2]
                        #ienglish = wline[1].lower().strip()
                        #english = ienglish
                        
                        # loop backwards until a record containing English is found

                        # if englishpunc is present in found record, get englishpunc else skip update database and exit

                        # if englishpunc is a period, question mark, or exclamation point... else skip update database and exit

                        # return to original record and capitalize, if not already done. 
                        
                        previous = id - 1
                        if previous >= 1:
                                cursor_TW.execute("SELECT ID,English,EnglishPunc FROM Bible WHERE ID=?", (previous,))
                                prevrec = cursor_TW.fetchone()
                                prevenglish = prevrec[1]
                                prevpunc = prevrec[2]
                                if prevrec[2]=="." or prevrec[2]=="!" or prevrec[2]=="?":
                                        english = ienglish.replace(ienglish[0],ienglish[0].upper(),1)              
                                #print(prevpunc," ",prevenglish," ",english)
                                print(prevpunc,"\t",prevenglish,"\t",english)'''
                        
                        # update database
                        sql_qry = "UPDATE Bible SET English = ? WHERE ID = ?"
                        data = (repenglish, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()

def propernames():
        for row in csv_f:
                        cfind, creplace = (row[0].lower(), row[0])
                        #cfind, creplace = (row[1].lower(), row[1])
                        #cfind, creplace = ("disObed", "disobed")
                        #print(cfind,creplace)

                        for wline in wlines:
                                # assign field variables
                                id = wline[0]
                                english = wline[1]
                                #print(english)
                                # english = wline[1].strip()
                                # search each word-line(wline) to find matches to current cfind value
                                if str(english) != "None":
                                        engwords = english.split()
                                        
                                        #pattern = re.compile(('\b' + cfind))
                                        #matches = pattern.finditer(english)  
                                        #for match in matches:
                                                #engword = match[0]
                                                #print(engword)
                                        for engword in engwords:
                                                
                                                '''if str(english) == "i":
                                                        cfind = " i "
                                                        creplace = " I "
                                                elif str(english) == "er":
                                                        cfind = " er "
                                                        creplace = " Er "
                                                elif str(english) == "holy":
                                                        cfind = "holy"
                                                        creplace = "Holy"                                    
                                                else:
                                                        cfind = cfind + " "
                                                        creplace = creplace + " "'''

                                                repword = re.sub((r"\b"+ cfind +r"\b"),creplace,engword) 
                                                #repword = engword.replace(cfind, creplace)
                                                #print(engword, repword)                               
                                                #repword = engword.replace(cfind, creplace)
                                                #print(id," ", cfind," ", creplace," ", english," ", repword)
                                                if repword != engword:
                                                        repenglish = re.sub((r"\b"+ engword +r"\b"),repword,english)
                                                        #repenglish = english.replace(("\b"+ str(engword) +"\b"),repword)
                                                        english = repenglish
                                                        print(id," ", cfind," ", creplace," ", english)
                                                        
                                                        sql_qry = "UPDATE Bible SET English = ? WHERE ID = ?"
                                                        data = (english, id)
                                                        cursor_TW.execute(sql_qry, data)
                                                        conn_TW.commit()
#depunctualize()
propernames()
normalize()
   
                
                
conn_TW.close()                  
csvfile.close()        
