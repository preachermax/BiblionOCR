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

dest_of_groundtruth = "/home/max/Projects/BiblionOCR/Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth/"
#path_of_images = r"/home/max/Projects/BiblionOCR/Model/Project/Images/Workflow/Greek/TEMP/"
path_of_images = r"/home/max/Projects/BiblionOCR/Model/Project/Images/Workflow/Greek/tif_greek_lines_renamed/"

#sorted(os.listdir(os.getcwd()), key=len) does not work

list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

#print(list_of_images)

newpagenum = 1
newlinenum = 1

for image in list_of_images:
    
    img = cv2.imread(os.path.join(path_of_images, image))

    height, width = img.shape[:2]
    
    filestr = os.path.basename(os.path.join(path_of_images, image))
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    
    fileext = filesplit[1]
    
    namesplit = filename.split("_")
    
    versionref = namesplit[0]
    
    pagestr = namesplit[2]
    
    pagenum = int(pagestr)
    
    linestr = namesplit[3]
    #print(versionref,pagenum,linestr)
    
    linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
    #print("Last digits of "+filename+" are "+last_digits)
    
    if pagenum > newpagenum:
        
        newlinenum = 1
        
        newpagenum = pagenum
    
    print("pagenum: " + pagestr + "  newpagenum: " + str(newpagenum) + "  linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
           
    shutil.move(path_of_images + filestr, dest_of_groundtruth + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + ".gt" + fileext)
    
    newlinenum += 1 
        #print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))   
