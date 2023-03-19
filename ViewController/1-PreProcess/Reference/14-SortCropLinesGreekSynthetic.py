import os
import cv2
import numpy as np
import imutils
import shutil
import re

def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)-([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)
    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

#dest_of_test_images = "/home/max/Projects/Python/Images/GreekSyntheticTesting/"
dest_of_groundtruth = "/home/max/Projects/Python/Images/GroundTruthSyntheticImages/"
dest_of_linebox = "/home/max/Projects/Python/Images/GroundTruthSyntheticLineBox/"
path_of_images = r"/home/max/Projects/Python/Images/GreekSyntheticDeskewed/"

list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

bnum=1

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
        kernel = np.ones((5,193), np.uint8)
        img_dilation = cv2.dilate(thresh, kernel, iterations=1)
        #cv2.imwrite(dest_of_test_images + filename + "_dilation" + fileext,img_dilation)
        #cv2.imshow('dilated',img_dilation)
        #cv2.waitKey(0)

        #medianblur
        median = cv2.medianBlur(img_dilation, 7)
        #cv2.imwrite(dest_of_test_images + filename + "_blur" + fileext,median)
        #cv2.imshow('medianblur',median)
        #cv2.waitKey(0)

        #find contours
        im2,ctrs, hier = cv2.findContours(img_dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        
        #set flags for sorting contours top to bottom
        reverse = False
        i = 1

        # construct the list of bounding boxes and sort them from top to bottom
        boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
        (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b:b[1][i], reverse=reverse))

        # Set initial box count
        # bnum = 1

        for i,c in enumerate(ctrs):
        
                # Get bounding box
                x, y, w, h = cv2.boundingRect(c)

                # Set width validation of contour to eliminate unwanted boxes
                if w>500:
                
                        # Getting ROI
                        roi = binary[y:y+h, x:x+w]
                        cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                                
                        # Extract accepted line for ground truth text image
                        cv2.imwrite(dest_of_groundtruth + "greek_nt_Line_" + str(bnum) + fileext,roi)
                        print("Extracting " + "greek_nt_Line_" + str(bnum))
                        bnum += 1

        # Write linebox image to file
        cv2.imwrite(dest_of_linebox + filename + "_linebox" + fileext,binary)
        #cv2.imshow("box image",image)
        #cv2.waitKey(0)

        #print("Writing "+filename+" Linebox Image")