with open("/home/max/Projects/Python/EstablishTruth/Greek completed text/Erasmus1516NT_Lines.txt") as xh:
  with open("/home/max/Projects/Python/EstablishTruth/Greek completed text/VerseList.txt") as yh:
    with open("/home/max/Projects/Python/EstablishTruth/Greek completed text/Erasmus1516NT_Verses.txt","w") as zh:
      #Read first file
      xlines = xh.readlines()
      #Read second file
      ylines = yh.readlines()
      #Combine content of both lists
      #combine = list(zip(ylines,xlines))
      #Write to third file
      for i in range(len(xlines)):
        line = ylines[i].strip() + ' ' + xlines[i]
        #print(line)
        zh.write(line)