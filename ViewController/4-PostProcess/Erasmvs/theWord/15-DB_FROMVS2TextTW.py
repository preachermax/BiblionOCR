import sqlite3
import re

wordopen = "<wt>"
wordclose = ""
strongopen = "<WG"
strongclose = ">"
rmacopen = "<WT"
rmacclose = " "
lemmaopen = 'l="'
lemmaclose = "\">"
englishopen = ""
englishclose = ""

txtfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/TheWord/ERASMS1516.nt', 'w', encoding='utf-8-sig')
#txtfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/TheWord/ERASMS1516.nt', 'w')

conn_TW = sqlite3.connect('/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/FROMVS.db')
print ("Opened The FROMVS database successfully")

cursor_TW = conn_TW.cursor()

'''cursor_TW.execute("SELECT Line FROM Bible WHERE ID = (SELECT MAX(ID) FROM Bible)")
lines = cursor_TW.fetchone()
if lines:
    lastline = lines[0]
    #print(lastline)
else:'''

lastline = 7958

loopcount = 1

while loopcount <= lastline:
    cursor_TW.execute("SELECT Line,Word,WordPunc FROM Bible WHERE Line = " + str(loopcount))
    vwords = cursor_TW.fetchall()
    lineverse = ""
       
    for vword in vwords:
        if vword:
            linenum = vword[0]
            word = vword[1]
            punc = vword[2]

            # print(str(linenum) + " " + str(book) + " " + str(chpt) + ":" + str(vrse) + " " + str(word) + str(punc) + " " + str(strong) + " " + str(RMAC) + " " + str(english) + str(engpunc))
            #linegroup = str(book) + str(chpt) + ":" + str(vrse) + " "
            wordgroup = wordopen + str(word) + str(punc)
            
            lineverse = lineverse + wordgroup + " "
            lineverse = lineverse.replace('None','')
        else:
            lineverse = ""
        
    txtfile.write(lineverse + "\r\n")
    print(loopcount)
    print(lineverse + "\n")
    loopcount += 1

conn_TW.close()
txtfile.close()

# Append footer
footfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/TheWord/TW_footer.txt', 'r', encoding='utf-8-sig')
txtfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/TheWord/ERASMS1516.nt', 'a+', encoding='utf-8-sig')
#footfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/TheWord/TW_footer.txt', 'r')
#txtfile = open('/home/max/Projects/BiblionOCR/Model/Project/Text/TheWord/ERASMS1516.nt', 'a+')
footer = footfile.read()
print(footer)
txtfile.write(footer)
txtfile.close()
footfile.close()