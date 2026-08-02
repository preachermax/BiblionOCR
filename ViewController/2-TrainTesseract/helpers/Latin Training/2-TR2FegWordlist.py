import os
import string
import re
from collections import defaultdict
from collections import OrderedDict
from operator import itemgetter
import csv

path_of_text = "/home/max/Projects/Python/EstablishTruth/TR/"
path_of_lig = "/home/max/Projects/Python/EstablishTruth/Greek ligatures/"
path_of_newwordfile = "/home/max/Projects/Python/EstablishTruth/Greek wordlist/"

path_of_wordfile = path_of_text + "TR2Wordlist.txt"
path_of_ligfile = path_of_lig + "LigReplaceList.csv"

wordfilestr = open(path_of_wordfile).read()

with open(path_of_newwordfile + "TR2FegWordlist.txt", 'w') as newwordfile:
       
    ligreplacelist_csv = open(path_of_ligfile, 'r')
    ligatureline = csv.reader(ligreplacelist_csv, delimiter="\t")
        
    for line in ligatureline:
        rtype = str(itemgetter(0))
        chrfind = str(itemgetter(1))
        ligsub = str(itemgetter(2))
        
    with open(path_of_wordfile, newline='') as oldwordfile:
        reader = csv.reader(oldwordfile)
        curwordlist = list(reader)  
        #oldwordlist = curwordlist
        
        for word in curwordlist:
            chrsub = re.compile('[' + chrfind + ']')
            wordsub = chrsub.sub(ligsub,str(word))
            # print(wordsub)
            if wordsub:
                wordfind = re.compile('[' + wordsub + ']')
                wordexists = wordfind.findall(wordfilestr)
                if not wordexists:
                    newwordfile.write(wordsub)
 
ligreplacelist_csv.close()
newwordfile.close()
oldwordfile.close()