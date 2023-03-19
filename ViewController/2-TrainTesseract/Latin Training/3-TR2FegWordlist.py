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
#print(wordfilestr)


with open(path_of_ligfile, 'r', encoding="utf-8") as ligreplacelist_csv:
    ligatureline = csv.DictReader(ligreplacelist_csv, delimiter="\t")
    #print(ligatureline)    
    for line in ligatureline:
        # print(line['Find'], line['Replace'])
        # rtype = line['Type']
        chrfind = line['Find']
        ligsub = line['Replace']
                                
        with open(path_of_newwordfile + "TR2FegOldWordlist.txt", 'r') as oldwordfile:
            for oldwords in oldwordfile:
                oldwordlist = oldwords
                #print(oldwordlist)
                with open(path_of_newwordfile + "TR2FegNewWordlist.txt", 'a+') as newwordfile:
                    # writer = csv.writer(newwordfile)
                    chrsub = re.compile('[' + chrfind + ']')
                    newword = chrsub.sub(ligsub,str(oldwords))
                    # print(newword)
                    newwordfile.write(newword)
                    '''if newword:
                        wordfind = re.compile('[' + newword + ']')
                        wordexists = wordfind.findall(oldwordlist)
                        if not wordexists:
                            print(newword)
                            #newwordfile.write(newword + "\n")

        with open(path_of_newwordfile + "TR2FegNewWordlist.txt", 'r') as newwordfile:
            newfiledata = newwordfile.read()

        with open(path_of_newwordfile + "TR2FegOldWordlist.txt", "w") as oldwordfile:
            oldwordfile.write(newfiledata)'''

#ligreplacelist_csv.close()
#newwordfile.close()
#oldwordfile.close() 

#d = OrderedDict()
#with open(path_of_newwordfile + "TR2FegWordlist.txt", 'w', newline="") as file:
    #writer = csv.writer(file)   
    #for k in d.keys():  
        #stripchrs = {k.translate({ord(c): "" for c in "[,']"})}
        #writer.writerow(stripchrs)'''