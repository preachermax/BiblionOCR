import csv
import json
import time


jsondir = r'/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/'
csvdir = r'/home/jetson/Projects/BiblionOCR/Model/Project/Data/csv/'

def csv_to_json(csvFilePath, jsonFilePath):

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

#csvFilePath = r'data.csv'
#jsonFilePath = r'data.json'

# Session
#csvFilePath = csvdir + 'Session.csv'
#jsonFilePath = jsondir + 'Session.json'

# Scanner
#csvFilePath = csvdir + 'ScannerSession.csv'
#jsonFilePath = jsondir + 'ScannerSession.json'

# Reader
#csvFilePath = csvdir + 'ReaderSession.csv'
#jsonFilePath = jsondir + 'ReaderSession.json'

# Versifier
csvFilePath = csvdir + 'VersifierSession.csv'
jsonFilePath = jsondir + 'VersifierSession.json'

# Grounder
#csvFilePath = csvdir + 'GrounderSession.csv'
#jsonFilePath = jsondir + 'GrounderSession.json'

# Writer
#csvFilePath = csvdir + 'WriterSession.csv'
#jsonFilePath = jsondir + 'WriterSession.json'

# Pixler
#csvFilePath = csvdir + 'PixlerSession.csv'
#jsonFilePath = jsondir + 'PixlerSession.json'

# Boxer
#csvFilePath = csvdir + 'BoxerSession.csv'
#jsonFilePath = jsondir + 'BoxerSession.json'

# Workflow
#csvFilePath = csvdir + 'Workflow.csv'
#jsonFilePath = jsondir + 'Workflow.json'

# BooksMarkDown
#csvFilePath = csvdir + 'BooksMarkDown.csv'
#jsonFilePath = jsondir + 'BooksMarkDown.json'

# BookChapterVerse
#csvFilePath = csvdir + 'csv4json/BookChapterVerse.csv'
#jsonFilePath = jsondir + 'BookChapterVerse.json'

# BookAbbrName
#csvFilePath = csvdir + 'BooksAbbrName.csv'
#jsonFilePath = jsondir + 'BooksAbbrName.json'

# BooksAbbrNameNumIndex
#csvFilePath = csvdir + 'BooksAbbrNameNumIndex.csv'
#jsonFilePath = jsondir + 'BooksAbbrNameNumIndex.json'

# PageVerseCrossReference
#csvFilePath = csvdir + 'PageVerseCrossReference.csv'
#jsonFilePath = jsondir + 'PageVerseCrossReference.json'

start = time.perf_counter()
csv_to_json(csvFilePath, jsonFilePath)
finish = time.perf_counter()

print(f"Conversion completed successfully in {finish - start:0.4f} seconds")