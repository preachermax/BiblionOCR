import csv
import sqlite3
import re

mytxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_norm/MarkVerses/Erasmus1516NT_Verses.txt'

reftxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/TR/TR-Verses.txt'
vartxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_variants/MarkVerses/Erasmus1516NT_Variants.txt'

csvfile = open("/home/max/Projects/BiblionOCR/Model/Data/csv/ERASMVS_PUA_norm.csv")

#frlist = []

lines = []
with open(mytxtpath, 'r') as f:
        lines = f.readlines()

count = 0
for line in lines:
    count += 1
    print(f'line {count}: {line}')
    wordcount = 0
    words = []
    words = line.split()[2:]
    wordscount = len(words)
    print(f'number of words in line: {wordscount}\n')
    #for words in line.split()[2:]:
    for word in words:
        wordcount += 1
        print(f'linenum: {count}  wordnum: {wordcount}  word: {word}\n')
        csvfile = open("/home/max/Projects/BiblionOCR/Model/Data/csv/ERASMVS_PUA_norm.csv")
        oldword = word
        with csvfile:
                csv_f = csv.reader(csvfile, delimiter = "\t")
                for row in csv_f:
                        #print(row[4],row[3])
                        cfind, creplace = (row[4], row[3])
                        #print(f'find: {cfind} replace: {creplace}')
                        #frlist.append(cfind, creplace)
                        # print(frlist)
                        normword = oldword.replace(cfind, creplace)
                        
                        # replace final sigma
                        # isfinalsigma = repword.rfind("σ")
                        lastchar = normword[-1]
                        if lastchar == "σ":
                                remsigma = normword[:-1]
                                normword = remsigma + "ς"  
                        
                        if isfinalsigma:
                                newword = normword[:isfinalsigma] + "ς" + normword[isfinalsigma+1:]
                                if normword != normword:
                                        normword = newword

                        finalsigma = "ς"
                        lastchar = normword[-1]

                        if lastchar == "σ":
                                normword = normword.replace(normword[-1],finalsigma)
                        
                        if normword != oldword:
                                print(f'linenum: {count}  wordnum: {wordcount}  word: {oldword} normword: {normword}')
                                oldword=normword
        csvfile.close()
f.close()

'''       
reflines = []
with open(reftxtpath, 'r') as ref:
        reflines = ref.readlines()

refcount = 0
for refline in reflines:
    refcount += 1
    print(f'ref line {refcount}: {refline}')
    refwordcount = 0
    refwords = []
    refwords = refline.split()[2:]
    refwordscount = len(refwords)
    print(f'number of words in line: {refwordscount}\n')
    #for refwords in refline.split()[2:]:
    for refword in refwords:
        refwordcount += 1
        print(f'reflinenum: {refcount}  refwordnum: {refwordcount}  refword: {refword}\n')'''  


#ref.close()

#vartxtpath = open('/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_variants/MarkVerses/Erasmus1516NT_Variants.txt', 'w')

#conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
#print ("Opened TheWord database successfully")
#cursor_TW = conn_TW.cursor()
#cursor_TW.execute("SELECT ID, Word, NormWord FROM Bible")
#wlines = cursor_TW.fetchall()
'''
frlist = []

for row in csv_f:
        cfind, creplace = (row[4], row[3])
        #print(cfind,creplace)
        #frlist.append(cfind, creplace)
        #print(frlist)
        
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
                if lastchar == "σ":
                        remsigma = repword[:-1]
                        repword = remsigma + "ς"  
                
                
                if isfinalsigma:
                        newword = repword[:isfinalsigma] + "ς" + repword[isfinalsigma+1:]
                        if repword != newword:
                                repword = newword   
                
                
                finalsigma = "ς"
                lastchar = repword[-1]
                if lastchar == "σ":
                        repword = repword.replace(repword[-1],finalsigma)


                if repword != normword:
                        # monitor data output
                        print(loopcount," ",id," ",word," ", cfind," ", creplace," ", normword," ", repword)
                        # update database
                        sql_qry = """UPDATE Bible SET NormWord = ? WHERE ID = ?"""
                        data = (repword, id)
                        cursor_TW.execute(sql_qry, data)
                        conn_TW.commit()
                
                normword = repword

        
conn_TW.close()                  
txtfile.close()
csvfile.close()'''        
