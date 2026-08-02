import csv
import sqlite3
import re

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened t FROMVS database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute("SELECT Line, WordNum, Word, NormWord, LcWord, NoDiaWord FROM Bible")

# Set path variables
mydbpath = '/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db'
mytxtpath = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_verses/Erasmus1516NT_Verses.txt'
normtxtpath = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_verses_norm/Erasmus1516NT_VersesNorm.txt'
reftxtpath = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Source/TR/TR-Verses.txt'
vartxtpath = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/Greek_verses_variants/Erasmus1516NT_Variants.txt'

# Remove previously normalized lines/verses
remfile = open(normtxtpath,"r+")
remfile.truncate(0)
remfile.close()

# Open text file and begin normalizing
lines = []
with open(mytxtpath, 'r') as txtfile:
    lines = txtfile.readlines()
    print(lines)
        
count = 0
for line in lines:
    # Initialize the LINE counter
    count += 1
    print(f'line {count}: {line}')

    # Initialize the WORD counter
    wordcount = 0
    
    # Split off the B C:V refernce
    verseref = line.split()[0:2]
    book, chapterverse = verseref
    print(f'verse reference: {verseref}\n')
    print(f'book: {book} chapterverse: {chapterverse}\n' )
    refstr = f'{book} {chapterverse}'

    # Create the wordlist count the words for the current line
    words = []
    words = line.split()[2:]
    wordscount = len(words)
    print(f'number of words in line: {wordscount}\n')

    # Initialize the final placeholder for the normalized line
    #normline = line

    # Iterate through the wordlist
    for word in words:
        # Remove punctuation
        nopunc = re.sub(r'[,.;,\';()]', '', word)
        #repword = nopunc.replace('.', '')
        #oldword = repword.replace(',', '')

        # Increment the word counter
        wordcount += 1
        
        #print(f'linenum: {count}  wordnum: {wordcount}  word: {word}\n')
        normfile = open("/home/max/Projects/BiblionOCR/Model/Project/Data/csv/ERASMVS_PUA_norm.csv")
        
        # Normalize ligatures in PUA and convert to lower case
        oldword = nopunc
        with normfile:
                csv_f = csv.reader(normfile)
                for row in csv_f:
                        #print(row[4],row[3])
                        cfind, creplace = (row[4], row[3])
                        normword = oldword.replace(cfind, creplace)
                        if normword != oldword:
                                #print(f'linenum: {count}  wordnum: {wordcount}  word: {oldword} normword: {normword}')
                                oldword=normword
                
                lowword = normword.lower()
                # replace final sigma
                #newlowword = lowword.replace("ς","σ")
                #lowword = newlowword

        normfile.close()

        # Remove diactritics
        diafile = open("/home/max/Projects/BiblionOCR/Model/Project/Data/csv/FromvsDiacritics.csv")
        
        oldword = lowword
        with diafile:
                csv_f = csv.reader(diafile)
                for row in csv_f:
                        #print(row[0],row[1])
                        cfind, creplace = (row[0], row[1])
                        nodiaword = oldword.replace(cfind, creplace)
                        if nodiaword != oldword:
                                #print(f'linenum: {count}  wordnum: {wordcount}  word: {oldword} nodiaword: {nodiaword}')
                                oldword=nodiaword
        diafile.close()

               
        sql_qry = '''UPDATE Bible SET NormWord = ?, LcWord = ?,NoDiaWord = ? WHERE Line = ? AND WordNum = ?'''
        data = (normword, lowword, nodiaword, count, wordcount)
        print(count, wordcount, normword, lowword, nodiaword)

        # Commit normalized word to database
        cursor_TW.execute(sql_qry, data)
        conn_TW.commit()
        
        # Assign normalized line/verse
        #normline = normline.replace(word,nodiaword)
        #normline = normline.replace(refstr,str(count)+'\t')

    # Print and save normalized line/verse
    #print(f'normalized line: {normline}')
    #with open(normtxtpath, 'a') as normfile:
            #normfile.write(normline)

normfile.close()
txtfile.close()   
