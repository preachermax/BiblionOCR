import fontTools
from fontTools.ttLib import ttFont
import fontParts
import fontPens

fontpath = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS.ttf'
xmlpath = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS.xml'
fontxml = ttFont.TTFont(fontpath)
fontxml.saveXML(xmlpath)
print(f'FROMVS.xml => {fontxml}')

def MyAppObjectGenerator(classIdentifier):
    unrequested = []
    #obj = myApp.foo.bar.something.hi(classIdentifier)
    #return obj, unrequested