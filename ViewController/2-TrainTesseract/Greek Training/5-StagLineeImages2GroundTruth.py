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
dest_of_groundtruth =r"/home/max/Projects/BiblionOCR/Model/Project/Images/Workflow/Greek/tif_greek_lines_2groundtruth/"
path_of_images = r"/home/max/Projects/BiblionOCR/Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth (copy)/"
#dest_of_groundtruth = "/home/max/Projects/Python/Images/Greek/tif_greek_tif2groundtruth/"
#path_of_images = r"/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/"
#dest_of_groundtruth = "/home/max/Projects/Python/Images/Greek/png_greek_png4groundtruth/"
#path_of_images = r"/home/max/Projects/Python/Images/Greek/png_greek_png2groundtruth/"

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

    # with prefix    
    '''fontname = namesplit[0] + "_" + namesplit[1] + "_"
    versionref = namesplit[2]
    pagestr = namesplit[4]
    linestr = namesplit[5]'''

    # without prefix
    fontname = "FROMVS_Regular_"
    versionref = namesplit[0]
    print(versionref)
    pagestr = namesplit[2]
    print(pagestr)
    linestr = namesplit[3]
    linestr = linestr.replace("Line","")
    linestr = linestr.replace(".gt","")
    print(linestr)
    linenum = int(linestr)
    print(linenum)
    pagenum = int(pagestr)
    
    #print(versionref,pagenum,linestr)
    
    #linenum = int(re.match('.*?([0-9]+)$', linestr))
    #print("Last digits of "+filename+" are "+last_digits)
    
    if pagenum > newpagenum:
        
        newlinenum = 1
        
        newpagenum = pagenum
    
    print("pagenum: " + pagestr + "  newpagenum: " + str(newpagenum) + "  linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
         
    shutil.move(path_of_images + filestr, dest_of_groundtruth + fontname + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)
    
    newlinenum += 1 
        #print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))  
