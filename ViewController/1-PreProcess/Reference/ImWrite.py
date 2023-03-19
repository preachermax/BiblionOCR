# import the necessary packages
import os
import numpy as np
import cv2

dest_of_images = "/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/"
#path_of_images = r"/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/"
path_of_images = "/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/"

list_of_images = os.listdir(path_of_images)

#print(list_of_images)

for img in list_of_images:
    
    image = cv2.imread(os.path.join(path_of_images, img))
    print(image.shape)
    height = int(image.shape[0]/4.166667)
    width = int(image.shape[1]/4.166667)
    dim = (width,height)
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_LINEAR)
    print(resized.shape)
    
    #cv2.imshow("image",image)
    cv2.imshow("resized",resized)
    cv2.waitKey(0)
    
    filename = os.path.basename(os.path.join(path_of_images, img))
    
    cv2.imwrite(os.path.join(dest_of_images, filename), resized)
    
 
 
    #cv2.imwrite(os.path.join(dest_of_images, filename), image)