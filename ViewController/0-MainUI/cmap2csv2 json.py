# Importing the required libraries
import xml.etree.ElementTree as Xet
import pandas as pd
import json
import csv 
import time
import os
  
cols = ["code", "name"]
rows = []
cmapdir = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
cmappath = '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS.ttf'
jsondir = r'/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
csvdir = r'/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/'
csvFilePath = jsondir + 'FROMVS_cmap.csv'
jsonFilePath = csvdir + 'FROMVS_cmap.json'

def get_cmap():
    cmap_cmd = f'ttx -t cmap {cmappath}'
    print(cmap_cmd)
    os.system(cmap_cmd)

def parse_cmap():
    # Parsing the cmap TTX/XML file
    xmlparse = Xet.parse(cmapdir + 'FROMVS_cmap.ttx')
    root = xmlparse.getroot()
    #print(root)
    #for child in root:
        #print(child.tag, child.attrib)

    #print(Xet.tostring(root, encoding='utf8').decode('utf8'))

    for map in root.iter('map'):
        #print(code.attrib)
        code = map.attrib['code']
        name = map.attrib['name']
        print(f'Code: {code} Name: {name}')
        #print(code.tag)
        #print(code.tag, code.attrib)
        rows.append({"code": code,"name": name})

def cmap2_csv():
    df = pd.DataFrame(rows, columns=cols)
    # Writing dataframe to csv
    df.to_csv('/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/fonts/FROMVS_cmap.csv')

# Write csv to json



def cmap2_json(csvFilePath, jsonFilePath):

    jsonArray = []
    
    #read csv file
    with open(csvFilePath, encoding='utf-8') as csvf: 
        #load csv file data using csv library's dictionary reader
        csvReader = csv.DictReader(csvf) 

        #convert each csv row into python dict
        for row in csvReader: 
            #add this python dict to json array
            jsonArray.append(row)
  
    #convert python jsonArray to JSON String and write to file
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf: 
        '''jsonString = json.dumps(jsonArray, indent=4)
        print(jsonString)
        jsonf.write(jsonString)'''
        json.dump(jsonArray, jsonf, indent=4)

start = time.perf_counter()
get_cmap()
parse_cmap()
cmap2_csv()
cmap2_json(csvFilePath, jsonFilePath)
finish = time.perf_counter()

print(f"Conversion completed successfully in {finish - start:0.4f} seconds")