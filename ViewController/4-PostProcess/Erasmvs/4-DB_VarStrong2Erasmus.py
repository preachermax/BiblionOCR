from SqliteHelper import *


helper = SqliteHelper('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
#helper = SqliteHelper("/home/max/Projects/Python/SQLite/TRiBibleWords.db")

query = '''SELECT Line,WordNum,NoDiaWord,VarWord,Strong,RMAC,Lemma,VarCode FROM Variants WHERE Preserved = "1"'''
variants = helper.select(query)

for variant in variants:
    if variant[2]:    
        
        line = variant[0]
        wordnum = variant[1]
        nodiaword = variant[2]
        varword = variant[3]
        strong = variant[4]
        rmac = variant[5]
        lemma = variant[6]
        varcode = variant[7]
    

        '''englishquery = "SELECT English FROM IntBibleWords WHERE Line = ? AND NoDiaWord = ?"
        engdata = (line,varword)
        english = helper.selectone(englishquery,engdata)
        if englishtup:
            #try:
            
            for val in englishtup:
                if len(val)>0:
                    english = val
            #except:
            else:
                english = ""
            
        english = ''.join(englishtup)

        if str(english) == "None":
        english = ""'''
        
        #print(line,"\t",varword,"\t",strong,"\t",rmac,"\t",lemma,"\t",english,"\t",varcode)
        print(line,"\t",varword,"\t",strong,"\t",rmac,"\t",lemma,"\t",varcode)
        
        query = """UPDATE Bible SET VarWord = ?,Strong = ?,RMAC = ?,Lemma = ?,VarCode = ?  WHERE Line = ? and NoDiaWord = ? and Strong IS NULL"""
        data = (varword,strong,rmac,lemma,varcode,line,nodiaword)
        #data = (varword,strong,rmac,lemma,english,varcode,line,nodiaword)
        helper.update(query,data)
