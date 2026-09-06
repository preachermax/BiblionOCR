import os
import csv
#import fontforge

#f = fontforge.open("/home/max/Documents/MyForge/FROMVS3_0.sfd")

searchdir = ''
findstr = ''
replacestr = ''

def swap_path(searchdir,findstr,replacestr):
    for dname, dirs, files in os.walk(searchdir):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                s = f.read()
            s = s.replace(findstr, replacestr)
            with open(fpath, "w") as f:
                f.write(s)

swapfile = open("/home/max/Projects/BiblionOCR/Model/Project/Data/csv/FROMVS3_0_PUA_Swap.csv")

# Replace ligature encodings from previous font's PUA

# Manually provide searchdir until MyCharacter.py is ready

#Developer
#searchdir = '/home/max/Projects/BiblionOCR/Model/Developer/Reference/font/FontChangeTov3_0/txt_greek_verses/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Developer/Reference/font/FontChangeTov3_0/txt_greek_pages/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Developer/Reference/font/FontChangeTov3_0/txt_greek_lines_autosplit/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Developer/Reference/font/FontChangeTov3_0/SQLite/Table Dumps/'


#Project
#searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_verses/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_pages/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/'
searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/Table Dumps/'

with swapfile:
        csv_f = csv.reader(swapfile)
        for row in csv_f:
                findstr, replacestr = (row[3], row[5])
                print(f'Replacing old font characters: find: {findstr} replace: {replacestr}')
                # Call swap_path
                swap_path(searchdir,findstr, replacestr)
swapfile.close()