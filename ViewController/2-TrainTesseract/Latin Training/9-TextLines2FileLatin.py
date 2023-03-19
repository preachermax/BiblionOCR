import os

dest_of_textlinefiles = "/home/max/Projects/Python/TextFiles/Greek/greek_book_40_Matthew/"
#dest_of_groundtruth = "/home/max/Projects/Python/GroundTruth/"
path_of_textfiles = r"/home/max/Projects/Python/TextFiles/Source/greek_book_40_Matthew/"

list_of_textfiles = os.listdir(path_of_textfiles)

for files in list_of_textfiles:
    
    textfile = open(os.path.join(path_of_textfiles, textfile))

    filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    
    fileext = filesplit[1]
    
    for cnt, line in enumerate(textfile):
        
        # open file to write line
        outF = open(dest_of_textlinefiles + filename + "_Line" + cnt + fileext, "w")
        # write line to output file
        outF.write(line)
        outF.write("\n")
        print("Line {}: {}".format(cnt, line))
        outF.close()
       