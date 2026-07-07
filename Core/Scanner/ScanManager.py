import platform
import os
from PyQt5.QtGui import QImage
from .escl_scanner import ESCLScanner
from .sane_scanner import SaneScanner
from .twain_scanner import TwainScanner
from .wia_scanner import WIAScanner


class ScanManager:
    REQUEST_FIELDS = (
        "destination_folder",
        "backend_preference",
        "device_name",
        "allow_network_fallback",
        "mode",
        "dpi",
        "source_type",
        "duplex",
        "persist_format",
    )

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
            "allow_network_fallback": True,
            "mode": "color",
            "dpi": 300,
            "source_type": "flatbed",
            "duplex": False,
            "persist_format": "tiff",
        }

    def request_from_state(self, state, destination_folder):
        request = self.default_request(destination_folder)
        for field_name in self.REQUEST_FIELDS:
            request[field_name] = getattr(state, f"scan_{field_name}", request[field_name])
        return self.normalize_request(request, destination_folder)

    def normalize_request(self, request, destination_folder=None):
        scan_request = self.default_request(destination_folder or (request or {}).get("destination_folder"))
        scan_request.update(request or {})

        destination_folder = scan_request.get("destination_folder")
        if not destination_folder:
            raise RuntimeError("Scan request is missing destination_folder")

        scan_request["destination_folder"] = destination_folder
        scan_request["backend_preference"] = scan_request.get("backend_preference") or ESCLScanner.__name__
        scan_request["device_name"] = scan_request.get("device_name") or ""
        scan_request["allow_network_fallback"] = self._coerce_bool(
            scan_request.get("allow_network_fallback", True),
            default=True,
        )
        scan_request["dpi"] = self._coerce_int(scan_request.get("dpi"), default=300)
        scan_request["source_type"] = scan_request.get("source_type") or "flatbed"
        scan_request["mode"] = scan_request.get("mode") or "color"
        scan_request["duplex"] = self._coerce_bool(scan_request.get("duplex"), default=False)
        scan_request["persist_format"] = scan_request.get("persist_format") or "tiff"

        os.makedirs(destination_folder, exist_ok=True)
        return scan_request

    def apply_request_state(self, target, request, destination_folder=None):
        normalized_request = self.normalize_request(request, destination_folder)
        for field_name in self.REQUEST_FIELDS:
            setattr(target, f"scan_{field_name}", normalized_request[field_name])
        return normalized_request

    def session_payload(self, request, destination_folder=None, pending_scan_handoff=None):
        normalized_request = self.normalize_request(request, destination_folder)
        payload = {
            f"self.scan_{field_name}": normalized_request[field_name]
            for field_name in self.REQUEST_FIELDS
        }
        if pending_scan_handoff is not None:
            payload["self.pending_scan_handoff"] = bool(pending_scan_handoff)
        return payload

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
        return self.normalize_request(request)

    def _coerce_bool(self, value, default=False):
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _coerce_int(self, value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

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