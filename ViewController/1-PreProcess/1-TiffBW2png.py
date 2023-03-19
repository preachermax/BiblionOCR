import os
from PIL import Image

path_of_png_images = "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/"
path_of_tif_bw_images = r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/"

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
        #my_img_resized.save(outfile, "PNG")
    except Exception as e:
        print(e)
    
    
    
           
  
