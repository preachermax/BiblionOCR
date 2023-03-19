# import the necessary packages
import os
import numpy as np
import cv2
from PIL import Image

dest_of_images = "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/"
path_of_images = "/home/max/Projects/Python/Images/Source/pdf2tif/"

list_of_images = os.listdir(path_of_images)

#print(list_of_images)

for img in list_of_images:
    
    filestr = os.path.basename(os.path.join(path_of_images, img))
    filesplit = os.path.splitext(filestr)
    filename = filesplit[0]
    fileext = filesplit[1]
    
    image = cv2.imread(os.path.join(path_of_images, img))
    
    
    #filename = os.path.basename(os.path.join(path_of_images, img))
    #print(filename)

    # convert the image to grayscale and flip the foreground
    # and background to ensure foreground is now "white" and
    # the background is "black"
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    
    #convert grayscale to binary to be rotated later
    ret, binary = cv2.threshold(image,127,255,cv2.THRESH_BINARY)
 
    PILimage = Image.fromarray(binary)
    thresh = 127
    fn = lambda x : 255 if x > thresh else 0
    PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
    
    outfile = dest_of_images + filename + ".tif"
        
    try:
        print("Generating: " + outfile)
        PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))
    except Exception as e:
        print(e)