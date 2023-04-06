import json
 
# Opening JSON file
with open('/home/max/Projects/BiblicalOCR/Model/SQLite/json/Workflow.json') as f:
    # returns JSON object as
    # a dictionary
    data = json.load(f)
 
# Iterating through the json
# list
for Sequence in data:
    print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
 
# Closing file
f.close()