import os
import shutil
import re
import subprocess

def runsubproc(uifile,pyfile):
    print(uifile,pyfile)
    #--resource-suffix=SUFFIX
    cmd = 'pyuic5 -x ' + path_of_uifiles + uifile + ' -o ' + dest_of_pythonfiles + pyfile
    print(cmd)
    os.system(cmd)

def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)
    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

dest_of_pythonfiles = "/home/max/Projects/Python/Workflow/0-MainUI/"
path_of_uifiles = r"/home/max/Projects/Python/Workflow/0-MainUI/QtDesignerUI/"

list_of_uifiles = sorted_alphanumeric(os.listdir(path_of_uifiles))
#print(list_of_uifiles)

for uifile in list_of_uifiles:
        
    #img = cv2.imread(os.path.join(path_of_images, image))

    #height, width = img.shape[:2]
    
    filestr = os.path.basename(os.path.join(path_of_uifiles, uifile))
    
    filesplit = os.path.splitext(filestr)
    
    filename = filesplit[0]
    fileext = filesplit[1]
    uifile = filename+fileext
    pyfile = filename+".py"
    #print(filestr)    
    
    runsubproc(uifile,pyfile)
    
    '''namesplit = filename.split("_")
    
    versionref = namesplit[0]
    
    pagestr = namesplit[2]
    
    pagenum = int(pagestr)
    
    linestr = namesplit[3]
    
    print(font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext)
        
    shutil.move(path_of_textfiles + filestr, dest_of_groundtruth + font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext) ''' 