from .wia_scanner import WIAScanner


class ScannerManager:

    def __init__(self):
        self.wia = WIAScanner()

    def discover_devices(self):
        return self.wia.list_devices()
    
    def acquire(self, destination_folder):
        return self.wia.acquire(destination_folder)

    # def acquire(self):
    #     return self.wia.acquire()

    def acquire_qimage(self):
        return self.wia.acquire_qimage()