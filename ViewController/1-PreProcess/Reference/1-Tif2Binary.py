import os
import cv2

dest_of_images = "/home/max/Projects/Python/Images/Source/tif_binary/source_book_44_Acts/"
path_of_images = r"/home/max/Projects/Python/Images/Source/tif_batch/"

list_of_images = os.listdir(path_of_images)
for image in list_of_images:
    
    img = cv2.imread(os.path.join(path_of_images, image))
    
    filename = os.path.basename(os.path.join(path_of_images, image))
    
    #convert image to grayscale
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray',gray)
    #cv2.waitKey(0)

    #convert grayscale to binary
    ret,binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
    
    #write binary file to destination folder
    cv2.imwrite(os.path.join(dest_of_images, filename),binary)
