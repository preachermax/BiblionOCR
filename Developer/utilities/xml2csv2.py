# Importing the required libraries
import xml.etree.ElementTree as Xet
import pandas as pd

cols = ["item id", "description"]
rows = []

# Parsing the XML file
xmlparse = Xet.parse('/home/max/Projects/BiblionOCR/Model/Developer/Reference/xml/rmac.xml')
root = xmlparse.getroot()
print(root)
'''for child in root:
    print(child.tag, child.attrib)'''

print(Xet.tostring(root, encoding='utf8').decode('utf8'))

'''for i in root:
    item_id = i.find("id").text
    description = i.find("description").text


    rows.append({"item_id": id,
                 "description": description})

df = pd.DataFrame(rows, columns=cols)

# Writing dataframe to csv
df.to_csv('output.csv')'''
