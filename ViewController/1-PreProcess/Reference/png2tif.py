import os
from PIL import Image

path_of_png_images = "/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/"
path_of_png2tif_images = r"/home/max/Projects/Python/Images/Greek/png2tif_greek/greek_book_40_Matthew/"

list_of_images = os.listdir(path_of_png_images)

for image in list_of_images:
    
    # Open the selected large .tif image. 
    png_image = Image.open(os.path.join(path_of_png_images, image))
       
    # separate .tif extension for original filename
    filestr = os.path.basename(os.path.join(path_of_png_images, image))
    filesplit = os.path.splitext(filestr)
    filename = filesplit[0]
    fileext = filesplit[1]
    
    # Resize image to original proportions to maintain aspect ratio
    #(width,height) = big_image.size
    #aspect_ratio = ((width/height))
    #print("Aspect Ratio: " + str(aspect_ratio))
    #new_width = (width/4)
    #new_height = (new_width/aspect_ratio)
    #my_img_resized = big_image.resize((int(new_width), int(new_height))) 
    
    # Designate .jpg output path/filename
    outfile = path_of_png2tif_images + filename + ".tif"
    
    try:
        print("Generating: " + outfile)
        png_image.save(outfile, "TIFF", dpi=(300,300))
        #my_img_resized.save(outfile, "PNG")
    except Exception as e:
        print(e)
    
    
    
           
  
