#print(len(locals()))

# Python imports

import time
import sys
import os
import cv2
import numpy as np
import shutil
import imutils
import re
from PIL import Image
#from tqdm import tqdm
# PyQt5 imports
'''
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
'''
from PyQt5 import QtCore as qtc
#print(len(locals()))

class PreProcess():  
    
    def pdfExtractPages(source, destination,firstpage,lastpage):

        args = [
        '-sDEVICE=pdfwrite', ' -dNOPAUSE', ' -dBATCH',
        ' -dSAFER', ' -dFirstPage=' + firstpage, ' -dLastPage=' + lastpage,
        ' -sOutputFile=' + destination + '1516_Page_' + firstpage + '-' + lastpage + '.pdf'
        ]
        gs_cmd = 'gs ' + ' '.join(args) +' '+ source
        os.system(gs_cmd)

    def pdf4tif(source, destination):
        #idx = destination.rindex('.')
        #destination = destination[:idx]
        args = [
        '-q', '-sDEVICE=tiff24nc',
        '-r300', '-sPAPERSIZE=letter', '-sCompression=lzw',
        '-o ' + destination + '1516_Page_%03d.tif'
        ]
        gs_cmd = 'gs ' + ' '.join(args) +' '+ source
        os.system(gs_cmd)
    
    def pdf2tif(source, destination, startpagenum):
        
        def sorted_alphanumeric(data):
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
            return sorted(data, key=alphanum_key)
            #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

        
        #dest_of_tiff = "/home/max/Projects/Python/Images/Source/pdf2tif/"
        #path_of_images = r"/home/max/Projects/Python/Images/Source/pdf4tif/"
        
        path_of_images = source
        dest_of_tiff = destination
        
        list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

        print(list_of_images)

        newpagenum = int(startpagenum)

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
                
            shutil.copy(path_of_images + filestr, dest_of_tiff + versionref + "_Page_" + pagenum + ".tif")
            
            newpagenum += 1

    def tiff2tiffidx(source, destination):
        start = time.perf_counter()
        #dest_of_images = "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/"
        #path_of_images = "/home/max/Projects/Python/Images/Source/pdf2tif/"

        path_of_images = source
        dest_of_images = destination
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
        
        finish = time.perf_counter()

        print(f'Finished in {round(finish - start, 2)} seconds(s)')

    def tiff2pngidx(source, destination):
        
        #path_of_png_images = "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/"
        #path_of_tif_bw_images = r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/"

        path_of_tif_bw_images = source
        path_of_png_images = destination
        list_of_images = os.listdir(path_of_tif_bw_images)

        for image in list_of_images:
            
            # Open the selected large .tif image. 
            bw_image = Image.open(os.path.join(path_of_tif_bw_images, image))
            
            # separate .tif extension for original filename
            filestr = os.path.basename(os.path.join(path_of_tif_bw_images, image))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            # Designate .png output path/filename
            outfile = path_of_png_images + filename + ".png"
            
            try:
                print("Generating: " + outfile)
                bw_image.save(outfile, "PNG", quality=100, dpi=(300,300))
            except Exception as e:
                print(e)

    def deskewfiles(source, pngdest, tifdest):
        
            # Calculate skew angle of an image
        def getSkewAngle(cvImage) -> float:
            # Prep image, copy, convert to gray scale, blur, and threshold
            newImage = cvImage.copy()
            gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (9, 9), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Apply dilate to merge text into meaningful lines/paragraphs.
            # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
            # But use smaller kernel on Y axis to separate between different blocks of text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
            dilate = cv2.dilate(thresh, kernel, iterations=5)

            # Find all contours
            dilated, contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key = cv2.contourArea, reverse = True)

            # Find largest contour and surround in min area box
            largestContour = contours[0]
            minAreaRect = cv2.minAreaRect(largestContour)

            # Determine the angle. Convert it to the value that was originally used to obtain skewed image
            angle = minAreaRect[-1]
            if angle < -45:
                angle = 90 + angle
            return -1.0 * angle

        # Rotate the image around its center
        def rotateImage(cvImage, angle: float):
            newImage = cvImage.copy()
            (h, w) = newImage.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return newImage

        # Deskew image
        def deskew(cvImage):
            angle = getSkewAngle(cvImage)
            # show the angle info
            print(filename + "[INFO] angle: {:.3f}".format(angle))
            return rotateImage(cvImage, -1.0 * angle)

        #dest_of_tif_images = "/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/"
        #dest_of_png_images = "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/"
        #path_of_images = "/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/"
        
        path_of_images = source
        dest_of_tif_images = tifdest
        dest_of_png_images = pngdest

        
        list_of_images = os.listdir(path_of_images)

        print(list_of_images)

        for img in list_of_images:
            
            filestr = os.path.basename(os.path.join(path_of_images, img))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            image = cv2.imread(os.path.join(path_of_images, img))

            #print(filename + "[INFO] angle: {:.3f}".format(angle))
            newImage = deskew(image)

            #write rotated file to destination folder
            PILimage = Image.fromarray(newImage)
            thresh = 127
            fn = lambda x : 255 if x > thresh else 0
            PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
            
            tif_outfile = dest_of_tif_images + filename + ".tif"
            png_outfile = dest_of_png_images + filename + ".png"
                
            try:
                print("Generating: " + tif_outfile)
                PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))
                
                print("Generating: " + png_outfile)
                PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
                #my_img_resized.save(outfile, "PNG")
            except Exception as e:
                print(e)

    def deskewimage(imgpath):
        
            # Calculate skew angle of an image
        def getSkewAngle(cvImage) -> float:
            # Prep image, copy, convert to gray scale, blur, and threshold
            newImage = cvImage.copy()
            gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (9, 9), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Apply dilate to merge text into meaningful lines/paragraphs.
            # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
            # But use smaller kernel on Y axis to separate between different blocks of text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
            dilate = cv2.dilate(thresh, kernel, iterations=5)

            # Find all contours
            dilated, contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key = cv2.contourArea, reverse = True)

            # Find largest contour and surround in min area box
            largestContour = contours[0]
            minAreaRect = cv2.minAreaRect(largestContour)

            # Determine the angle. Convert it to the value that was originally used to obtain skewed image
            angle = minAreaRect[-1]
            if angle < -45:
                angle = 90 + angle
            return -1.0 * angle

        # Rotate the image around its center
        def rotateImage(cvImage, angle: float):
            newImage = cvImage.copy()
            (h, w) = newImage.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return newImage

        # Deskew image
        def deskew(cvImage):
            angle = getSkewAngle(cvImage)
            # show the angle info
            print(filename + "[INFO] angle: {:.3f}".format(angle))
            return rotateImage(cvImage, -1.0 * angle)
           
        filestr = os.path.basename(imgpath)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        image = cv2.imread(imgpath)
        print("Converting image to cv2 image")
        newImage = deskew(image)

        #print(filename + "[INFO] angle: {:.3f}".format(angle))

        #write rotated file to destination folder
        PILimage = Image.fromarray(newImage)
        thresh = 127
        fn = lambda x : 255 if x > thresh else 0
        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
        
        outfile = imgpath
        print("Converting cv2 image to PIL image: " + outfile)
        #png_outfile = self.imgpath + self.ui.ImageLe.text()
            
        try:
            print("Generating: " + outfile)
            PIL_BWimage.save(outfile)
            
            #print("Generating: " + png_outfile)
            #PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
            #my_img_resized.save(outfile, "PNG")
        except Exception as e:
            print(e)

    def croplangs(source, boxdir, greekdir, latindir, elimdir):

        dest_of_elimination = elimdir
        dest_of_greek = greekdir
        dest_of_latin = latindir
        dest_of_box = boxdir
        path_of_images = source
        
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

    def resizepngs(source, destination):

        path_of_png_resized = destination
        path_of_png_deskew = source

        list_of_images = os.listdir(path_of_png_deskew)

        for image in list_of_images:
            
            # Open the selected large .tif image. 
            big_image = Image.open(os.path.join(path_of_png_deskew, image))
            
            # separate .tif extension for original filename
            filestr = os.path.basename(os.path.join(path_of_png_deskew, image))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            # Resize image to original proportions to maintain aspect ratio
            (width,height) = big_image.size
            aspect_ratio = ((width/height))
            print("Aspect Ratio: " + str(aspect_ratio))
            new_width = (width/4)
            new_height = (new_width/aspect_ratio)
            my_img_resized = big_image.resize((int(new_width), int(new_height))) 
            
            # Designate .jpg output path/filename
            outfile = path_of_png_resized + filename + ".png"
            
            try:
                print("Generating: " + outfile)
                my_img_resized.save(outfile, "PNG", quality=100)
            except Exception as e:
                print(e)