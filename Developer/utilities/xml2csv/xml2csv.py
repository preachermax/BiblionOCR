from xml.etree import ElementTree
import csv

# PARSE XML
xml = ElementTree.parse('/home/max/Projects/BiblionOCR/Model/Developer/Reference/xml/rmac.xml')
print(xml)
# CREATE CSV FILE
csvfile = open('/home/max/Projects/BiblionOCR/Model/Developer/Reference/csv/rmac.csv','w',encoding='utf-8')
csvfile_writer = csv.writer(csvfile)

# ADD THE HEADER TO CSV FILE
csvfile_writer.writerow(["item id","description"])

# FOR EACH EMPLOYEE
'''for item in xml.findall("employee"):

    if(item):

       # EXTRACT EMPLOYEE DETAILS
      id = item.find("item id")
      description = item.find("description")
      csv_line = [id.text, description.text]

      # ADD A NEW ROW TO CSV FILE
      csvfile_writer.writerow(csv_line)'''