import os
import re
import shutil
import subprocess
import sys

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
    _availability_cache = {}
    _engine_cache = {}

    @classmethod
    def is_supported_platform(cls, platform_name):
        return platform_name in {"linux", "darwin"}

    @classmethod
    def is_available(cls):
        return cls._select_engine() is not None

    @classmethod
    def _select_engine(cls):
        if Image is None:
            return None

        cache_key = sys.executable
        if cache_key in cls._engine_cache:
            return cls._engine_cache[cache_key]

        engine = None
        if cls._python_sane_available():
            engine = "python"
        elif cls._scanimage_available():
            engine = "scanimage"

        cls._engine_cache[cache_key] = engine
        cls._availability_cache[cache_key] = engine is not None
        return engine

    @classmethod
    def _python_sane_available(cls):
        if sane is None:
            return False

        probe_script = (
            "import sys\n"
            "try:\n"
            "    import sane\n"
            "    sane.init()\n"
            "    devices = sane.get_devices()\n"
            "    sane.exit()\n"
            "    sys.exit(0 if devices else 3)\n"
            "except Exception:\n"
            "    sys.exit(2)\n"
        )

        try:
            completed = subprocess.run(
                [sys.executable, "-c", probe_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
            return completed.returncode == 0
        except Exception:
            return False

    @classmethod
    def _scanimage_available(cls):
        scanimage_path = shutil.which("scanimage")
        if not scanimage_path:
            return False

        try:
            completed = subprocess.run(
                [scanimage_path, "-L"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception:
            return False

        if completed.returncode != 0:
            return False

        return bool(cls._parse_scanimage_devices(completed.stdout))

    def __init__(self):
        engine = self._select_engine()
        if engine is None:
            raise RuntimeError("SANE scanning requires a working python-sane or scanimage installation plus Pillow")
        self._engine = engine

    def list_devices(self):
        if self._engine == "python":
            sane.init()
            try:
                devices = sane.get_devices()
                return [self._display_name(device) for device in devices]
            finally:
                sane.exit()

        devices = self._list_devices_via_scanimage()
        return [device["display_name"] for device in devices]

    def acquire(self, destination_folder, request=None):
        request = request or {}
        if self._engine == "scanimage":
            return self._acquire_via_scanimage(destination_folder, request)

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

    def _list_devices_via_scanimage(self):
        scanimage_path = shutil.which("scanimage")
        if not scanimage_path:
            return []

        completed = subprocess.run(
            [scanimage_path, "-L"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "scanimage -L failed").strip())

        return self._parse_scanimage_devices(completed.stdout)

    @classmethod
    def _parse_scanimage_devices(cls, output):
        devices = []
        for raw_line in (output or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            match = re.match(r"^device\s+[`'](?P<name>[^`']+)[`']\s+is\s+a\s+(?P<label>.+)$", line)
            if match:
                device_name = match.group("name").strip()
                label = match.group("label").strip()
                devices.append(
                    {
                        "name": device_name,
                        "label": label,
                        "display_name": f"{label} ({device_name})",
                    }
                )
        return devices

    def _acquire_via_scanimage(self, destination_folder, request):
        devices = self._list_devices_via_scanimage()
        if not devices:
            raise RuntimeError("SANE did not report any scanner devices")

        device_info = self._select_scanimage_device(devices, request.get("device_name"))
        output_path = self._save_path(destination_folder)
        scanimage_path = shutil.which("scanimage")
        if not scanimage_path:
            raise RuntimeError("scanimage is not installed or not on PATH")

        command = [scanimage_path, "--format=tiff", "--device-name", device_info["name"]]
        command.extend(["--resolution", str(int(request.get("dpi", 300)))])

        mode_map = {
            "color": "Color",
            "grayscale": "Gray",
            "mono": "Lineart",
        }
        command.extend(["--mode", mode_map.get(request.get("mode", "color"), "Color")])

        if request.get("source_type") == "adf":
            command.extend(["--source", "ADF"])

        with open(output_path, "wb") as image_handle:
            completed = subprocess.run(
                command,
                stdout=image_handle,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False,
            )

        if completed.returncode != 0:
            try:
                os.remove(output_path)
            except OSError:
                pass
            message = completed.stderr.decode("utf-8", errors="replace").strip() or "scanimage acquisition failed"
            raise RuntimeError(message)

        return {
            "path": output_path,
            "dir": destination_folder,
            "device": device_info["display_name"],
        }

    def _select_scanimage_device(self, devices, requested_name):
        if not requested_name:
            return devices[0]

        normalized_requested = str(requested_name).strip().lower()
        for device in devices:
            candidates = {device["name"].strip().lower(), device["display_name"].strip().lower()}
            if normalized_requested in candidates:
                return device
        for device in devices:
            if normalized_requested in device["name"].strip().lower():
                return device
            if normalized_requested in device["display_name"].strip().lower():
                return device

        raise RuntimeError(f"SANE device not found: {requested_name}")

    def _save_path(self, destination_folder):
        scan_number = 1
        while True:
            filename = f"scan_{scan_number:06d}.tif"
            path = os.path.join(destination_folder, filename)
            if not os.path.exists(path):
                return path
            scan_number += 1