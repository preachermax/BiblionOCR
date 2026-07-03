import os
import re
import shutil
import subprocess
import sys
import time

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
    _scanimage_timeout_seconds = 20
    _scanimage_discovery_attempts = 3
    _scanimage_retry_delay_seconds = 2.0
    _availability_cache = {}
    _engine_cache = {}
    _last_scanimage_devices = []

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
        scanimage_path = cls._scanimage_path()
        if not scanimage_path:
            return False

        # Once scanimage is installed, SANE operations can run safely in a
        # subprocess even if discovery is slow or temporarily empty.
        return True

        try:
            completed = subprocess.run(
                [scanimage_path, "-L"],
                capture_output=True,
                text=True,
                timeout=cls._scanimage_timeout_seconds,
                check=False,
            )
        except Exception:
            return False

        if completed.returncode != 0:
            return False

        return bool(cls._parse_scanimage_devices(completed.stdout))

    @classmethod
    def _scanimage_path(cls):
        for candidate in (
            shutil.which("scanimage"),
            "/usr/bin/scanimage",
            "/usr/local/bin/scanimage",
        ):
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    def __init__(self):
        engine = self._select_engine()
        if engine is None:
            raise RuntimeError("SANE scanning requires a working python-sane or scanimage installation plus Pillow")
        self._engine = engine

    def _allow_network_fallback(self, request=None):
        fallback_value = True if request is None else request.get("allow_network_fallback", True)
        if isinstance(fallback_value, str):
            return fallback_value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(fallback_value)

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

    def _list_devices_via_scanimage(self, request=None):
        scanimage_path = self._scanimage_path()
        if not scanimage_path:
            return []

        last_error = None
        for attempt in range(self._scanimage_discovery_attempts):
            completed = subprocess.run(
                [scanimage_path, "-L"],
                capture_output=True,
                text=True,
                timeout=self._scanimage_timeout_seconds,
                check=False,
            )
            if completed.returncode != 0:
                last_error = (completed.stderr or completed.stdout or "scanimage -L failed").strip()
            else:
                output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
                devices = self._parse_scanimage_devices(output)
                if devices:
                    self.__class__._last_scanimage_devices = list(devices)
                    return devices
                last_error = "No devices reported by scanimage -L"

            if attempt < self._scanimage_discovery_attempts - 1:
                time.sleep(self._scanimage_retry_delay_seconds)

        if self.__class__._last_scanimage_devices:
            return list(self.__class__._last_scanimage_devices)

        if self._allow_network_fallback(request):
            fallback_devices = self._discover_devices_via_escl_fallback()
            if fallback_devices:
                self.__class__._last_scanimage_devices = list(fallback_devices)
                return fallback_devices

        if last_error:
            raise RuntimeError(last_error)
        return []

    def _discover_devices_via_escl_fallback(self):
        try:
            from .escl_scanner import ESCLScanner
        except Exception:
            return []

        if not ESCLScanner.is_available():
            return []

        try:
            devices = ESCLScanner()._discover_devices(force_refresh=True)
        except Exception:
            return []

        fallback_devices = []
        for device in devices:
            host = str(device.get("host") or "").strip()
            if not host:
                continue
            display_name = f"{device.get('display_name', host)} [AirScan fallback]"
            fallback_devices.append(
                {
                    "name": f"escl-fallback:{host}",
                    "label": f"eSCL fallback ip={host}",
                    "display_name": display_name,
                    "fallback_target": host,
                }
            )
        return fallback_devices

    @classmethod
    def _parse_scanimage_devices(cls, output):
        devices = []
        for raw_line in (output or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            name_match = re.search(r"\bdevice\s+[`'](?P<name>[^`']+)[`']", line, flags=re.IGNORECASE)
            if not name_match:
                continue

            device_name = name_match.group("name").strip()
            label_match = re.search(r"\bis\s+(?:an?\s+)?(?P<label>.+)$", line, flags=re.IGNORECASE)
            label = label_match.group("label").strip() if label_match else ""
            display_name = f"{label} ({device_name}) [native SANE]" if label else f"{device_name} [native SANE]"
            devices.append(
                {
                    "name": device_name,
                    "label": label,
                    "display_name": display_name,
                }
            )
        return devices

    def _acquire_via_scanimage(self, destination_folder, request):
        devices = self._list_devices_via_scanimage(request)
        if not devices:
            raise RuntimeError("SANE did not report any scanner devices")

        device_info = self._select_scanimage_device(devices, request.get("device_name"))
        if device_info.get("fallback_target"):
            if not self._allow_network_fallback(request):
                raise RuntimeError("SANE strict mode is enabled and scanimage did not report a native device")
            fallback_result = self._fallback_to_escl_target(
                device_info.get("fallback_target"),
                device_info,
                destination_folder,
                request,
            )
            if fallback_result is not None:
                return fallback_result
            raise RuntimeError("AirScan fallback device could not be reached")

        output_path = self._save_path(destination_folder)
        scanimage_path = self._scanimage_path()
        if not scanimage_path:
            raise RuntimeError("scanimage is not installed or not on PATH")

        command = [scanimage_path, "--format=tiff", "--device-name", device_info["name"]]
        supported_options = self._scanimage_supported_options(scanimage_path, device_info["name"])

        mode_map = {
            "color": "Color",
            "grayscale": "Gray",
            "mono": "Lineart",
        }
        requested_mode = mode_map.get(request.get("mode", "color"), "Color")
        if "--mode" in supported_options:
            command.extend(["--mode", requested_mode])

        requested_dpi = str(int(request.get("dpi", 300)))
        if "--resolution" in supported_options:
            command.extend(["--resolution", requested_dpi])

        if request.get("source_type") == "adf" and "--source" in supported_options:
            command.extend(["--source", "ADF"])

        fallback_command = [scanimage_path, "--format=tiff"]

        completed = self._run_scanimage_command(command, output_path)
        if completed.returncode != 0 and self._should_retry_scanimage_without_device_name(completed.stderr):
            completed = self._run_scanimage_command(fallback_command, output_path)

        if completed.returncode != 0:
            if self._allow_network_fallback(request):
                fallback_result = self._fallback_to_escl_if_possible(device_info, destination_folder, request)
                if fallback_result is not None:
                    return fallback_result
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

    def _run_scanimage_command(self, command, output_path):
        with open(output_path, "wb") as image_handle:
            return subprocess.run(
                command,
                stdout=image_handle,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False,
            )

    def _should_retry_scanimage_without_device_name(self, stderr_bytes):
        message = stderr_bytes.decode("utf-8", errors="replace").lower()
        return "open of device" in message and "invalid argument" in message

    def _fallback_to_escl_if_possible(self, device_info, destination_folder, request):
        label = str(device_info.get("label") or "")
        ip_match = re.search(r"\bip=(?P<host>[^\s,;]+)", label, flags=re.IGNORECASE)
        if not ip_match:
            return None

        return self._fallback_to_escl_target(ip_match.group("host").strip(), device_info, destination_folder, request)

    def _fallback_to_escl_target(self, direct_target, device_info, destination_folder, request):
        if not direct_target:
            return None

        try:
            from .escl_scanner import ESCLScanner
        except Exception:
            return None

        if not ESCLScanner.is_available():
            return None

        fallback_request = dict(request or {})
        fallback_request["device_name"] = direct_target

        try:
            result = ESCLScanner().acquire(destination_folder, request=fallback_request)
        except Exception:
            return None

        if isinstance(result, dict):
            result.setdefault("device", device_info.get("display_name") or direct_target)
        return result

    def _scanimage_supported_options(self, scanimage_path, device_name):
        try:
            completed = subprocess.run(
                [scanimage_path, "-A", "--device-name", device_name],
                capture_output=True,
                text=True,
                timeout=self._scanimage_timeout_seconds,
                check=False,
            )
        except Exception:
            return set()

        if completed.returncode != 0:
            return set()

        supported_options = set()
        for raw_line in completed.stdout.splitlines():
            line = raw_line.strip()
            if not line.startswith("--"):
                continue

            option_name = line.split()[0]
            option_name = option_name.split("=")[0].rstrip(":")
            supported_options.add(option_name)
        return supported_options

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