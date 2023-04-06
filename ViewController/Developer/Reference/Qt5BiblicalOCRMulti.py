#print(len(locals()))

# Python
import sys
import os
import pytesseract
import tiffcapture
import qimage2ndarray
from queue import Queue
#from tqdm.auto import tqdm
#from subprocess import Popen, PIPE, CalledProcessError

# PyQt5
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc 
from PyQt5.QtCore import QObject, QThread, pyqtSignal

# Custom
from MainUI import Ui_MainUI
from Training import Train as tr
import Qt5GroundTruthReview as gtr
import Qt5Versify as versify
#from CorrectOCR import CorrectOCR as ocr
#from PreProcess import PreProcess as pp
#from MultiPreProcess import MultiPreProcess as mpp

#print(len(locals()))

# The Main Application Thread
class MainApp(qtw.QApplication):
    '''The Main Application Object'''
    def __init__(self,argv):
        super().__init__(argv)

        # create main window
        self.main_window = MainWindow()
        self.main_window.show()

        '''Class Signals Binding Monitor'''
        
        # Main window signals

        # Bind main window signals to worker slots
        

        # Worker thread signals

        # Instantiate & monitor worker thread class for (worker)signal/(mainwindow)slot binding
        self.pdfextractor = ExtractPdf4Tiff()
        # Bind worker thread signals to main window slots
        self.pdfextractor.progress.connect(MainWindow.progress_report)
        self.pdfextractor.finished.connect(MainWindow.process_complete)
    
