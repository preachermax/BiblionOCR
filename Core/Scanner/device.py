from PyQt5.QtGui import QImage


class ScannerDevice:
    backend_name = "scanner"

    @classmethod
    def is_supported_platform(cls, platform_name):
        return True

    @classmethod
    def is_available(cls):
        return False

    def discover(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def acquire(self, destination_folder, request=None):
        raise RuntimeError(f"{self.backend_name} backend is not available")

    def acquire_qimage(self, destination_folder, request=None):
        result = self.acquire(destination_folder, request=request)
        path = result.get("path") if isinstance(result, dict) else None
        if not path:
            raise RuntimeError(f"{self.backend_name} backend did not return a file path")

        qimage = QImage(path)
        if qimage.isNull():
            raise RuntimeError(f"Failed to load scanned image from {path}")
        return qimage

    def disconnect(self):
        raise NotImplementedError