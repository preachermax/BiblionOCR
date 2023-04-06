import csv
import sqlite3
import re

# Initialize variant fieldlist
#varfields = [ID,Line,Book,Chapter,Verse,WordNum,Word,NoDiaWord,VarWord,Strong,RMAC,Lemma,VarianceForm,VarianceType,ImpactCode,ErrorCode,VarCode,Description,Preserved,Corrected,Error,Variance,Context,Inflection,Resolved]

# Set path variables

versepath = '/home/max/Projects/BiblionOCR/Model/Data/csv/VerseLines.csv'
mytextpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_norm/MarkVerses/Erasmus1516NT_VersesNorm.txt'
reftextpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/TR/TR-VersesNorm.txt'
vartextpath = '/home/max/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek_verses_variants/MarkVerses/Erasmus1516NT_Variants.txt'


verselines = []
with open(versepath, 'r') as versefile:
    csv_f = csv.reader(versefile, delimiter = "\t")
    for row in csv_f:
        verselines.append(row) 
versefile.close()

normlines = []
linecount = 0
with open(mytextpath, 'r') as textfile:
        textlines = textfile.readlines()

        for textline in textlines:
             linecount += 1
             normlines.append(textline)
             normlinenum, normline = textline.split('\t')
textfile.close()

refnormlines = []
with open(reftextpath, 'r') as reftextfile:
        reflines = reftextfile.readlines()
        
        for refline in reflines:
             refnormlines.append(refline)
             refnormlinenum, refnormline = refline.split('\t')
reftextfile.close()

loopcount = 0       
while loopcount <= linecount:
        loopcount += 1
        for verseline in verselines:
                verselinenum = str(verseline[0])
                
                count = 0
                wordscount = 0
                for textnormline in normlines:
                        normlinenum, normline = textnormline.split('\t')

                        # locate current verse
                        if str(normlinenum) == str(verselinenum):
                                count += 1
                                wordscount = 0
                                words = []
                                words = normline.split()#[2:]
                                # get verse word count 
                                wordscount = len(words)

                refcount = 0
                refwordscount = 0
                for textrefnormline in refnormlines:
                        refnormlinenum, refnormline = textrefnormline.split('\t')
                        
                        # locate current ref verse
                        if str(refnormlinenum) == str(verselinenum):
                                refcount += 1
                                refwordscount = 0
                                refwords = []
                                refwords = refnormline.split()#[2:]
                                # get ref verse word count 
                                refwordscount = len(refwords)

                if wordscount != 0:
                        print(f'line: {verselinenum} number of ref words: {refwordscount} number of words {wordscount}')
                        if refwordscount != wordscount:
                                print(f'There is a count difference in line: {verselinenum}')
                                if refwordscount > wordscount:
                                        print('There are added reference words missing in verse words')
                                        # Since there are extra ref words,
                                        refwordnum = 1
                                        wordnum = 1
                                        for word in words:
                                                #words.index(word[, wordnum[, wordnum]])
                                                while refwordnum <= refwordscount:
                                                        for refword in refwords:
                                                                if refword == word:
                                                                        print(f'{refword} matches {word}')
                                                                
                                                                        if refwordnum == wordnum:
                                                                                print('Perfect match!')
                                                                        elif refwordnum > wordnum:
                                                                                print(f'previous {refword} added, {word} matches later {refword}')
                                                               
                                                                wordnum += 1

                                                refwordnum += 1 

                                        
                                elif wordscount > refwordscount:
                                        print('There are added verse words missing in reference words')
                                        refwordnum = 1
                                        wordnum = 1
                                        for refword in refwords:
                                                
                                                while wordnum <= wordscount:
                                                        for word in words:
                                                                if word == refword:
                                                                        print(f'{word} matches {refword}')
                                                                
                                                                        if refwordnum == wordnum:
                                                                                print('Perfect match!')
                                                                        elif refwordnum > wordnum:
                                                                                print(f'previous {refword} added, {word} matches later {refword}')
                                                                        elif refwordnum < wordnum:
                                                                                print(f'previous {refword} omitted, {word} matches earlier {refword}')
                                                                        
                                                                else:
                                                                        print(f'{refword} not matched, checking next word')
                                                               
                                                                wordnum += 1

                                                refwordnum += 1

                        else:
                                print(f'The word counts are equal in line: {verselinenum}')     

        '''
                varline = line
                for word in words:
                        wordcount += 1
                        #print(f'linenum: {count}  wordnum: {wordcount}  word: {word}\n')
                        varfile = open("/home/max/Projects/BiblionOCR/Model/Data/csv/VariantText.csv")
                        
                        
                
                
                
                # Normalize ligatures in PUA and convert to lower case
                oldword = word
                with varfile:
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
                                #print(row[0],row[1])
                                cfind, creplace = (row[0], row[1])
                                nodiaword = oldword.replace(cfind, creplace)
                                if nodiaword != oldword:
                                        #print(f'linenum: {count}  wordnum: {wordcount}  word: {oldword} nodiaword: {nodiaword}')
                                        oldword=nodiaword
                diafile.close()
                
                # Replace final sigma
                lastchar = nodiaword[-1]
                if lastchar == "ς":
                        remsigma = nodiaword[:-1]
                        nodiaword = remsigma + "σ"  
                
                
                # Assign normalized line/verse
                normline = normline.replace(word,nodiaword)

        # Print and save normalized line/verse
        print(f'normalized line: {normline}')
        with open(normtxtpath, 'a') as normfile:
                normfile.write(normline)

        normfile.close()
        txtfile.close() '''  
