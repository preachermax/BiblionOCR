# Importing the required libraries
import xml.etree.ElementTree as Xet
import pandas as pd
import json
import csv
import time
import os


fontttf = "FROMVS.ttf"
fontttfsplit = fontttf.split('.')
fontfamily = fontttfsplit[0]
fonttype = fontttfsplit[1]
fonttabledir = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
fonttablepath = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/' + fontttf
fontjsondir = r'/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
fontcsvdir = r'/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
fontttxdir = r'/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
fonttablename = 'glyf'
fontttxFilePath = fontttxdir + fontfamily + '_' + fonttablename + '.ttx'
fontcsvFilePath = fontcsvdir + fontfamily + '_' + fonttablename + '.csv'
fontjsonFilePath = fontjsondir + fontfamily + '_' + fonttablename + '.json'

cols = ["name", "xMin", "yMin", "xMax", "yMax"]
rows = []

# Write ttf to ttx
def get_table():
    table_cmd = f'ttx -t {fonttablename} -o {fontttxFilePath} {fonttablepath}'
    print(table_cmd)
    os.system(table_cmd)

# Parse ttx
def parse_glyf():
    # Parsing the glyf TTX/XML file
    xmlparse = Xet.parse(fontttxFilePath)
    root = xmlparse.getroot()
    print(f'Root: {root}')
    #for child in root:
        #print(child.tag, child.attrib)

    # print(Xet.tostring(root, encoding='utf8').decode('utf8'))

    for TTGlyph in root.iter('TTGlyph'):
        cnt = 1
        # print(code.attrib)
        if TTGlyph.attrib['name'] != ".null" and TTGlyph.attrib['name'] != "glyph2" and TTGlyph.attrib['name'] != "space"\
                            and TTGlyph.attrib['name'] != "uni0000" and TTGlyph.attrib['name'] != "uni00A0"\
                            and TTGlyph.attrib['name'] != "uniE138" and TTGlyph.attrib['name'] != "uniE138"\
                            and TTGlyph.attrib['name'] != "uniE84E" and TTGlyph.attrib['name'] != "uniE84F":
            name = TTGlyph.attrib['name']
            print(f'Name: {name}')
            xMin = TTGlyph.attrib['xMin']
            print(f'xMin: {xMin}')
            yMin = TTGlyph.attrib['yMin']
            print(f'yMin: {yMin}')
            xMax = TTGlyph.attrib['xMax']
            print(f'xMax: {xMax}')
            yMax = TTGlyph.attrib['yMax']
            print(f'yMax: {yMax}')
            cnt = 1
            print(f'Glyph name: {name} xmin: {xMin}, ymin: {yMin} xmax: {xMax} ymax: {yMax}')
            rows.append({"name": name, "xMin": xMin, "yMin": yMin, "xMax": xMax, "yMax": yMax})
    
    
    '''for contour in TTGlyph.iter('contour'):    
        cols = ["contour","name", "xMin", "yMin", "xMax", "yMax"]
        for pt in contour.iter('pt'):
            x = pt.attrib['x']
            y = pt.attrib['y']
            on = pt.attrib['on']
            print(f'contour {cnt}: x: {x}, y: {y} on: {on}')
            rows.append({"contour": cnt, "x": x, "y": y, "on": on})
            cnt += 1'''

# Write ttx to csv
def table2_csv():
    df = pd.DataFrame(rows, columns=cols)
    # Writing dataframe to csv
    df.to_csv(fontcsvFilePath)
    
# Write csv to json
def table2_json(fontcsvFilePath, fontjsonFilePath):

    jsonArray = []

    # read csv file
    with open(fontcsvFilePath, encoding='utf-8') as csvf:
        # load csv file data using csv library's dictionary reader
        csvReader = csv.DictReader(csvf)

        # convert each csv row into python dict
        for row in csvReader:
            # add this python dict to json array
            jsonArray.append(row)

    # convert python jsonArray to JSON String and write to file
    with open(fontjsonFilePath, 'w', encoding='utf-8') as jsonf:
        '''jsonString = json.dumps(jsonArray, indent=4)
        print(jsonString)
        jsonf.write(jsonString)'''
        json.dump(jsonArray, jsonf, indent=4)

# Start progress counter
start = time.perf_counter()

get_table()
parse_glyf()
table2_csv()
table2_json(fontcsvFilePath, fontjsonFilePath)

finish = time.perf_counter()
print(f"Conversion completed successfully in {finish - start:0.4f} seconds")
