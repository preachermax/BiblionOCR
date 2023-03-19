import os

dest_of_textlinefiles = "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"
#dest_of_groundtruth = "/home/max/Projects/Python/GroundTruth/"
path_of_textfiles = r"/home/max/Projects/Python/EstablishTruth/Greek txt4linesplit/"

list_of_textfiles = os.listdir(path_of_textfiles)

for tfile in list_of_textfiles:
    
    textfile = open(path_of_textfiles + tfile)

    filestr = os.path.basename(path_of_textfiles + tfile)
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    
    fileext = filesplit[1]
    
    for cnt, line in enumerate(textfile):
        
        # open file to write line
        outF = open(dest_of_textlinefiles + "greek" + filename + "_Line" + str(cnt + 1) + ".gt" + fileext, "w")
        # write line to output file
        outF.write(line)
        outF.write("\n")
        print("Line {}: {}".format(cnt, line))
        outF.close()
       