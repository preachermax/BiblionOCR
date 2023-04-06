import csv
import sqlite3
import re

# Set path variables
mytxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_norm/MarkVerses/Erasmus1516NT_Verses.txt'
normreftxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/TR/TR-VersesNorm.txt'
reftxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/TR/TR-Verses.txt'
vartxtpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_variants/MarkVerses/Erasmus1516NT_Variants.txt'

# Remove previously normalized reference lines/verses
remfile = open(normreftxtpath,"r+")
remfile.truncate(0)
remfile.close()

# Open reference text file and begin normalizing
lines = []
with open(reftxtpath, 'r') as txtfile:
        lines = txtfile.readlines()

count = 0
for line in lines:
    count += 1
    print(f'line {count}: {line}')
    wordcount = 0
    verseref = line.split()[0:2]
    book, chapterverse = verseref
    print(f'verse reference: {verseref}\n')
    print(f'book: {book} chapterverse: {chapterverse}\n' )
    refstr = f'{book} {chapterverse}'
    words = []
    words = line.split()[2:]
    wordscount = len(words)
    print(f'number of words in verse line: {wordscount}\n')
    normline = line
    #normline = (f'{count} {words}')
    print(normline)
    
    for word in words:
        wordcount += 1
        #print(f'linenum: {count}  wordnum: {wordcount}  word: {word}\n')
        normfile = open("/home/max/Projects/BiblionOCR/Model/Data/csv/ERASMVS_PUA_norm.csv")
        
        # Normalize ligatures in PUA and convert to lower case      
        oldword = word
        with normfile:
                csv_f = csv.reader(normfile, delimiter = "\t")
                for row in csv_f:
                        #print(row[4],row[3])
                        cfind, creplace = (row[4], row[3])
                        normword = oldword.replace(cfind, creplace)
                        if normword != oldword:
                                #print(f'linenum: {count}  wordnum: {wordcount}  word: {oldword} normword: {normword}')
                                oldword=normword
                lowword = normword.lower()
        normfile.close()

        # Remove diactritics
        diafile = open("/home/max/Projects/BiblionOCR/Model/Data/csv/FromvsDiacritics.csv")
        
        oldword = lowword
        with diafile:
                csv_f = csv.reader(diafile, delimiter = "\t")
                for row in csv_f:
                        #print(row[4],row[3])
                        cfind, creplace = (row[0], row[1])
                        nodiaword = oldword.replace(cfind, creplace)
                        if nodiaword != oldword:
                                #print(f'linenum: {count}  wordnum: {wordcount}  word: {oldword} nodiaword: {nodiaword}')
                                oldword=nodiaword
        diafile.close()
        
        # Assign normalized line/verse
        normline = normline.replace(word,nodiaword)
        normline = normline.replace(refstr,str(count)+'\t')
    # Print and save normalized reference line/verse        
    print(f'normalized line: {normline}')
    with open(normreftxtpath, 'a') as normfile:
            normfile.write(normline)

normfile.close()
txtfile.close()     
