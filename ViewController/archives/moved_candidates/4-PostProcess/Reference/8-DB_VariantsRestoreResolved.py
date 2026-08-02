import sqlite3
import re

conn_TR = sqlite3.connect('/home/max/Projects/Python/SQLite/FROMVS.db')
print ("Opened the database successfully")

cursor_TR = conn_TR.cursor()

cursor_TR.execute('''SELECT * FROM Resolved''')

#vlines = cursor_TR.fetchone()
#vlines = cursor_TR.fetchmany(0)
vlines = cursor_TR.fetchall()

for vline in vlines:
    line = vline[1]
    book = vline[2]
    chapter = vline[3]
    verse = vline[4]
    wordnum = vline[5]
    word = vline[6]
    nodiaWord = vline[7]
    varword = vline[8]
    strong = vline[9]
    rmac = vline[10]
    lemma = vline[11]
    varform = vline[12]
    vartype = vline[13]
    impactcode = vline[14]
    errorcode = vline[15]
    varcode = vline[16]
    desc = vline[17]
    preserved = vline[18]
    corrected = vline[19]
    error = vline[20]
    variance = vline[21]
    context = vline[22]
    inflection = vline[23]
    resolved = vline[24]

    
    #cursor_TR.execute("SELECT * FROM Resolved")
    insert_parameters = """UPDATE Variants SET Line = ?,Book = ?,Chapter = ?,Verse = ?,WordNum = ?,Word = ?,NoDiaWord = ?,VarWord = ?,
                            Strong = ?,RMAC = ?,Lemma = ?,VarianceForm = ?,VarianceType = ?,ImpactCode = ?,ErrorCode = ?,VarCode = ?,Description = ?,
                            Preserved = ?,Corrected = ?,Error = ?,Variance = ?,Context = ?,Inflection = ?, Resolved = ?
                            WHERE Line = ? and WordNum = ? and Strong IS NULL"""
    insert_data = (line,book,chapter,verse,wordnum,word,nodiaWord,varword,strong,rmac,lemma,varform,vartype,impactcode,errorcode,varcode,desc,preserved,corrected,error,variance,context,inflection,resolved,line,wordnum)

    cursor_TR.execute(insert_parameters,insert_data)
    conn_TR.commit()
    print(line,"\t",book,"\t",chapter,"\t",verse,"\t",wordnum,"\t",word,"\t",nodiaWord,"\t",varword,"\t",strong)
conn_TR.close()