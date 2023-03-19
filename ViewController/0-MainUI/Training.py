#print(len(locals()))

# Python imports
import sys
import os
import cv2
import numpy as np
import shutil
import imutils
import re
from PIL import Image
# PyQt5 imports
'''
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
'''

#print(len(locals()))

class Train():
    
        def sortcroplines(source, linebox, splitdir):
                dest_of_autosplit = splitdir
                dest_of_linebox = linebox
                path_of_images = source

                list_of_images = os.listdir(path_of_images)

                def saveline(roi,bnum):
                        PILimage = Image.fromarray(roi)
                        thresh = 127
                        fn = lambda x : 255 if x > thresh else 0
                        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                        tif_outfile = dest_of_autosplit + filename + "_Line" + str(bnum) + ".tif"
                        print("Generating: " + tif_outfile)
                        PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))

                def removeworkflow(source):
                        shutil.remove(source)
                
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
                                dividers = int(round(h/150))
                                print("countour height = " + str(h) + "\t" + "number of boxes = " + str(dividers))
                                # Set height validation of contour to eliminate unwanted boxes
                                if h>120 and h<200:
                                        roi = binary[y:y+h, x:x+w]
                                        cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                                        bnum += 1
                                        saveline(roi,bnum)
                                        
                                # Set height of multi-line contours and subdivide proportionally
                                elif h > 200:
                                        h = int(round(h/dividers))
                                        for subdiv in range(0,dividers):
                                                print('subloopcount =' + str(subdiv))
                                                roi = binary[y:y+h, x:x+w]
                                                cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                                                bnum += 1
                                                y = y + h
                                                saveline(roi,bnum)
                                                
                        
                        # Write linebox image to file
                        cv2.imwrite(dest_of_linebox + filename + "_linebox" + fileext,binary)
                        
                        #cv2.imshow("box image",image)
                        #cv2.waitKey(0)
                        #print("Writing "+filename+" Linebox Image")
        
        def renameimages(source, destination):
                def sorted_alphanumeric(data):
                        convert = lambda text: int(text) if text.isdigit() else text.lower()
                        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                        return sorted(data, key=alphanum_key)
                        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

                path_of_images = source
                dest_of_images = destination
                #sorted(os.listdir(os.getcwd()), key=len) does not work

                list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

                print(list_of_images)

                newpagenum = 1
                newlinenum = 1

                for image in list_of_images:
                
                        img = cv2.imread(os.path.join(path_of_images, image))

                        height, width = img.shape[:2]
                        
                        filestr = os.path.basename(os.path.join(path_of_images, image))
                        
                        filesplit = os.path.splitext(filestr)
                        
                        filename = filesplit[0]
                        
                        fileext = filesplit[1]
                        
                        namesplit = filename.split("_")
                       
                        
                        versionref = namesplit[0]
                        
                        pagestr = namesplit[2]
                        
                        pagenum = int(pagestr)
                        
                        linestr = namesplit[3]
                        #print(versionref,pagenum,linestr)
                        print(f"namesplit: {namesplit} versionref: {versionref} pagestr: {pagestr} pagenum: {pagenum} linestr: {linestr}")
                        linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
                        #print("Last digits of "+filename+" are "+last_digits)
                        
                        if pagenum > newpagenum:
                                
                                newlinenum = 1
                                
                                newpagenum = pagenum
                        
                        
                        print(versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)

                        shutil.copy(path_of_images + filestr, dest_of_images + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)
                        
                        newlinenum += 1 
                        print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))

        def renumberimages(source, destination, startpage, endpage):
                def sorted_alphanumeric(data):
                        convert = lambda text: int(text) if text.isdigit() else text.lower()
                        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                        return sorted(data, key=alphanum_key)
                        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

                path_of_images = source
                dest_of_images = destination
                start_page = int(startpage)
                if endpage:
                        end_page = int(endpage)
                else:
                        end_page = ''
                #sorted(os.listdir(os.getcwd()), key=len) does not work

                list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

                print(list_of_images)

                newpagenum = 1
                newlinenum = 1

                for image in list_of_images:
                
                        img = cv2.imread(os.path.join(path_of_images, image))

                        height, width = img.shape[:2]
                        
                        filestr = os.path.basename(os.path.join(path_of_images, image))
                        
                        filesplit = os.path.splitext(filestr)
                        
                        filename = filesplit[0]
                        
                        fileext = filesplit[1]
                        
                        namesplit = filename.split("_")
                       
                        versionref = namesplit[0]
                        
                        pagestr = namesplit[2]
                        
                        pagenum = int(pagestr)

                        if end_page != "":
                                limit_page = end_page
                        else:
                                limit_page = 1000
                        
                        if pagenum >= start_page and pagenum <= limit_page:
                                linestr = namesplit[3]
                                #print(versionref,pagenum,linestr)
                                print(f"namesplit: {namesplit} versionref: {versionref} pagestr: {pagestr} pagenum: {pagenum} linestr: {linestr}")
                                linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
                                #print("Last digits of "+filename+" are "+last_digits)
                                
                                if pagenum > newpagenum:
                                        
                                        newlinenum = 1
                                        
                                        newpagenum = pagenum
                                
                                print(versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)

                                shutil.copy(path_of_images + filestr, dest_of_images + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)
                                
                                newlinenum += 1 
                                print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum)) 

        def stageimages(source, destination):
                def sorted_alphanumeric(data):
                        convert = lambda text: int(text) if text.isdigit() else text.lower()
                        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                        return sorted(data, key=alphanum_key)
                        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

                path_of_images = source
                dest_of_groundtruth = destination
                #sorted(os.listdir(os.getcwd()), key=len) does not work

                list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

                #print(list_of_images)

                newpagenum = 1
                newlinenum = 1

                for image in list_of_images:
                
                        img = cv2.imread(os.path.join(path_of_images, image))

                        height, width = img.shape[:2]
                        
                        filestr = os.path.basename(os.path.join(path_of_images, image))
                        
                        filesplit = os.path.splitext(filestr)
                        
                        filename = filesplit[0]
                        
                        fileext = filesplit[1]
                        
                        namesplit = filename.split("_")
                        
                        versionref = namesplit[0]
                        
                        pagestr = namesplit[2]
                        
                        pagenum = int(pagestr)
                        
                        linestr = namesplit[3]
                        #print(versionref,pagenum,linestr)
                        
                        linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
                        #print("Last digits of "+filename+" are "+last_digits)
                        
                        if pagenum > newpagenum:
                                
                                newlinenum = 1
                                
                                newpagenum = pagenum
                        
                        print("pagenum: " + pagestr + "  newpagenum: " + str(newpagenum) + "  linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
                                
                        shutil.copy(path_of_images + filestr, dest_of_groundtruth + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + r'.gt' + fileext)
                        
                        newlinenum += 1 
                                #print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
        def moveimages(source, destination):
                def sorted_alphanumeric(data):
                        convert = lambda text: int(text) if text.isdigit() else text.lower()
                        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                        return sorted(data, key=alphanum_key)
                        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

                path_of_images = source
                dest_of_groundtruth = destination
                #sorted(os.listdir(os.getcwd()), key=len) does not work

                list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

                #print(list_of_images)

                newpagenum = 1
                newlinenum = 1

                for image in list_of_images:
                
                        img = cv2.imread(os.path.join(path_of_images, image))

                        height, width = img.shape[:2]
                        
                        filestr = os.path.basename(os.path.join(path_of_images, image))
                        
                        filesplit = os.path.splitext(filestr)
                        
                        filename = filesplit[0]
                        
                        fileext = filesplit[1]
                        
                        namesplit = filename.split("_")
                        
                        versionref = namesplit[0]
                        
                        pagestr = namesplit[2]
                        
                        pagenum = int(pagestr)
                        
                        linestr = namesplit[3]
                        #print(versionref,pagenum,linestr)
                        
                        linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
                        #print("Last digits of "+filename+" are "+last_digits)
                        
                        if pagenum > newpagenum:
                                
                                newlinenum = 1
                                
                                newpagenum = pagenum
                        
                        print("pagenum: " + pagestr + "  newpagenum: " + str(newpagenum) + "  linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
                                
                        shutil.move(path_of_images + filestr, dest_of_groundtruth + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)
                        
                        newlinenum += 1 
                                #print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
        def splittextlines(source, destination):
                dest_of_textlinefiles = destination
                path_of_textfiles = source
                print(f'source:  {source} destination {destination}')
                list_of_textfiles = os.listdir(path_of_textfiles)
                        
                for tfile in list_of_textfiles:
                
                        textfile = open(path_of_textfiles + tfile)
                        
                        filestr = os.path.basename(path_of_textfiles + tfile)
                        
                        filesplit = os.path.splitext(filestr)
                        
                        filename = filesplit[0]
                        
                        fileext = filesplit[1]
                
                        for cnt, line in enumerate(textfile):
                                # open file to write line
                                outF = open(dest_of_textlinefiles + filename + "_Line" + str(cnt + 1) + ".gt" + fileext, "w")
                                # write line to output file
                                #outF.write(line)
                                outF.write(" ".join(line.split()))
                                #outF.write("\n")
                                print("Line {}: {}".format(cnt, line))
                                outF.close()

        def text2groundtruth(source, destination):
                def sorted_alphanumeric(data):
                        convert = lambda text: int(text) if text.isdigit() else text.lower()
                        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                        return sorted(data, key=alphanum_key)
                        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

                dest_of_groundtruth = destination
                #print(dest_of_groundtruth)
                path_of_textfiles = source
                #print(path_of_textfiles)
                list_of_textfiles = sorted_alphanumeric(os.listdir(path_of_textfiles))
                #font_name = "FROMVS_Regular_"

                newpagenum = 1
                newlinenum = 1


                for textfile in list_of_textfiles:

                        #filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))

                        #print(dest_of_groundtruth + filestr)
                                
                        #shutil.copy(path_of_textfiles + filestr, dest_of_groundtruth + filestr)
                        
                        filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))
                        #filestr = textfile

                        filesplit = os.path.splitext(textfile)
  
                        filename = filesplit[0]
  
                        fileext = filesplit[1]

                        namesplit = filename.split("_")
                       
                        
                        versionref = namesplit[0]
                        
                        pagestr = namesplit[2]
                        
                        pagenum = int(pagestr)
                        
                        linestr = namesplit[3]
                        #print(versionref,pagenum,linestr)
                        
                        if pagenum > newpagenum:
                                
                                newlinenum = 1
                                
                                newpagenum = pagenum

                        print(versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)
           
                        #shutil.copy(path_of_textfiles + filestr, dest_of_groundtruth + filename + "_Page_" + pagestr + "_" + linestr + '.gt' + fileext)   
                        shutil.copy(path_of_textfiles + textfile, dest_of_groundtruth + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum)+ '.gt' + fileext)
                        
                        newlinenum += 1 

        def text2groundtruthcopy(source, destination):
                def sorted_alphanumeric(data):
                        convert = lambda text: int(text) if text.isdigit() else text.lower()
                        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                        return sorted(data, key=alphanum_key)
                        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

                dest_of_groundtruth = destination
                path_of_textfiles = source
                list_of_textfiles = sorted_alphanumeric(os.listdir(path_of_textfiles))
                font_name = "FROMVS_Regular_"

                for textfile in list_of_textfiles:

                        '''filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))

                        print(dest_of_groundtruth + filestr)
                                
                        shutil.copy(path_of_textfiles + filestr, dest_of_groundtruth + filestr)'''
                        
                        filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))
    
                        filesplit = os.path.splitext(filestr)
                        
                        filename = filesplit[0]
                        
                        fileext = filesplit[1]
                        
                        namesplit = filename.split("_")
                        
                        versionref = namesplit[0]
                        
                        pagestr = namesplit[2]
                        
                        pagenum = int(pagestr)
                        
                        linestr = namesplit[3]
                        
                        print(font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext)
           
                        shutil.move(path_of_textfiles + filestr, dest_of_groundtruth + font_name + versionref + "_Page_" + pagestr + "_" + linestr + '.gt' + fileext)   

