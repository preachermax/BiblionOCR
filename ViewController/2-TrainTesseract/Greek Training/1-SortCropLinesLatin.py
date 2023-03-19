import os
import cv2
import numpy as np
import imutils
from PIL import Image

dest_of_autosplit = "/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/"
dest_of_linebox = "/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/"
path_of_images = r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/"

list_of_images = os.listdir(path_of_images)

for image in list_of_images:
    
        img = cv2.imread(os.path.join(path_of_images, image))

        filestr = os.path.basename(os.path.join(path_of_images, image))
        
        filesplit = os.path.splitext(filestr)
        
        filename = filesplit[0]
        
        fileext = filesplit[1]

        #grayscale
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #cv2.imwrite(dest_of_test_images + filename + "_gray" + fileext,gray)
        #cv2.imshow('gray',gray)
        #cv2.waitKey(0)

        #binary 
        ret,binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)

        #binary inversion
        ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
        #cv2.imwrite(dest_of_test_images + filename + "_thresh" + fileext,thresh)
        #cv2.imshow('second',thresh)
        #cv2.waitKey(0)

        #dilation
        kernel = np.ones((5,195), np.uint8)
        img_dilation = cv2.dilate(thresh, kernel, iterations=1)
        #cv2.imwrite(dest_of_test_images + filename + "_dilation" + fileext,img_dilation)
        #cv2.imshow('dilated',img_dilation)
        #cv2.waitKey(0)

        #medianblur
        median = cv2.medianBlur(img_dilation, 13)
        #cv2.imwrite(dest_of_test_images + filename + "_blur" + fileext,median)
        #cv2.imshow('medianblur',median)
        #cv2.waitKey(0)

        #find contours
        im2,ctrs, hier = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        #set flags for sorting contours top to bottom
        reverse = False
        i = 1

        # construct the list of bounding boxes and sort them from top to bottom
        boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
        (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b:b[1][i], reverse=reverse))

        # Set initial box count
        bnum = 1

        for i,c in enumerate(ctrs):
        
                # Get bounding box
                x, y, w, h = cv2.boundingRect(c)

                # Set height validation of contour to eliminate unwanted boxes
                if h>120:
                        
                        # Getting ROI
                        roi = binary[y:y+h, x:x+w]
                        bnum += 1
                        cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                        
                        # Extract accepted line for ground truth text image
                        #cv2.imwrite(dest_of_groundtruth + filename + "_Line" + str(bnum) + fileext,roi)
                        #print("Extracting " + filename + " Line" + str(bnum))
                        PILimage = Image.fromarray(roi)
                        thresh = 127
                        fn = lambda x : 255 if x > thresh else 0
                        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                        tif_outfile = dest_of_autosplit + filename + "_Line" + str(bnum) + ".tif"
                        print("Generating: " + tif_outfile)
                        PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))
        
        # Write linebox image to file
        cv2.imwrite(dest_of_linebox + filename + "_linebox" + fileext,binary)
        #cv2.imshow("box image",image)
        #cv2.waitKey(0)
        #print("Writing "+filename+" Linebox Image")
        