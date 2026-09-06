import os


searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_verses/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_pages/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/'
#searchdir = '/home/max/Projects/BiblionOCR/Model/Project/Data/SQLite/Table Dumps/'

#searchdir = ''

findstr = 'αʼ'
replacestr = ''
#findstr = 'δʼ'
#replacestr = ''
#findstr = 'θʼ'
#replacestr = ''
#findstr = 'ϑʼ'
#replacestr = ''
#findstr = 'φʼ'
#replacestr = ''
#findstr = 'λʼ'
#replacestr = ''
#findstr = 'πʼ'
#replacestr = ''
#findstr = 'ϖʼ'
#replacestr = ''
#findstr = 'ʼ'
#replacestr = ''
#findstr = 'τʼ'
#replacestr = ''
#findstr = 'χʼ'
#replacestr = ''
#findstr = 'ά'
#replacestr = 'ά'
#findstr = 'έ'
#replacestr = 'έ'
#findstr = 'ή'
#replacestr = 'ή'
#findstr = 'ί'
#replacestr = 'ί'
#findstr = 'ό'
#replacestr = 'ό'
#findstr = 'ύ'
#replacestr = 'ύ'
#findstr = 'ώ'
#replacestr = 'ώ'

for dname, dirs, files in os.walk(searchdir):
    for fname in files:
        fpath = os.path.join(dname, fname)
        with open(fpath) as f:
            s = f.read()
        print(f'for file: {fname} replacing strings: find: {findstr} replace: {replacestr}')
        s = s.replace(findstr, replacestr)
        with open(fpath, "w") as f:
            f.write(s)