# The new Stream Object which replaces the default stream associated with sys.stdout
# This object just puts data in a queue!
class WriteStream(object):
    def __init__(self,queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        """
        Stream flush implementation
        """
        pass
    
# A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
# It blocks until data is available, and one it has got something from the queue, it sends
# it to the "MainThread" by emitting a Qt Signal 
class ThreadConsoleTextQueueReceiver(qtc.QObject):
    
    queue_element_received_signal = qtc.pyqtSignal(str)

    def __init__(self, q: Queue, *args, **kwargs):
        qtc.QObject.__init__(self, *args, **kwargs)
        self.queue = q

    @qtc.pyqtSlot()
    def run(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Started <---\n')
        while True:
            text = self.queue.get()
            self.queue_element_received_signal.emit(text)

    @qtc.pyqtSlot()
    def finished(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Stopped <---\n')

'''
class Logging(qtc.QObject):
    def setup_logging(log_prefix):
        global __is_setup_done

        if __is_setup_done:
            pass
        else:
            __log_file_name = "{}-{}_log_file.txt".format(log_prefix,
                                                        datetime.datetime.utcnow().isoformat().replace(":", "-"))

            __log_format = '%(asctime)s - %(name)-30s - %(levelname)s - %(message)s'
            __console_date_format = '%Y-%m-%d %H:%M:%S'
            __file_date_format = '%Y-%m-%d %H-%M-%S'

            root = logging.getLogger()
            root.setLevel(logging.DEBUG)

            console_formatter = logging.Formatter(__log_format, __console_date_format)

            file_formatter = logging.Formatter(__log_format, __file_date_format)
            file_handler = logging.FileHandler(__log_file_name, mode='a', delay=True)

            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            root.addHandler(file_handler)

            tqdm_handler = TqdmLoggingHandler()
            tqdm_handler.setLevel(logging.DEBUG)
            tqdm_handler.setFormatter(console_formatter)
            root.addHandler(tqdm_handler)

            __is_setup_done = True

class TqdmLoggingHandler(logging.StreamHandler):

    def __init__(self, level=logging.NOTSET):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)
        # from https://stackoverflow.com/questions/38543506/change-logging-print-function-to-tqdm-write-so-logging-doesnt-interfere-wit/38739634#38739634
        self.flush()
'''

class ExtractPdf4Tiff(qtc.QObject):
    # Step 1
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

    def pdf4tiff(self, source, destination,firstpage,lastpage):

        args = [
        '-sDEVICE=pdfwrite', ' -dNOPAUSE', ' -dBATCH',
        ' -dSAFER', ' -dFirstPage=' + firstpage, ' -dLastPage=' + lastpage,
        ' -sOutputFile=' + destination + '1516_Page_' + firstpage + '-' + lastpage + '.pdf'
        ]
        gs_cmd = 'gs ' + ' '.join(args) +' '+ source
        
        print("Extracting pages " + firstpage +" through "+ lastpage + " from " + source)
        progstr = f"Extracting pdf pages {firstpage} through {lastpage} from the {source} folder."
        
        self.progress.connect(MainWindow.progress_report)
        self.progress.emit(progstr)
        
        os.system(gs_cmd)
        
        print("Completed extracting pages " + firstpage +" through "+ lastpage + " into " + destination)
        completestr = f"Threaded process complete. Extracted pdf pages are located inside the {destination} folder."
        
        self.finished.connect(MainWindow.process_complete)
        self.finished.emit(completestr)

class ConvertPdf2Tiff(qtc.QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def pdf2tiff(self, source, destination):
        #idx = destination.rindex('.')
        #destination = destination[:idx]
        args = [
        '-q', '-sDEVICE=tiff24nc',
        '-r300', '-sPAPERSIZE=letter', '-sCompression=lzw',
        '-o ' + destination + '1516_Page_%03d.tif'
        ]
        gs_cmd = 'gs ' + ' '.join(args) +' '+ source
        
        progstr = f"Converting extracted pdf pages into tiff files from the {source} folder."
        print(progstr)
        
        self.progress.connect(MainWindow.progress_report)
        self.progress.emit(progstr)
        
        os.system(gs_cmd)

        completestr = f"Threaded process complete.  Converted tiff files are located inside the {destination} folder."
        print(completestr)
        
        self.finished.connect(MainWindow.process_complete)
        self.finished.emit(completestr)

class Move2TiffFolder(qtc.QObject):   
    
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def pdf2tif(source, destination, startpagenum):
        
        def sorted_alphanumeric(data):
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
            return sorted(data, key=alphanum_key)
            #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

        
        #dest_of_tiff = "/home/max/Projects/Python/Images/Source/pdf2tif/"
        #path_of_images = r"/home/max/Projects/Python/Images/Source/pdf4tif/"
        
        path_of_images = source
        dest_of_tiff = destination
        
        list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

        #print(list_of_images)

        newpagenum = int(startpagenum)

        for image in list_of_images:
            
            img = cv2.imread(os.path.join(path_of_images, image))

            # height, width = img.shape[:2]
            
            filestr = os.path.basename(os.path.join(path_of_images, image))
            
            filesplit = os.path.splitext(filestr)
            
            filename = filesplit[0]
            
            fileext = filesplit[1]
            
            namesplit = filename.split("_")
            
            versionref = namesplit[0]
            
            oldpagenum = str(namesplit[2])
            
            pagenum = str(newpagenum).zfill(3)
            
            #print("oldpagenum: " + oldpagenum + "  newpagenum: " + pagenum)
                
            shutil.move(path_of_images + filestr, dest_of_tiff + versionref + "_Page_" + pagenum + ".tif")
            
            newpagenum += 1

            progstr = f"oldpagenum: {oldpagenum} newpagenum: {pagenum}"
            self.progress.emit(progstr)
            self.progress.connect(MainWindow.progress_report(progstr))

        completestr = "Threaded process complete.  Converted tiff files are located inside the " + destination + " folder."
        self.finished.emit(completestr)
        self.finished.connect(MainWindow.process_complete(completestr))

class ConvertTiff2Idx(qtc.QObject): 
    def tiff2tiffidx(source, destination):
        start = time.perf_counter()
        #dest_of_images = "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/"
        #path_of_images = "/home/max/Projects/Python/Images/Source/pdf2tif/"

        path_of_images = source
        dest_of_images = destination
        list_of_images = os.listdir(path_of_images)

        #print(list_of_images)

        for img in list_of_images:
            
            filestr = os.path.basename(os.path.join(path_of_images, img))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            image = cv2.imread(os.path.join(path_of_images, img))
            
            
            #filename = os.path.basename(os.path.join(path_of_images, img))
            #print(filename)

            # convert the image to grayscale and flip the foreground
            # and background to ensure foreground is now "white" and
            # the background is "black"
            gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            inverted = cv2.bitwise_not(gray)
            
            #convert grayscale to binary to be rotated later
            ret, binary = cv2.threshold(image,127,255,cv2.THRESH_BINARY)
        
            PILimage = Image.fromarray(binary)
            thresh = 127
            fn = lambda x : 255 if x > thresh else 0
            PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
            
            outfile = dest_of_images + filename + ".tif"
                
            try:
                print("Generating: " + outfile)
                PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))
            except Exception as e:
                print(e)
        
        finish = time.perf_counter()

        print(f'Finished in {round(finish - start, 2)} seconds(s)')

class ConvertTiff2PngIdx(qtc.QObject): 
    def tiff2pngidx(source, destination):
        
        #path_of_png_images = "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/"
        #path_of_tif_bw_images = r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/"

        path_of_tif_bw_images = source
        path_of_png_images = destination
        list_of_images = os.listdir(path_of_tif_bw_images)

        for image in list_of_images:
            
            # Open the selected large .tif image. 
            bw_image = Image.open(os.path.join(path_of_tif_bw_images, image))
            
            # separate .tif extension for original filename
            filestr = os.path.basename(os.path.join(path_of_tif_bw_images, image))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            # Designate .png output path/filename
            outfile = path_of_png_images + filename + ".png"
            
            try:
                print("Generating: " + outfile)
                bw_image.save(outfile, "PNG", quality=100, dpi=(300,300))
                #my_img_resized.save(outfile, "PNG")
            except Exception as e:
                print(e)

class DeskewTiffPng(qtc.QObject): 
    def deskewfiles(source, pngdest, tifdest):
        
            # Calculate skew angle of an image
        def getSkewAngle(cvImage) -> float:
            # Prep image, copy, convert to gray scale, blur, and threshold
            newImage = cvImage.copy()
            gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (9, 9), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Apply dilate to merge text into meaningful lines/paragraphs.
            # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
            # But use smaller kernel on Y axis to separate between different blocks of text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
            dilate = cv2.dilate(thresh, kernel, iterations=5)

            # Find all contours
            dilated, contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key = cv2.contourArea, reverse = True)

            # Find largest contour and surround in min area box
            largestContour = contours[0]
            minAreaRect = cv2.minAreaRect(largestContour)

            # Determine the angle. Convert it to the value that was originally used to obtain skewed image
            angle = minAreaRect[-1]
            if angle < -45:
                angle = 90 + angle
            return -1.0 * angle

        # Rotate the image around its center
        def rotateImage(cvImage, angle: float):
            newImage = cvImage.copy()
            (h, w) = newImage.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return newImage

        # Deskew image
        def deskew(cvImage):
            angle = getSkewAngle(cvImage)
            # show the angle info
            print(filename + "[INFO] angle: {:.3f}".format(angle))
            return rotateImage(cvImage, -1.0 * angle)

        #dest_of_tif_images = "/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/"
        #dest_of_png_images = "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/"
        #path_of_images = "/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/"
        
        path_of_images = source
        dest_of_tif_images = tifdest
        dest_of_png_images = pngdest

        
        list_of_images = os.listdir(path_of_images)

        print(list_of_images)

        for img in list_of_images:
            
            filestr = os.path.basename(os.path.join(path_of_images, img))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            image = cv2.imread(os.path.join(path_of_images, img))

            #print(filename + "[INFO] angle: {:.3f}".format(angle))
            newImage = deskew(image)

            #write rotated file to destination folder
            PILimage = Image.fromarray(newImage)
            thresh = 127
            fn = lambda x : 255 if x > thresh else 0
            PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
            
            tif_outfile = dest_of_tif_images + filename + ".tif"
            png_outfile = dest_of_png_images + filename + ".png"
                
            try:
                print("Generating: " + tif_outfile)
                PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))
                
                print("Generating: " + png_outfile)
                PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
                #my_img_resized.save(outfile, "PNG")
            except Exception as e:
                print(e)

