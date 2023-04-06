import os 

def pdf4tiff(source, destination,firstpage,lastpage):

    args = [
    '-sDEVICE=pdfwrite', ' -dNOPAUSE', ' -dBATCH',
    ' -dSAFER', ' -dFirstPage=' + firstpage, ' -dLastPage=' + lastpage,
    ' -sOutputFile=' + destination + '1516_Page_' + firstpage + '-' + lastpage + '.pdf'
    ]
    gs_cmd = 'gs ' + ' '.join(args) +' '+ source
    os.system(gs_cmd)
   
#pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60')