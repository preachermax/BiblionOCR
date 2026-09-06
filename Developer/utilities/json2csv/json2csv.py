import time
import pandas as pd


def json2csv(csvFilePath, jsonFilePath):
    df = pd.read_json (jsonFilePath)
    df.to_csv(csvFilePath, index = True, encoding='utf-8')

#csvFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/csv4json/Session.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/json/Session.json'

#csvFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/csv4json/Workflow.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/json/Workflow.json'

#csvFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/csv4json/BooksMarkDown.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/json/BooksMarkDown.json'

#csvFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/csv/csv4json/BookChapterVerse.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblicalOCR/Model/Data/json/BookChapterVerse.json'

#csvFilePath = r'c:/users/max/Projects/BiblionOCR/Model/Developer/Reference/csv/rmac.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblionOCR/Model/Developer/Reference/json/rmac.json'

#csvFilePath = r'c:/users/max/Projects/BiblionOCR/Model/Project/Data/csv/PageVerseXref.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblionOCR/Model/Project/Data/json/PageVerseCrossReference.json'

#csvFilePath = r'c:/users/max/Projects/BiblionOCR/Model/Project/Data/csv/RMAC.csv'
#jsonFilePath = r'c:/users/max/Projects/BiblionOCR/Model/Project/Data/json/RMAC.json'

#csvFilePath = r'/home/max-richey/Projects/BiblionOCR/Model/Project/Data/csv/Session.csv'
#jsonFilePath = r'/home/max-richey/Projects/BiblionOCR/Model/Project/Data/json/Session.json'

csvFilePath = r'/home/max-richey/Projects/BiblionOCR/Model/Project/Data/csv/project_database.csv'
jsonFilePath = r'/home/max-richey/Projects/BiblionOCR/Model/Project/Data/json/project_database.json'


start = time.perf_counter()
json2csv(csvFilePath, jsonFilePath)
finish = time.perf_counter()

print(f"Conversion completed successfully in {finish - start:0.4f} seconds")