class CropGreekLatin(qtc.QObject):
    def croplangs(source, boxdir, greekdir, latindir, elimdir):

        dest_of_elimination = elimdir
        dest_of_greek = greekdir
        dest_of_latin = latindir
        dest_of_box = boxdir
        path_of_images = source
        
        list_of_images = os.listdir(path_of_images)
        for image in list_of_images:
            
                img = cv2.imread(os.path.join(path_of_images, image))

                filestr = os.path.basename(os.path.join(path_of_images, image))
                filesplit = os.path.splitext(filestr)
                filename = filesplit[0]
                fileext = filesplit[1]
                
                #filename = os.path.basename(os.path.join(path_of_images, image))
        #load the image
        #image = cv2.imread(args["image"])
        #image = cv2.imread("./Images/tif_newtest/1516_Page_002.tif")
        #cv2.imshow('orig',image)
        #cv2.waitKey(0)

        #grayscale
                gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #cv2.imshow('gray',gray)
        #cv2.waitKey(0)read 

        #binary 
                ret,binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)

        #binary inversion
                ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
        #cv2.imshow('thresh',thresh)
        #cv2.waitKey(0)

        #dilation
                kernel = np.ones((70,100), np.uint8)
                img_dilation = cv2.dilate(thresh, kernel, iterations=1)
        #cv2.imshow('dilated',img_dilation)
                #cv2.imwrite((image+'dilation.tif'),img_dilation)
        #cv2.waitKey(0)

        #medianblur
                #median = cv2.medianBlur(img_dilation, 17)
        #cv2.imshow('medianblur',median)
        #cv2.imwrite('medianblur.tif',median)
        #cv2.waitKey(0)

        #find contours
                im2,ctrs, hier = cv2.findContours(img_dilation.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #set flags for sorting contours top to bottom
                reverse = False
                i = 0

        # construct the list of bounding boxes and sort them from left to right
                boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
                (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes), key=lambda b:b[1][i], reverse=reverse))

        # Set initial box count
                bnum = 1
                destfolder = ""
                deststr = ""

                for i,c in enumerate(ctrs):
                
                        # Get bounding box
                        x, y, w, h = cv2.boundingRect(c)
                        
                        # Get ROI
                        roi = binary[y:y+h, x:x+w]
                        
                        # Set height validation of contour to eliminate unwanted ROI's
                        if w > 1600 and h > 4000:
                                                        
                                if bnum==1:
                                        destfolder = dest_of_greek
                                        deststr = 'greek'
                                        bnum = bnum + 1
                                else:
                                        destfolder = dest_of_latin
                                        deststr = 'latin'
                                        bnum = 1

                                if destfolder!="":
                                        # Write accepted ROI to correct folder/file
                                        PILimage = Image.fromarray(roi)
                                        thresh = 127
                                        fn = lambda x : 255 if x > thresh else 0
                                        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                                        outfile = destfolder+deststr+filename + ".tif"
                                        print("Generating: " + outfile)
                                        PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))
                                        
                                        #cv2.imwrite(destfolder+deststr+filename, roi)
                                        # Draw box around accepted ROI
                                        cv2.rectangle(binary,(x,y),( x + w, y + h ),(90,0,255),2)
                                else:
                                        pass
                        else:
                                # Eliminate smaller ROI as noise but save to eliminated folder/file anyway
                                cv2.imwrite(dest_of_elimination + filename + "segment-" + str(i) + fileext, roi)
                        
                cv2.imwrite(os.path.join(dest_of_box, filename + fileext),binary)

