import os
import string
import re
from collections import defaultdict
from collections import OrderedDict
from operator import itemgetter
import csv

path_of_text = "/home/max/Projects/Python/EstablishTruth/Greek wordlist/"
path_of_textfile = path_of_text + "Erasmus1516NT_Lines.txt"

textfilestr = open(path_of_textfile).read()

strippedfile = textfilestr.translate({ord(c): "" for c in ",.;;"})

print(strippedfile)

word_counts = defaultdict(int)
row_list = []

with open(path_of_text + "Erasmus1516NT-stripped.txt", 'w') as file:
    file.write(strippedfile)
    file.close()

with open(path_of_text + "fegWordlistcount.txt", 'w', newline="") as file:
    writer = csv.writer(file, delimiter="\t")

    for w in open(path_of_text + "Erasmus1516NT-stripped.txt").read().split():
        word_counts[w] += 1
        row_list = [w,word_counts[w]]
        print(row_list)
        writer.writerow(row_list)
        
        
wordlist_int_sort = []

with open(path_of_text + "fegWordlistsort.txt", 'w', newline="") as file:
    writer = csv.writer(file, delimiter="\t")
    
    wordlist_csv = open(path_of_text + "fegWordlistcount.txt", 'r')
    wordlist_raw = csv.reader(wordlist_csv, delimiter="\t")
        
    for item in wordlist_raw:
        int_convert = [int(value) if idx == 1 else value for idx, value in enumerate(item)]
        wordlist_int_sort.append(int_convert) 
        wordlist_sorted = sorted(wordlist_int_sort, key=itemgetter(1), reverse=True)
    
    d = OrderedDict()
          
    for row in wordlist_sorted:
        word, wordcount = (row[0], row[1])
        d[word] = None
        print(word, "occurs", wordcount, "times")
        wordlist = [word,wordcount]
        writer.writerow(wordlist)
 
    with open(path_of_text + "fegWordlist.txt", 'w', newline="") as file:
        writer = csv.writer(file, delimiter="\t")   
        for k in d.keys():  
            striptabs = {k.translate({ord(c): "" for c in "\t"})}
            writer.writerow(striptabs)
        
        
        





