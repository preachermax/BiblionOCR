import os

try:
    import sane
except ImportError:
    sane = None

try:
    from PIL import Image
except ImportError:
    Image = None

from .device import ScannerDevice


class SaneScanner(ScannerDevice):
    backend_name = "SANE"

    @classmethod
    def is_supported_platform(cls, platform_name):
        return platform_name in {"linux", "darwin"}

    @classmethod
    def is_available(cls):
        return sane is not None and Image is not None

    def __init__(self):
        if sane is None or Image is None:
            raise RuntimeError("SANE scanning requires python-sane and Pillow")

    def list_devices(self):
        sane.init()
        try:
            devices = sane.get_devices()
            return [self._display_name(device) for device in devices]
        finally:
            sane.exit()

    def acquire(self, destination_folder, request=None):
        request = request or {}
        sane.init()
        device_handle = None
        try:
            devices = sane.get_devices()
            if not devices:
                raise RuntimeError("SANE did not report any scanner devices")

            device_info = self._select_device(devices, request.get("device_name"))
            device_handle = sane.open(device_info[0])
            self._configure_device(device_handle, request)

            image = device_handle.start()
            if image is None:
                raise RuntimeError("SANE scan did not return any image data")

            normalized_image = self._normalize_image_mode(image, request.get("mode", "color"))
            path = self._save_image(normalized_image, destination_folder)
            return {
                "path": path,
                "dir": destination_folder,
                "device": self._display_name(device_info),
            }
        finally:
            if device_handle is not None:
                try:
                    device_handle.close()
                except Exception:
                    pass
            sane.exit()

    def _select_device(self, devices, requested_name):
        if not requested_name:
            return devices[0]

        normalized_requested = str(requested_name).strip().lower()
        for device in devices:
            device_name = str(device[0]).strip().lower()
            display_name = self._display_name(device).strip().lower()
            if normalized_requested in {device_name, display_name}:
                return device
        for device in devices:
            device_name = str(device[0]).strip().lower()
            display_name = self._display_name(device).strip().lower()
            if normalized_requested in device_name or normalized_requested in display_name:
                return device

        raise RuntimeError(f"SANE device not found: {requested_name}")

    def _configure_device(self, device_handle, request):
        mode_map = {
            "color": "Color",
            "grayscale": "Gray",
            "mono": "Lineart",
        }
        requested_mode = mode_map.get(request.get("mode", "color"), "Color")
        requested_dpi = int(request.get("dpi", 300))

        try:
            device_handle.mode = requested_mode
        except Exception:
            pass

        try:
            device_handle.resolution = requested_dpi
        except Exception:
            pass

        if request.get("source_type") == "adf":
            for attribute_name, attribute_value in (("source", "ADF"), ("feeder_mode", "All Pages")):
                try:
                    setattr(device_handle, attribute_name, attribute_value)
                except Exception:
                    pass

    def _normalize_image_mode(self, image, mode):
        if mode == "grayscale":
            return image.convert("L")
        if mode == "mono":
            return image.convert("1")
        return image.convert("RGB")

    def _save_image(self, image, destination_folder):
        scan_number = 1
        while True:
            filename = f"scan_{scan_number:06d}.tif"
            path = os.path.join(destination_folder, filename)
            if not os.path.exists(path):
                break
            scan_number += 1

        image.save(path, format="TIFF")
        return path

    def _display_name(self, device):
        device_name, vendor, model, _device_type = device
        label = " ".join(part for part in (vendor, model) if part).strip()
        if label:
            return f"{label} ({device_name})"
        return str(device_name)