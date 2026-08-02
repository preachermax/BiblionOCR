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
fonttablename = ''

fontttxFilePath = fontttxdir + fontfamily + '_' + fonttablename + '.ttx'
fontcsvFilePath = fontcsvdir + fontfamily + '_' + fonttablename + '.csv'
fontjsonFilePath = fontjsondir + fontfamily + '_' + fonttablename + '.json'

# Write ttf to ttx
def get_table(fonttablename,fontttxFilePath):
    table_cmd = f'ttx -t {fonttablename} -o {fontttxFilePath} {fonttablepath}'
    print(table_cmd)
    os.system(table_cmd)

# Write ttx to csv
def table2_csv(fonttablename):
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


start = time.perf_counter()

##### cmap #####
fonttablename = 'cmap'
fontttxFilePath = fontttxdir + fontfamily + '_' + fonttablename + '.ttx'
fontcsvFilePath = fontcsvdir + fontfamily + '_' + fonttablename + '.csv'
fontjsonFilePath = fontjsondir + fontfamily + '_' + fonttablename + '.json'
cols = ["code", "name"]
rows = []
get_table(fonttablename,fontttxFilePath)
def parse_cmap():
    # Parsing the cmap TTX/XML file
    xmlparse = Xet.parse(fontttxFilePath)
    root = xmlparse.getroot()
    # print(root)
    # for child in root:
    # print(child.tag, child.attrib)

    # print(Xet.tostring(root, encoding='utf8').decode('utf8'))

    for map in root.iter('map'):
        # print(code.attrib)
        code = map.attrib['code']
        name = map.attrib['name']
        print(f'Code: {code} Name: {name}')
        # print(code.tag)
        # print(code.tag, code.attrib)
        rows.append({"code": code, "name": name})
parse_cmap()
table2_csv(fonttablename)
table2_json(fontcsvFilePath, fontjsonFilePath)


finish = time.perf_counter()
print(f"Conversion completed successfully in {finish - start:0.4f} seconds")
