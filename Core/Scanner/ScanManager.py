import platform
import os
from PyQt5.QtGui import QImage
from .escl_scanner import ESCLScanner
from .sane_scanner import SaneScanner
from .twain_scanner import TwainScanner
from .wia_scanner import WIAScanner


class ScanManager:
    BACKEND_PRIORITY = (
        ESCLScanner,
        SaneScanner,
        TwainScanner,
        WIAScanner,
    )

    def __init__(self):
        self._backend = None
        self._platform = platform.system().lower()

    def backend_options(self):
        options = []
        for backend_class in self.BACKEND_PRIORITY:
            if not backend_class.is_supported_platform(self._platform):
                continue
            availability = backend_class.availability_details()
            options.append(
                {
                    "value": backend_class.__name__,
                    "label": backend_class.backend_name,
                    "available": availability.get("available", False),
                    "unavailable_reason": availability.get("reason"),
                }
            )
        return options

    def backend_option(self, backend_name):
        for option in self.backend_options():
            if option["value"] == backend_name:
                return option
        return None

    def default_request(self, destination_folder):
        return {
            "destination_folder": destination_folder,
            "backend_preference": ESCLScanner.__name__,
            "device_name": "",
            "mode": "color",
            "dpi": 300,
            "source_type": "flatbed",
            "duplex": False,
            "persist_format": "tiff",
        }

    def discover_devices(self, request=None):
        backend = self._get_backend(request or {"backend_preference": "auto"}, required=False)
        if backend is None:
            return []
        return backend.list_devices()

    def acquire(self, destination_folder):
        return self.run_scan({"destination_folder": destination_folder})

    def acquire_qimage(self, destination_folder):
        backend = self._get_backend({"backend_preference": "auto"}, required=True)
        return backend.acquire_qimage(destination_folder, request={"destination_folder": destination_folder})

    def run_scan(self, request):
        request = self._normalize_request(request)
        destination_folder = request["destination_folder"]
        backend = self._get_backend(request, required=True)

        result = backend.acquire(destination_folder, request=request)
        if not isinstance(result, dict):
            raise RuntimeError("Scanner backend returned an invalid result")

        path = result.get("path")
        if not path:
            raise RuntimeError("Scanner backend did not return a scanned file path")

        result.setdefault("dir", destination_folder)
        result["backend"] = backend.__class__.__name__
        result["backend_label"] = getattr(backend, "backend_name", backend.__class__.__name__)
        result["platform"] = self._platform
        result["request"] = request
        result["status"] = "success"
        return result

    def load_qimage(self, result):
        path = result.get("path")
        if not path:
            raise RuntimeError("Scan result does not contain a file path")

        qimage = QImage(path)
        if qimage.isNull():
            raise RuntimeError(f"Failed to load scanned image from {path}")
        return qimage

    def _normalize_request(self, request):
        scan_request = self.default_request((request or {}).get("destination_folder"))
        scan_request.update(request or {})

        destination_folder = scan_request.get("destination_folder")
        if not destination_folder:
            raise RuntimeError("Scan request is missing destination_folder")

        os.makedirs(destination_folder, exist_ok=True)
        scan_request["destination_folder"] = destination_folder
        return scan_request

    def _get_backend(self, request, required):
        if self._backend is not None:
            if self._matches_preference(self._backend, request):
                return self._backend

        backend_preference = (request or {}).get("backend_preference", "auto")
        if backend_preference != "auto":
            backend_class = self._backend_class_by_name(backend_preference)
            if backend_class is None:
                raise RuntimeError(f"Unknown scanner backend preference: {backend_preference}")
            if not backend_class.is_supported_platform(self._platform):
                raise RuntimeError(
                    f"Scanner backend {backend_class.backend_name} is not supported on {self._platform}"
                )
            if not backend_class.is_available():
                availability = backend_class.availability_details()
                reason = availability.get("reason")
                if reason:
                    raise RuntimeError(reason)
                raise RuntimeError(
                    f"Scanner backend {backend_class.backend_name} is not currently available"
                )

            self._backend = backend_class()
            return self._backend

        for backend_class in self.BACKEND_PRIORITY:
            if not backend_class.is_supported_platform(self._platform):
                continue
            if not backend_class.is_available():
                continue

            self._backend = backend_class()
            return self._backend

        if required:
            raise RuntimeError(
                "No supported scanner backend is available for platform: "
                f"{self._platform}. Backend priority is eSCL / AirScan, SANE, TWAIN, WIA."
            )

        return None

    def _backend_class_by_name(self, backend_name):
        for backend_class in self.BACKEND_PRIORITY:
            if backend_class.__name__ == backend_name:
                return backend_class
        return None

    def _matches_preference(self, backend, request):
        backend_preference = (request or {}).get("backend_preference", "auto")
        if backend_preference == "auto":
            return True
        return backend.__class__.__name__ == backend_preference