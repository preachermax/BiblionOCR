import os

searchdir = ''

findstr = ''
replacestr = ''

for dname, dirs, files in os.walk(searchdir):
    for fname in files:
        fpath = os.path.join(dname, fname)
        with open(fpath) as f:
            s = f.read()
        s = s.replace(findstr, replacestr)
        with open(fpath, "w") as f:
            f.write(s)