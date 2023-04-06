print("This is the Biblion Boxer application")

''' https://www.codesofinterest.com/2017/07/more-fonts-on-opencv.html'''
from PIL import ImageFont, ImageDraw, Image  
import cv2  
import numpy as np  

text_to_show = "The quick brown fox jumps over the lazy dog"  

# Load image in OpenCV  
image = cv2.imread("Me.jpg")  

# Convert the image to RGB (OpenCV uses BGR)  
cv2_im_rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)  

# Pass the image to PIL  
pil_im = Image.fromarray(cv2_im_rgb)  

draw = ImageDraw.Draw(pil_im)  
# use a truetype font  
font = ImageFont.truetype("PAPYRUS.ttf", 80)  

# Draw the text  
draw.text((10, 700), text_to_show, font=font)  

# Get back the image to OpenCV  
cv2_im_processed = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)  

cv2.imshow('Fonts', cv2_im_processed)  
cv2.waitKey(0)  

cv2.destroyAllWindows() 


'''https://www.computervision.zone/courses/text-detection/'''

####Text Detection Basics####
import cv2
import pytesseract
import numpy as np
from PIL import ImageGrab
import time


pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
img = cv2.imread('1.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

#############################################
#### Detecting Characters  ######
#############################################
hImg, wImg,_ = img.shape
boxes = pytesseract.image_to_boxes(img)
for b in boxes.splitlines():
    print(b)
    b = b.split(' ')
    print(b)
    x, y, w, h = int(b[1]), int(b[2]), int(b[3]), int(b[4])
    cv2.rectangle(img, (x,hImg- y), (w,hImg- h), (50, 50, 255), 2)
    cv2.putText(img,b[0],(x,hImg- y+25),cv2.FONT_HERSHEY_SIMPLEX,1,(50,50,255),2)


cv2.imshow('img', img)
cv2.waitKey(0)



##### Image to String   ######
import cv2
import pytesseract
import numpy as np
from PIL import ImageGrab
import time


pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
img = cv2.imread('1.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
pytesseract
##############################################
##### Image to String   ######
##############################################
print(pytesseract.image_to_string(img))&lt;br&gt;cv2.imshow('img', img)&lt;br&gt;cv2.waitKey(0)



##### Detecting Words  ######
import cv2
import pytesseract
import numpy as np
from PIL import ImageGrab
import time

pytesseract.pytesseract.tesseract_cmd = 'C:Program FilesTesseract-OCRtesseract.exe'
img = cv2.imread('1.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

##############################################
##### Detecting Words  ######
##############################################
# #[   0          1           2           3           4          5         6       7       8        9        10       11 ]
# #['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
# boxes = pytesseract.image_to_data(img)
# for a,b in enumerate(boxes.splitlines()):
#         print(b)
#         if a!=0:
#             b = b.split()
#             if len(b)==12:
#                 x,y,w,h = int(b[6]),int(b[7]),int(b[8]),int(b[9])
#                 cv2.putText(img,b[11],(x,y-5),cv2.FONT_HERSHEY_SIMPLEX,1,(50,50,255),2)
#                 cv2.rectangle(img, (x,y), (x+w, y+h), (50, 50, 255), 2)
&lt;br&gt;cv2.imshow('img', img)&lt;br&gt;cv2.waitKey(0)



##### Detecting ONLY Digits  ######
import cv2
import pytesseract
import numpy as np
from PIL import ImageGrab
import time

pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
img = cv2.imread('1.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)&lt;br&gt;
##############################################
##### Detecting ONLY Digits  ######
##############################################
# hImg, wImg,_ = img.shape
# conf = r'--oem 3 --psm 6 outputbase digits'
# boxes = pytesseract.image_to_boxes(img,config=conf)
# for b in boxes.splitlines():
#     print(b)
#     b = b.split(' ')
#     print(b)
#     x, y, w, h = int(b[1]), int(b[2]), int(b[3]), int(b[4])
#     cv2.rectangle(img, (x,hImg- y), (w,hImg- h), (50, 50, 255), 2)
#     cv2.putText(img,b[0],(x,hImg- y+25),cv2.FONT_HERSHEY_SIMPLEX,1,(50,50,255),2)&lt;br&gt;
cv2.imshow('img', img)
cv2.waitKey(0)