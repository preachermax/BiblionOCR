import os
import filecmp
  
# Path of first directory
dir1 = "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"
  
# Path of second directory
dir2 = "/home/max/tesseract/tesstrain-raw-49-2/data/feg-ground-truth/"
   
# Common files
common = os.listdir(dir1)
  
# Shallow compare the files
# common in both directories  
match, mismatch, errors = filecmp.cmpfiles(dir1, dir2, common)

with open('/home/max/Projects/Python/CompareFiles/GTShallowMismatch.txt', 'w') as f:
    for item in mismatch:
        f.write("%s\n" % item)

# Print the result of
# shallow comparison
print("Shallow comparison:")
#print("Match :", match)
print("Mismatch :", mismatch)
print("Errors :", errors, "\n")  
  
# Compare the
# contents of both files
# (i.e deep comparison)
match, mismatch, errors = filecmp.cmpfiles(dir1, dir2, common,
                                              shallow = False)
  
with open('/home/max/Projects/Python/CompareFiles/GTDeepMismatch.txt', 'w') as f:
    for item in mismatch:
        f.write("%s\n" % item)

# Print the result of
# deep comparison
print("Deep comparison:")
#print("Match :", match)
print("Mismatch :", mismatch)
print("Errors :", errors)