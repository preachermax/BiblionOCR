# coding=utf-8

import time
import logging
import sys
import datetime
__is_setup_done = False

from queue import Queue

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QMetaObject, Q_ARG, Qt
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit, QWidget, QToolButton, QVBoxLayout, QApplication
from tqdm.auto import tqdm


class MainApp(QWidget):
    def __init__(self):
        super().__init__()

        setup_logging(self.__class__.__name__)


        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.setLevel(logging.DEBUG)

        # create console text queue
        self.queue_console_text = Queue()
        # redirect stdout to the queue
        output_stream = WriteStream(self.queue_console_text)
        sys.stdout = output_stream

        layout = QVBoxLayout()

        self.setMinimumWidth(500)

        # GO button
        self.btn_perform_actions = QToolButton(self)
        self.btn_perform_actions.setText('Launch long processing')
        self.btn_perform_actions.clicked.connect(self._btn_go_clicked)

        self.console_text_edit = ConsoleTextEdit(self)

        self.thread_initialize = QThread()
        self.init_procedure_object = InitializationProcedures(self)

        # create console text read thread + receiver object
        self.thread_queue_listener = QThread()
        self.console_text_receiver = ThreadConsoleTextQueueReceiver(self.queue_console_text)
        # connect receiver object to widget for text update
        self.console_text_receiver.queue_element_received_signal.connect(self.console_text_edit.append_text)
        # attach console text receiver to console text thread
        self.console_text_receiver.moveToThread(self.thread_queue_listener)
        # attach to start / stop methods
        self.thread_queue_listener.started.connect(self.console_text_receiver.run)
        self.thread_queue_listener.finished.connect(self.console_text_receiver.finished)
        self.thread_queue_listener.start()

        layout.addWidget(self.btn_perform_actions)
        layout.addWidget(self.console_text_edit)
        self.setLayout(layout)
        self.show()

    @pyqtSlot()
    def _btn_go_clicked(self):
        # prepare thread for long operation
        self.init_procedure_object.moveToThread(self.thread_initialize)
        self.thread_initialize.started.connect(self.init_procedure_object.run)
        self.thread_initialize.finished.connect(self.init_procedure_object.finished)
        # start thread
        self.btn_perform_actions.setEnabled(False)
        self.thread_initialize.start()


class WriteStream(object):
    def __init__(self, q: Queue):
        self.queue = q

    def write(self, text):
        """
        Redirection of stream to the given queue
        """
        self.queue.put(text)

    def flush(self):
        """
        Stream flush implementation
        """
        pass


class ThreadConsoleTextQueueReceiver(QObject):
    queue_element_received_signal = pyqtSignal(str)

    def __init__(self, q: Queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = q

    @pyqtSlot()
    def run(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Started <---\n')
        while True:
            text = self.queue.get()
            self.queue_element_received_signal.emit(text)

    @pyqtSlot()
    def finished(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Stopped <---\n')


class ConsoleTextEdit(QTextEdit):#QTextEdit):
    def __init__(self, parent):
        super(ConsoleTextEdit, self).__init__()
        self.setParent(parent)
        self.setReadOnly(True)
        self.setLineWidth(50)
        self.setMinimumWidth(1200)
        self.setFont(QFont('Consolas', 11))
        self.flag = False

    @pyqtSlot(str)
    def append_text(self, text: str):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)

def long_procedure():
    setup_logging('long_procedure')
    __logger = logging.getLogger('long_procedure')
    __logger.setLevel(logging.DEBUG)
    for i in tqdm(range(10), unit_scale=True, dynamic_ncols=True):
        time.sleep(.1)
        __logger.info('foo {}'.format(i))


class InitializationProcedures(QObject):
    def __init__(self, main_app: MainApp):
        super(InitializationProcedures, self).__init__()
        self._main_app = main_app

    @pyqtSlot()
    def run(self):
        long_procedure()

    @pyqtSlot()
    def finished(self):
        print("Thread finished !")  # might call main window to do some stuff with buttons
        self._main_app.btn_perform_actions.setEnabled(True)

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

if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    tqdm.ncols = 50
    ex = MainApp()
    sys.exit(app.exec_())
