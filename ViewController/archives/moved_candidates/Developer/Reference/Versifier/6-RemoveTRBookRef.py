import os
import string
import re
from collections import defaultdict
from collections import OrderedDict
from operator import itemgetter
import csv

path_of_text = "/home/max/Projects/Python/EstablishTruth/Greek completed text/Erasmus1516NT_Verses.txt"
path_of_textfile = "/home/max/Projects/Python/EstablishTruth/Greek completed text/Erasmus1516NT_Lines.txt"

#textfilestr = open(path_of_textfile).read()

# bookmatch = bookref.finditer(textfilestr)
    # for match in bookmatch:
        #print(match.group())

textfilestr = open(path_of_text, 'r')
newfile = open(path_of_textfile, 'w')
 
for line in textfilestr.readlines():
    linesub = re.sub('[\\w]{3}[\\s]{1}[\\d]{1,2}[:]{1}[\\d]{1,2}[\\s]{1}','',line)
    print(linesub)
    newfile.write(linesub)
    
    
    # bookref = re.compile('[\\w]{3}[\\s]{1}[\\d]{1,2}[:]{1}[\\d]{1,2}[\\s]{1}')
    # bookmatch = bookref.match(line)
    # if bookmatch != 'None':
    # if bookmatch:
        # print(bookmatch.group())
    

# strippedfile = textfilestr.translate({ord(c): "" for c in ",.;;"})
#print(strippedfile)

newfile.close()
textfilestr.close()