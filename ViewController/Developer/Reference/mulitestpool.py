import os
import time
import concurrent.futures as cf
from PIL import Image, ImageFilter
import cv2

img_names = [
'1516_Page_051.tif',
'1516_Page_052.tif',
'1516_Page_053.tif',
'1516_Page_054.tif',
'1516_Page_055.tif'
]

t1 = time.perf_counter()

size = (1200, 1200)

def process_image(img_name):
    
    #img = Image.open("Workflow/0-MainUI/" + img_name)
    image = cv2.imread(os.path.join("Workflow/0-MainUI/", img_name))
    
    filestr = os.path.basename(os.path.join("Workflow/0-MainUI/", img_name))
    filesplit = os.path.splitext(filestr)
    filename = filesplit[0]
    fileext = filesplit[1]
    
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    
    #convert grayscale to binary to be rotated later
    ret, binary = cv2.threshold(image,127,255,cv2.THRESH_BINARY)

    PILimage = Image.fromarray(binary)
    thresh = 127
    fn = lambda x : 255 if x > thresh else 0
    PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
    
    outfile = "Workflow/0-MainUI/processed/" + filename + ".tif"
                    
    try:
        print("Generating: " + outfile)
        PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))
    except Exception as e:
        print(e)
    
    
    '''img = img.filter(ImageFilter.GaussianBlur(15))

    img.thumbnail(size)
    img.save(f'processed/{img_name}')'''

    print(f'{img_name} was processed...')

with cf.ProcessPoolExecutor() as executor:
    executor.map(process_image, img_names)

t2 = time.perf_counter()

print(f'Finished in {t2-t1} seconds')

