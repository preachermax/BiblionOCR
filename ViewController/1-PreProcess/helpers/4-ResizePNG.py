import os
from PIL import Image

path_of_png_resized = "/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/"
path_of_png_deskew = r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/"

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
    
    
    
           
  
