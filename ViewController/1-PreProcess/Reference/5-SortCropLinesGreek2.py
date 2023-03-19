import os
import cv2
import numpy as np
import imutils
import re

path_of_images = r"/home/max/Projects/Python/Images/Greek/tif_greek_groundcheck/"

list_of_images = os.listdir(path_of_images)

for image in list_of_images:
    
        img = cv2.imread(os.path.join(path_of_images, image))

        height, width = img.shape[:2]
        
        filestr = os.path.basename(os.path.join(path_of_images, image))
        
        filesplit = os.path.splitext(filestr)
        
        filename = filesplit[0]
        
        fileext = filesplit[1]
        
        namesplit = filename.split("_")
        
        versionref = namesplit[0]
        
        pagenum = namesplit[2]
        
        linestr = namesplit[3]
        #print(versionref,pagenum,linestr)
        
        linenum = re.match('.*?([0-9]+)$', linestr).group(1)
        #print("Last digits of "+filename+" are "+last_digits)
        
        if height > 200:
        
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
                kernel = np.ones((5,125), np.uint8)
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
                        if h>100:
                                
                                # Getting ROI
                                roi = binary[y:y+h, x:x+w]
                                bnum += 1
                                cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                                
                                # Extract accepted line for ground truth text image
                                cv2.imwrite(path_of_images + filename + "_Line" + linenum + "_" + str(bnum) + fileext,roi)
                #print("Extracting " + filename + " Line" + str(bnum))
                os.remove(path_of_images + image)    