class ResizePng(qtc.QObject):
    def resizepngs(source, destination):

        path_of_png_resized = destination
        path_of_png_deskew = source

        list_of_images = os.listdir(path_of_png_deskew)

        for image in list_of_images:
            
            # Open the selected large .tif image. 
            big_image = Image.open(os.path.join(path_of_png_deskew, image))
            
            # separate .tif extension for original filename
            filestr = os.path.basename(os.path.join(path_of_png_deskew, image))
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
            
            # Resize image to original proportions to maintain aspect ratio
            (width,height) = big_image.size
            aspect_ratio = ((width/height))
            print("Aspect Ratio: " + str(aspect_ratio))
            new_width = (width/4)
            new_height = (new_width/aspect_ratio)
            my_img_resized = big_image.resize((int(new_width), int(new_height))) 
            
            # Designate .jpg output path/filename
            outfile = path_of_png_resized + filename + ".png"
            
            try:
                print("Generating: " + outfile)
                my_img_resized.save(outfile, "PNG", quality=100)
            except Exception as e:
                print(e)

# Define a stream, custom class, that reports data written to it, with a Qt signal
class Streamer(qtc.QObject):

    textWritten = qtc.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

class MainWindow(qtw.QMainWindow):
    '''The Main Window Object'''
    
    worker_requested = pyqtSignal()
    
    # Menu and Toolbar Action Methods 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:
        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_MainUI()
        self.ui.setupUi(self)

        # extended slots code
        self.ui.actionOpen_Image.triggered.connect(self.OpenImageFileDialog)
        self.ui.actionVerse_Correction.triggered.connect(self.actionVerse_Correction)
        
        self.ui.actionextract_pdf_tb.triggered.connect(self.actionextract_pdf)      
        self.ui.actionpdf_for_tiff_tb.triggered.connect(self.actionpdf_for_tiff)
        self.ui.actionpdf_to_tiff_tb.triggered.connect(self.actionpdf_to_tiff)
        self.ui.actiontiff_to_mono_tb.triggered.connect(self.actiontiff_to_mono)
        self.ui.actiondeskew_mono.triggered.connect(self.actiondeskew_mono)
        self.ui.actionmono_to_png_tb.triggered.connect(self.actionmono_to_png)
        self.ui.actionCrop_Languages_tb.triggered.connect(self.actionCrop_Languages)
        self.ui.actionDeskewGreek_tiff_tb.triggered.connect(self.actionDeskewGreek_tiff)
        self.ui.actionResizeGreek_png_tb.triggered.connect(self.actionResizeGreek_png)
        self.ui.actionDeskewLatin_tiff_tb.triggered.connect(self.actionDeskewLatin_tiff)
        self.ui.actionResizeLatin_png_tb.triggered.connect(self.actionResizeLatin_png)
        
        self.ui.actionCrop_Greek_to_tiff_Lines_tb.triggered.connect(self.actionCrop_Greek_To_tiff_Lines)
        self.ui.actionRename_Greek_tiff_Lines_tb.triggered.connect(self.actionRename_Greek_tiff_Lines)
        self.ui.actionMove_Greek_tiff_Lines_tb.triggered.connect(self.actionMove_Greek_tiff_Lines)
        
        self.ui.actionCrop_Latin_To_tiff_Lines_tb.triggered.connect(self.actionCrop_Latin_To_tiff_Lines)
        self.ui.actionRename_Latin_tiff_Lines_tb.triggered.connect(self.actionRename_Latin_tiff_Lines)
        self.ui.actionMove_Latin_tiff_Lines_tb.triggered.connect(self.actionMove_Latin_tiff_Lines)
        
        self.ui.actionSplitGreek_text_lines_tb.triggered.connect(self.actionSplitGreek_text_lines)
        self.ui.actionRenameGreek_text_lines_tb.triggered.connect(self.actionRenameGreek_text_lines)
        
        self.ui.actionSplit_Latin_Text_Lines_tb.triggered.connect(self.actionSplit_Latin_Text_Lines)
        self.ui.actionRename_Latin_Text_Lines_tb.triggered.connect(self.actionRename_Latin_Text_Lines)
        
        self.ui.actionReview_Ground_Truth_tb.triggered.connect(self.actionReview_Ground_Truth)
        self.ui.actionUpdate_Wordlist_tb.triggered.connect(self.actionUpdate_Wordlist)
        self.ui.actionTrain_Tesseract_tb.triggered.connect(self.actionTrain_Tesseract)
        self.ui.actionCorrect_OCR_tb.triggered.connect(self.actionCorrect_OCR)

        self.ui.OCRbutton.clicked.connect(self.GetRawOCRtext)       
        self.ui.SetLineSpacingbutton.clicked.connect(self.SetLineSpacing)
        self.ui.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        self.ui.SaveAsOCRCorrTextbutton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)         
        self.ui.OpenImageFilebutton.clicked.connect(self.OpenImageFileDialog)
        
        # UI and slots code ends here.
        
        # Show the Main user interface
        self.ui.OCRDocument = qtg.QTextDocument(self.ui.OCRText)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(20)
        self.ui.OCRDocument.setDefaultFont(font)
        
        self.ui.OCRDocument.setDefaultFont(font)
        self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
        self.ui.OCRTextFormat = qtg.QTextFormat()
        self.ui.OCRCursor = qtg.QTextCursor(self.ui.OCRDocument)
        
        self.ui.OCRText.setDocument(self.ui.OCRDocument)

        ChrRefText = open('/home/max/Projects/Python/Workflow/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        '''
        # Install a custom output stream by connecting sys.stdout to instance of Streamer.
        #sys.stdout = Streamer(textWritten=self.output_terminal_written)
        
        
        #setup_logging(self.__class__.__name__)
        #self.__logger = logging.getLogger(self.__class__.__name__)
        #self.__logger.setLevel(logging.DEBUG)

        # create console text queue
        self.queue_console_text = Queue()
        # redirect stdout to the queue
        output_stream = WriteStream(self.queue_console_text)
        sys.stdout = output_stream

        #self.thread_initialize = qtc.QThread()
        #self.init_procedure_object = InitializationProcedures(self)

        # create console text read thread + receiver object
        self.thread_queue_listener = qtc.QThread()
        self.console_text_receiver = ThreadConsoleTextQueueReceiver(self.queue_console_text)
        
        # connect receiver object to widget for text update
        self.console_text_receiver.queue_element_received_signal.connect(self.append_text)
        
        # attach console text receiver to console text thread
        self.console_text_receiver.moveToThread(self.thread_queue_listener)
        
        # attach to start / stop methods
        self.thread_queue_listener.started.connect(self.console_text_receiver.run)
        self.thread_queue_listener.finished.connect(self.console_text_receiver.finished)
        self.thread_queue_listener.start()'''

        self.show()
 
    #@qtc.pyqtSlot(str)
    def progress_report(self, progstr):
        self.ui.OutputText.append(progstr)
    
    #@qtc.pyqtSlot(str)
    def process_complete(self, completestr):
        self.ui.OutputText.append(completestr)

    @qtc.pyqtSlot(str)
    def thread_complete(self, completestr):
        self.ui.OutputText.append(completestr)
        
    '''@qtc.pyqtSlot(str)
    def append_text(self,text):
        #self.ui.OutputText.moveCursor(QTextCursor.End)
        #self.ui.OutputText.insertPlainText(text)
        self.ui.OutputText.append(text)
    
    @qtc.pyqtSlot()
    def start_thread(self):
        self.thread = qtc.QThread()
        #self.long_running_thing = LongRunningThing()
        #self.long_running_thing.moveToThread(self.thread)
        #self.thread.started.connect(self.long_running_thing.run)
        self.thread.start()'''

    '''def onUpdateText(self, text):
        cursor = self.process.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.process.setTextCursor(cursor)
        self.process.ensureCursorVisible()'''
    
    #custom method to write anything printed out to console/terminal to my QTextEdit widget via append function.
    def output_terminal_written(self, text):
        self.ui.OutputText.append(text)
    
    def actionextract_pdf(self):
        '''print("extracting pdf pages from source pdf")
        #usage: pdf4tiff(source, destination,firstpage,lastpage)
        pp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60') 
        #mpp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60')
        print("pdf page extraction complete")'''

        '''with Popen(pp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60'), stdout=PIPE, bufsize=1, universal_newlines=True) as p:
            for b in p.stdout:
                print(b, end='') # b is the byte from stdout

        if p.returncode != 0:
            raise CalledProcessError(p.returncode, p.args)'''

        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = ExtractPdf4Tiff()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60'))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect()
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.thread.finished.connect(self.thread_complete("Worker thread completed"))
        
    def actionpdf_for_tiff(self):
        '''print("converting pdf for tiff")
        #usage: pdf2tiff(source, destination)
        #pp.pdf2tiff('./Images/Source/pdf_source/1516_Page_51-60.pdf', './Images/Source/pdf4tif/')
        pp.pdf2tiff('./Images/Source/pdf_source/1516_Page_51-60.pdf', './Images/Source/pdf4tif/')
        print("pdf for tiff conversion complete")'''

        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = ConvertPdf2Tiff()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.pdf2tiff('./Images/Source/pdf_source/1516_Page_51-60.pdf', './Images/Source/pdf4tif/'))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect()
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.thread.finished.connect(self.thread_complete("Worker thread completed"))

    def actionpdf_to_tiff(self):
        print("converting pdf to tiff")
        #usage: pdf2tif(source, destination, startpagenum)
        #pp.pdf2tif(r"/home/max/Projects/Python/Images/Source/pdf4tif/", "/home/max/Projects/Python/Images/Source/pdf2tif/","51")
        pp.pdf2tif(r"/home/max/Projects/Python/Images/Source/pdf4tif/", "/home/max/Projects/Python/Images/Source/pdf2tif/","51")
        print("pdf to tiff conversion complete")

    def actiontiff_to_mono(self):
        print("creating indexed(BW) tiff")
        #usage: pp.tiff2tiffidx(source, destination)
        pp.tiff2tiffidx("/home/max/Projects/Python/Images/Source/pdf2tif/", "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/")
        #mpp.tiff2tiffidx("/home/max/Projects/Python/Images/Source/pdf2tif/", "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/")

    def actiondeskew_mono(self):
        print("deskewing monochrome tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/png_black_white_deskew/","/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/")
        pp.deskewfiles("/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/png_black_white_deskew/","/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/")

    def actionmono_to_png(self):
        print("creating indexed(BW) png")
        #usage: pp.tiff2pngidx(source, destination)
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        
    def actionCrop_Languages(self):
        print("creating indexed(BW) png")
        #usage: pp.croplangs(source, boxdir, greekdir, latindir, elimdir)
        #pp.croplangs(r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_40_Matthew/")
        pp.croplangs(r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_40_Matthew/")
    
    def actionDeskewGreek_tiff(self):
        print("deskewing Greek tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
        pp.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
    
    def actionResizeGreek_png(self):
        print("resizing Greek png files")
        #usage: pp.resizepngs(source, destination)
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
        pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
    
    def actionDeskewLatin_tiff(self):
        print("deskewing Latin tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
        pp.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
    
    def actionResizeLatin_png(self):
        print("resizing Latin png files")
        #usage: pp.resizepngs(source, destination)
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
        pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")

    def actionCrop_Greek_To_tiff_Lines(self):
        print("cropping and sorting Greek tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")
        tr.sortcroplines(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")
        
    def actionRename_Greek_tiff_Lines(self):
        print("renaming Greek tiff lines for ground truth")
        # usage: tr.renameimages(source, destination)
        # tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
       
    def actionMove_Greek_tiff_Lines(self):
        pass

    def actionCrop_Latin_To_tiff_Lines(self):
        print("cropping and sorting Latin tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")
        tr.sortcroplines(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")

    def actionRename_Latin_tiff_Lines(self):
        print("renaming Latin tiff lines for ground truth")
        # usage: tr.renameimages(source, destination)
        # tr.renameimages(r"/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")
        tr.renameimages(r"/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")

    def actionMove_Latin_tiff_Lines(self):
        pass

    def actionSplitGreek_text_lines(self):
        print("splitting Greek textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        # tr.splittextlines(r"/home/max/Projects/Python/EstablishTruth/Greek txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/")
        tr.splittextlines("/home/max/Projects/Python/EstablishTruth/Greek txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/")
        
    def actionRenameGreek_text_lines(self):
        print("renaming Greek textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
        tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
    
    def actionSplit_Latin_Text_Lines(self):
        print("splitting Latin textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        # tr.splittextlines(r"/home/max/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/")
        tr.splittextlines("/home/max/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/")

    def actionRename_Latin_Text_Lines(self):
        print("renaming Latin textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
        tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
    
    def actionReview_Ground_Truth(self):
        gtr.MainWindow = qtw.QMainWindow()
        gtr.ui = gtr.Ui_MainWindow()
        gtr.ui.setupUi(gtr.MainWindow)
        gtr.MainWindow.show()

    def actionVerse_Correction(self):
        versify.MainWindow = qtw.QMainWindow()
        versify.ui = versify.Ui_MainWindow()
        versify.ui.setupUi(versify.MainWindow)
        versify.MainWindow.show()
    
    def actionUpdate_Wordlist(self):
        pass
    
    def actionTrain_Tesseract(self):
        pass
    
    def actionCorrect_OCR(self):
        print("performing OCR on current image")
        self.GetRawOCRtext()

    def setImageStack(self, tiffCaptureHandle):
            """ Set the scene's current TIFF image stack to the input TiffCapture object.
            Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
            :type tiffCaptureHandle: TiffCapture
            """
            if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
                raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
            self._tiffCaptureHandle = tiffCaptureHandle
            self.showFrame(0)

    def loadImageStackFromFile(self,fileName=''):
        """ Load an image stack from file.
        Without any arguments, loadImageStackFromFile() will popup a file dialog to choose the image file.
        With a fileName argument, loadImageStackFromFile(fileName) will attempt to load the specified file directly.
        """
        if len(fileName) == 0:
            if QT_VERSION_STR[0] == '4':
                fileName = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
            elif QT_VERSION_STR[0] == '5':
                fileName, dummy = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
        fileName = str(fileName)
        if len(fileName) and os.path.isfile(fileName):
            self._tiffCaptureHandle = tiffcapture.opentiff(fileName)
            
    def numFrames(self):
        """ Return the number of image frames in the stack.
        """
        if self._tiffCaptureHandle is not None:
            # !!! tiffcapture has length=0 for a single page TIFF.
            # If our handle is valid, we'll assume we have at least one image.
            return max([1, self._tiffCaptureHandle.length])
        return 0

    def getFrame(self, i=None):
        """ Return the i^th image frame as a NumPy ndarray.
        If i is None, return the current image frame.
        """
        if self._tiffCaptureHandle is None:
            return None
        if i is None:
            i = self.currentFrameIndex
        if (i is None) or (i < 0) or (i >= self.numFrames()):
            return None
        return self._tiffCaptureHandle.find_and_read(i)

    def showFrame(self, i=None):
        """ Display the i^th frame in the viewer.
        Also update the frame slider position and current frame text.
        """
        self.frame = self.getFrame(i)
        if self.frame is None:
            return
        # Convert frame ndarray to a QImage.
        self.qimage = qimage2ndarray.array2qimage(self.frame, normalize=True)
    
    def OpenImageFileDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open image file', '',
            'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
                
        if self.path:
            file = qtc.QFile(self.path)
            filestr = os.path.basename(self.path)
            self.ui.ImageLe.setText(filestr)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
                        
            if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(self.path)
                
                if fileext == '.tif':
                    self.loadImageStackFromFile(str(self.path))
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)
                    self.ui.Image.setPixmap(qtg.QPixmap(pixmap))
                else:
                    
                    self.ui.Image.setPixmap(qtg.QPixmap(self.path))
                
                file.close()
    
    def GetRawOCRtext(self):
        my_OCR_rawtext = pytesseract.image_to_string(self.path,lang="feg")
        self.ui.OCRText.insertPlainText(my_OCR_rawtext)
        '''path = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open tif image file', '',
            'Images (*.tif)')[0]
        if path:
            file = qtc.QFile(path)
            if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.ui.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.ui.OCRText.insertPlainText(my_OCR_rawtext)
                file.close()'''
    
    def SetLineSpacing(self, MainWindow):
        num,ok = qtw.QInputDialog.getInt(self.ui.centralwidget,"Proportional Line Spacing","Enter a percent value from 0-200")
        if ok:
            lineSpacing = num
        else:
            lineSpacing = 145
            
        cursor = self.ui.OCRText.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.OCRCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.OCRBlockFormat.ProportionalHeight) 
        cursor.mergeBlockFormat(bf)
    
    def OpenTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if path:
            file = qtc.QFile(path)
            filename = os.path.basename(path)
            self.ui.TextLE.setText(filename)
            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(path)
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text)
                    self.ui.OCRText.insertPlainText(text)
                else:
                    self.ui.OCRText.setPlainText(text)
                file.close()
        
    def SaveRawTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Raw text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.ui.OCRDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()
        
    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        
        defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek txt pages/greek_book_40_Matthew/"
        defaultfile = self.ui.TextLE.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        
        self.ui.TextLE.setText(filename)
        file.close()

# Only run this code if I am actually running this script
if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec())