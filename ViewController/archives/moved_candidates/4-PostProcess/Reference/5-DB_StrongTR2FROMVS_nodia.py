import sqlite3

conn_TW = sqlite3.connect('/home/max/Projects/Python/SQLite/TRa-Words_FROMVS.db')
print ("Opened TheWord database successfully")
cursor_TW = conn_TW.cursor()
cursor_TW.execute('''SELECT f.ID, f.Line, f.WordNum, f.Word, f.NoDiaWord, f.Strong, t.Strong, t.RMAC, t.NoDiaLemma, t.NoDiaWord, t.Word, t.WordNum
FROM Bible as f
LEFT JOIN TRaBible as t
ON f.Line == t.Line AND f.NoDiaWord LIKE t.NoDiaWord''')
wlines = cursor_TW.fetchall()
frlist = []
 
for wline in wlines:
        id = wline[0]
        fword = wline[3]
        fstrong = wline[5]
        tstrong = wline[6]
        tword = wline[10]
        
        if fstrong != tstrong:
            print(tword," ",tstrong," ",fword," ", fstrong)
        
            # update database
            sql_qry = '''UPDATE Bible SET Strong = ? WHERE ID = ?'''
            data = (tstrong, id)
            cursor_TW.execute(sql_qry, data)
            conn_TW.commit()
        fstrong = tstrong     

conn_TW.commit()
conn_TW.close()