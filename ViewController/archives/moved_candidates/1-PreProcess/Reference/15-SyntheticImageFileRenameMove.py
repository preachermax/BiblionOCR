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

dest_of_groundtruth = "/home/max/Projects/Python/GroundTruthSynthetic/"
path_of_images = r"/home/max/Projects/Python/Images/GroundTruthSyntheticImages/"

list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

newlinenum = 1

for image in list_of_images:
    
    filestr = os.path.basename(os.path.join(path_of_images, image))
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    
    fileext = filesplit[1]
    
    shutil.move(path_of_images + filestr, dest_of_groundtruth + "greek_nt_Line_" + str(newlinenum) + fileext)
    
    newlinenum += 1 
        
