# Import required modules
from tkinter import *
from tkinter import ttk
from PIL import ImageTk,Image
from tkinter import filedialog
import os
import pytesseract

# Initialize root loop to start application
root = Tk()
root.title("OCR Processing")
root.geometry("480x640")
#root.iconbitmap('my_icon.ico') - .ico is windows only

def get_OCR_raw(imgfilename):
    
    path_to_OCR_raw = "/home/max/Projects/Python/OCRText/OCR-Raw/greek_book_40_Matthew/"
    
    imgbasename = os.path.basename(imgfilename)
    
    filestr = os.path.basename(os.path.join(path_to_OCR_raw, imgbasename))
    
    my_OCR_rawtextfile = open(filestr, 'w')
      
    my_OCR_rawtext = pytesseract.image_to_string(imgfilename,lang="feg")
    
    my_OCR_rawtextfile.write(my_OCR_rawtext)
    
    my_OCR_text.insert(END,my_OCR_rawtext)
    
def save_OCR_corrected(imgfilename):
    
    path_to_OCR_raw = "/home/max/Projects/Python/OCRText/OCR-Raw/greek_book_40_Matthew/"
    
    imgbasename = os.path.basename(imgfilename)
    
    rawfilestr = os.path.basename(os.path.join(path_to_OCR_raw, imgbasename))
    
    rawfilesplit = os.path.splitext(rawfilestr)
    
    rawfilename = rawfilesplit[0]
    
    rawfileext = ".txt"
    
    rawtextfile = path_to_OCR_raw + rawfilename + rawfileext
    
    if os.path.exists(rawtextfile):
        my_OCR_rawtextfile = open(rawtextfile, 'r')
        my_OCR_rawtextfile.read()
    else:
        my_OCR_rawtextfile = open(rawtextfile, 'w')
        my_OCR_rawtextfile.write(rawtextfile)
        
    my_OCR_rawtextfile.close()
       
    path_to_OCR_corrected = "/home/max/Projects/Python/OCRText/OCR-Corrected/greek_book_40_Matthew/"
    
    corrfilestr = path_to_OCR_corrected + rawfilename + rawfileext

    my_OCR_corrtextfile = open(corrfilestr, 'w')
    my_OCR_corrtextfile.write = my_OCR_text.get(1.0,END)
    

# To create a scollable canvas for an application window, follow these steps: 

# 1. Create a primary frame.
main_frame = Frame(root)
main_frame.pack(fill=BOTH, expand=1)

# 2. Create a canvas inside the primary frame.
my_canvas = Canvas(main_frame)
my_canvas.pack(side=LEFT, fill=BOTH, expand=1)

# 3. Add a Scrollbar to the canvas.
my_scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=my_canvas.yview)
my_scrollbar.pack(side=RIGHT, fill=Y)

# 4. Configure the canvas to utilize the Scrollbar.
my_canvas.configure(yscrollcommand=my_scrollbar.set)

# 5. Bind the configuration to an event
my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion = my_canvas.bbox("all")))

# 6. Create a secondary frame inside the canvas.
secondary_frame = Frame(my_canvas)

# 7. Add the secondary frame to an application window also inside the canvas.
my_canvas.create_window((0,0), window = secondary_frame, anchor="nw")

# Set initial directory for image folders containing deskewed images.
path_to_images = "/home/max/Projects/Python/Images/Greek/tif_desk_greek"

# Open file dialog in initial directory to select image folder.
# Then select the deskewed .tif image for display and to perform OCR.
secondary_frame.filename = filedialog.askopenfilename(initialdir=path_to_images, title="Select an OCR .tif image", filetypes=(("tif files","*.tif"),("all files","*.*")))

# Open the selected large .tif image. 
big_image = Image.open(secondary_frame.filename)
(width,height) = big_image.size
aspect_ratio = ((width/height))
new_width = (width/4)
new_height = (new_width/aspect_ratio)

# Resize image to original proportions to maintain aspect ratio
my_img_resized = big_image.resize((int(new_width), int(new_height)))

# Create container variable for resized image
my_img = ImageTk.PhotoImage(my_img_resized)

# Create label container and display in application window
my_label = Label(secondary_frame, image=my_img)
my_label.pack(side=LEFT, fill=BOTH, expand=1, pady=40)

my_OCR_text = Text(secondary_frame, width=40, height=10, font=("FROMVS",22), spacing1=12)
my_OCR_text.pack(side=RIGHT, fill=BOTH, expand=1, pady=7)

OCR_button = Button(secondary_frame, text = "OCR", command=get_OCR_raw(secondary_frame.filename))
OCR_button.pack(side=TOP)

save_button = Button(secondary_frame, text = "Save", command=save_OCR_corrected(secondary_frame.filename))
save_button.pack(side=TOP)

# End of root loop
root.mainloop()