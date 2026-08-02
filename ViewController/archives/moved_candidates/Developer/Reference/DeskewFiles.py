# import the necessary packages
import os
import numpy as np
import cv2
from PIL import Image

class DeskewFileList():

    # Deskew images in folder
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