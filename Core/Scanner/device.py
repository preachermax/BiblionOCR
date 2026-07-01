class ScannerDevice:

    def discover(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def acquire(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError