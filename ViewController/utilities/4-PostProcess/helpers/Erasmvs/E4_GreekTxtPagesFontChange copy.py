import os
import csv
import tempfile

#dest_of_textiles = "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"
#dest_of_groundtruth = "/home/max/Projects/Python/GroundTruth/"
path_of_textfiles = r"/home/max/Projects/Python/FontChange/Greek txt pages/greek_book_40_Matthew/"

list_of_textfiles = os.listdir(path_of_textfiles)

for tfile in list_of_textfiles:

    #Create temporary file read/write
    t = tempfile.NamedTemporaryFile(mode="r+")

    #Open input file read-only
    i = open(path_of_textfiles + tfile, 'r')

    #Copy input file to temporary file, modifying as we go
    for line in i:
        print(line.rstrip()+"\n")
        t.write(line.rstrip()+"\n")

    i.close() #Close input file

    t.seek(0) #Rewind temporary file to beginning

    o = open(path_of_textfiles + tfile, "w")  #Reopen input file writable
    #txtfile = open('/home/max/Projects/Python/FontChange/Greek completed text/Erasmus1516NT_Verses.txt')


    # Open ERASMVS swap file 
    #fontswapfile = open('/home/max/Projects/Python/FontChange/ERASMVS_PUA_norm.csv')
    #csv_f = csv.reader(fontswapfile, delimiter = "\t")
    #print(csv_f)


    for row in t:
        textline = row
        #print(textline)
        fontswapfile = open('/home/max/Projects/Python/FontChange/ERASMVS_PUA_norm.csv')
        csv_f = csv.reader(fontswapfile, delimiter = "\t")
        for swap in csv_f:
            cfind = swap[2]
            creplace = swap[4]
            print(cfind,"\t",creplace)
            textline = textline.replace(cfind,creplace)
        o.write(textline)
        print(textline)
        fontswapfile.close()

        #txtfile.close()

        
 # Cleanup         
t.close()
o.close()
#txtfile.close()
fontswapfile.close()      
 