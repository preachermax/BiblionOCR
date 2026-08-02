# import the necessary packages
import os
import numpy as np
import cv2

dest_of_images = "/home/max/Projects/Python/Images/tif_desk_latin/"
path_of_images = r"/home/max/Projects/Python/Images/tif_latin/"

list_of_images = os.listdir(path_of_images)
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
    
    invert = cv2.bitwise_not(gray)
    
    # convert grayscale to binary to be rotated later
    ret, binary = cv2.threshold(image,127,255,cv2.THRESH_BINARY)
 
    # threshold the image, setting all foreground pixels to
    # 255 and all background pixels to 0
    thresh = cv2.threshold(invert, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # grab the (x, y) coordinates of all pixel values that
    # are greater than zero, then use these coordinates to
    # compute a rotated bounding box that contains all
    # coordinates
    coords = np.column_stack(np.where(thresh>0))
    

    # the `cv2.minAreaRect` function returns values in the
    angle = cv2.minAreaRect(coords)[-1]
    # range [-90, 0); as the rectangle rotates clockwise the
    # returned angle trends to 0 -- in this special case we
    # need to add 90 degrees to the angle   
    if angle < -45:
        angle = -(90 + angle)

    # otherwise, just take the inverse of the angle to make
    # it positive
    else:
        angle = -angle

    # rotate the image to deskew it
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # draw the correction angle on the image so we can validate it
    #cv2.putText(rotated, "Angle: {:.2f} degrees".format(angle), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # show the angle info
    print(filename + "[INFO] angle: {:.3f}".format(angle))

    
    #cv2.imshow("Input", image)
    #cv2.imshow("Rotated", rotated)

    #write rotated file to destination folder
    cv2.imwrite(os.path.join(dest_of_images, filename),rotated)

