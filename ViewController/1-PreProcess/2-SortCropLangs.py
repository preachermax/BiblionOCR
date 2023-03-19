import os
import cv2
import numpy as np
import imutils
from PIL import Image

dest_of_elimination = "/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_40_Matthew/"
dest_of_greek = "/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/"
dest_of_latin = "/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_40_Matthew/"
dest_of_box = "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_40_Matthew/"
path_of_images = r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/"
#note-for checking missing languages after run
#path_of_images = r"/home/max/Projects/Python/Images/Source/tif_binary_check/"

list_of_images = os.listdir(path_of_images)
for image in list_of_images:
    
        img = cv2.imread(os.path.join(path_of_images, image))

        filestr = os.path.basename(os.path.join(path_of_images, image))
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        #filename = os.path.basename(os.path.join(path_of_images, image))
#load the image
#image = cv2.imread(args["image"])
#image = cv2.imread("./Images/tif_newtest/1516_Page_002.tif")
#cv2.imshow('orig',image)
#cv2.waitKey(0)

#grayscale
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
#cv2.imshow('gray',gray)
#cv2.waitKey(0)read 

#binary 
        ret,binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)

#binary inversion
        ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
#cv2.imshow('thresh',thresh)
#cv2.waitKey(0)

#dilation
        kernel = np.ones((70,100), np.uint8)
        img_dilation = cv2.dilate(thresh, kernel, iterations=1)
#cv2.imshow('dilated',img_dilation)
        #cv2.imwrite((image+'dilation.tif'),img_dilation)
#cv2.waitKey(0)

#medianblur
        #median = cv2.medianBlur(img_dilation, 17)
#cv2.imshow('medianblur',median)
#cv2.imwrite('medianblur.tif',median)
#cv2.waitKey(0)

#find contours
        im2,ctrs, hier = cv2.findContours(img_dilation.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#set flags for sorting contours top to bottom
        reverse = False
        i = 0

# construct the list of bounding boxes and sort them from left to right
        boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
        (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes), key=lambda b:b[1][i], reverse=reverse))

# Set initial box count
        bnum = 1
        destfolder = ""
        deststr = ""

        for i,c in enumerate(ctrs):
           
                # Get bounding box
                x, y, w, h = cv2.boundingRect(c)
                
                # Get ROI
                roi = binary[y:y+h, x:x+w]
                
                # Set height validation of contour to eliminate unwanted ROI's
                if w > 1600 and h > 4000:
                                                
                        if bnum==1:
                                destfolder = dest_of_greek
                                deststr = 'greek'
                                bnum = bnum + 1
                        else:
                                destfolder = dest_of_latin
                                deststr = 'latin'
                                bnum = 1

                        if destfolder!="":
                                # Write accepted ROI to correct folder/file
                                PILimage = Image.fromarray(roi)
                                thresh = 127
                                fn = lambda x : 255 if x > thresh else 0
                                PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                                outfile = destfolder+deststr+filename + ".tif"
                                print("Generating: " + outfile)
                                PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))
                                
                                #cv2.imwrite(destfolder+deststr+filename, roi)
                                # Draw box around accepted ROI
                                cv2.rectangle(binary,(x,y),( x + w, y + h ),(90,0,255),2)
                        else:
                                pass
                else:
                        # Eliminate smaller ROI as noise but save to eliminated folder/file anyway
                        cv2.imwrite(dest_of_elimination + filename + "segment-" + str(i) + fileext, roi)
                
        cv2.imwrite(os.path.join(dest_of_box, filename + fileext),binary)