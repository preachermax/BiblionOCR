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

dest_of_tiff = "/home/max/Projects/Python/Images/Source/pdf2tif/"
path_of_images = r"/home/max/Projects/Python/Images/Source/pdf4tif/"


list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

#print(list_of_images)

newpagenum = 51

for image in list_of_images:
    
    img = cv2.imread(os.path.join(path_of_images, image))

    # height, width = img.shape[:2]
    
    filestr = os.path.basename(os.path.join(path_of_images, image))
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    
    fileext = filesplit[1]
    
    namesplit = filename.split("_")
    
    versionref = namesplit[0]
      
    oldpagenum = str(namesplit[2])
    
    pagenum = str(newpagenum).zfill(3)
    
    print("oldpagenum: " + oldpagenum + "  newpagenum: " + pagenum)
           
    shutil.move(path_of_images + filestr, dest_of_tiff + versionref + "_Page_" + pagenum + ".tif")
    
    newpagenum += 1