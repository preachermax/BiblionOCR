import os
import cv2
import numpy as np
import shutil
import re

def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)
    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

dest_of_groundtruth = "/home/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/"
path_of_textfiles = r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"

font_name = "FROMVS_Regular_"

#sorted(os.listdir(os.getcwd()), key=len) does not work

list_of_textfiles = sorted_alphanumeric(os.listdir(path_of_textfiles))

for textfile in list_of_textfiles:
    
    #img = cv2.imread(os.path.join(path_of_images, image))

    #height, width = img.shape[:2]
    
    filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    
    fileext = filesplit[1]
    
    namesplit = filename.split("_")
    
    versionref = namesplit[0]
    
    pagestr = namesplit[2]
    
    pagenum = int(pagestr)
    
    linestr = namesplit[3]
    
    print(font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext)
           
    shutil.move(path_of_textfiles + filestr, dest_of_groundtruth + font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext)  
