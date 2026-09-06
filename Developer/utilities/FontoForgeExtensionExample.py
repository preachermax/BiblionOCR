import fontforge


'''

Disregard: the yellow squigly line caused by PyLance and the resulting
ModuleNotFoundError: No module named 'fontforge'.

    This will occur anytime a python script containing 'import fontforge'
    is ran as 'python3 pythonfile.py' from a terminal window

Instead:
Correct usage is: from terminal window or with shutil:

    fontforge -lang=py -script pythonfile.py
        where pythonfile.py is the python script that cobtains 'import fontforge'
        and all the fontforge module functions that need to run with the fontforge module.

Refer to: https://github.com/fontforge/fontforge/issues/2597

Therefore:

a workable code solution is to utilize a python script that calls any needed
fontforge function(s) in spearate files, which can be executed as shown above.
    So, shutil() call-function scripts which require an 'import fontforge' statement
    for execution by fontforge will run without errors

Note:  The FontForge applicayion's GUI will not start and run.
Only the script will execute as a normal python script.

Refer to: https://dmtr.org/ff.php#Font
for a description of available fontforge and psMat functions.

'''

# to run this script, copy & paste the following into a terminal window:
# fontforge -lang=py -script /home/jetson/Projects/BiblionOCR/Model/Developer/Reference/Utilities/FontoForgeExtensionExample.py

f = fontforge.open("/home/jetson/Documents/MyForge/FROMVS.ttf")
M_width = f['sigma_chi'].width
print(M_width)
