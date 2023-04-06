import os

def pdf2tiff(source, destination):
    #idx = destination.rindex('.')
    #destination = destination[:idx]
    args = [
    '-q', '-sDEVICE=tiff24nc',
    '-r300', '-sPAPERSIZE=letter', '-sCompression=lzw',
    '-o ' + destination + '1516_Page_%03d.tif'
    ]
    gs_cmd = 'gs ' + ' '.join(args) +' '+ source
    os.system(gs_cmd)
   
#pdf2tiff('./Images/Source/pdf_source/1516_Page_51-60.pdf', './Images/Source/pdf4tif/')