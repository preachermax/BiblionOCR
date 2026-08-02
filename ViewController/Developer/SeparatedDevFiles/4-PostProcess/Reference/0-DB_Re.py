import sqlite3
import re

conn = sqlite3.connect('/home/max/Projects/Python/SQLite/TR-Words_TW.db')
print ("Opened database successfully")

cursor = conn.cursor()

cursor.execute("SELECT * FROM Bible ")
               
'''#vlines = cursor.fetchone()
vlines = cursor.fetchall()

for vline in vlines:
    pattern = re.compile('(<wt>\w+)(<WG\d+>)(<W\w+-\w+?-?\w+?\s)(l=\w+>)([,.;])?')
    matches = pattern.finditer(str(vline))
    
    for match in matches:
        print(match)
    print(vline)'''




conn.commit()

conn.close()
