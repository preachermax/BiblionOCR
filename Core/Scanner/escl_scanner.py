import io
import os
import ipaddress
import socket
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    requests = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
except ImportError:
    ServiceBrowser = None
    ServiceListener = object
    Zeroconf = None

try:
    from scapy.all import ARP, Ether, srp
except ImportError:
    ARP = None
    Ether = None
    srp = None

from .device import ScannerDevice


class _ESCLServiceListener(ServiceListener):
    def __init__(self, zeroconf_instance, backend):
        self._zeroconf = zeroconf_instance
        self._backend = backend
        self.devices = []
        self._seen = set()

    def add_service(self, zeroconf_instance, service_type, name):
        self._collect(service_type, name)

    def update_service(self, zeroconf_instance, service_type, name):
        self._collect(service_type, name)

    def remove_service(self, zeroconf_instance, service_type, name):
        return None

    def _collect(self, service_type, name):
        info = self._zeroconf.get_service_info(service_type, name, timeout=1500)
        if info is None:
            return
        device = self._backend.device_from_service_info(service_type, name, info)
        if not device:
            return

        identity = (device["display_name"], device["base_url"])
        if identity in self._seen:
            return

        self._seen.add(identity)
        self.devices.append(device)


class ESCLScanner(ScannerDevice):
    backend_name = "eSCL / AirScan"
    service_types = ("_uscan._tcp.local.", "_uscans._tcp.local.")
    discovery_timeout_seconds = 1.5
    request_timeout_seconds = 20

    def __init__(self):
        self._cached_devices = None

    @classmethod
    def is_available(cls):
        return Zeroconf is not None and requests is not None and Image is not None

    def list_devices(self):
        return [device["display_name"] for device in self._discover_devices()]

    def acquire(self, destination_folder, request=None):
        if not self.is_available():
            raise RuntimeError(
                "AirScan requires zeroconf, requests, and Pillow to be installed"
            )

        request = request or {}
        devices = self._discover_devices(force_refresh=True)
        direct_device = self._device_from_direct_target(request.get("device_name"))
        if direct_device:
            devices = self._merge_direct_device(devices, direct_device)
        if not devices:
            raise RuntimeError(
                "No AirScan devices were discovered on the network, and no direct AirScan host responded"
            )

        device = self._select_device(devices, request.get("device_name"))
        capabilities = self._fetch_capabilities(device)
        scan_settings = self._build_scan_settings(request, capabilities)
        content, content_type = self._submit_scan_job(device, scan_settings)
        path = self._save_scan_bytes(content, content_type, destination_folder, request)
        return {
            "path": path,
            "dir": destination_folder,
            "device": device["display_name"],
        }

    @classmethod
    def device_from_service_info(cls, service_type, name, info):
        addresses = []
        parsed_addresses = getattr(info, "parsed_addresses", None)
        if callable(parsed_addresses):
            addresses = parsed_addresses()
        if not addresses and getattr(info, "addresses", None):
            addresses = [socket.inet_ntoa(raw) for raw in info.addresses if len(raw) == 4]

        host = addresses[0] if addresses else getattr(info, "server", "").rstrip(".")
        if not host:
            return None

        properties = {}
        for key, value in getattr(info, "properties", {}).items():
            decoded_key = key.decode("utf-8", errors="ignore") if isinstance(key, bytes) else str(key)
            decoded_value = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)
            properties[decoded_key] = decoded_value

        resource_path = properties.get("rs") or properties.get("resource") or properties.get("path") or "/eSCL"
        resource_path = "/" + resource_path.lstrip("/")
        scheme = "https" if service_type.startswith("_uscans") else "http"
        base_url = f"{scheme}://{host}:{info.port}{resource_path.rstrip('/')}/"
        display_name = properties.get("ty") or properties.get("note") or name.split("._", 1)[0]

        return {
            "display_name": display_name,
            "host": host,
            "port": info.port,
            "base_url": base_url,
            "properties": properties,
        }

    def _discover_devices(self, force_refresh=False):
        if self._cached_devices is not None and not force_refresh:
            return list(self._cached_devices)

        devices = self._discover_devices_via_mdns()
        if not devices:
            devices = self._discover_devices_via_arp()

        self._cached_devices = devices
        return list(self._cached_devices)

    def _discover_devices_via_mdns(self):
        if Zeroconf is None or ServiceBrowser is None:
            return []

        zeroconf_instance = Zeroconf()
        listener = _ESCLServiceListener(zeroconf_instance, self)
        browsers = [ServiceBrowser(zeroconf_instance, service_type, listener) for service_type in self.service_types]
        try:
            time.sleep(self.discovery_timeout_seconds)
        finally:
            for browser in browsers:
                cancel = getattr(browser, "cancel", None)
                if callable(cancel):
                    cancel()
            zeroconf_instance.close()

        return listener.devices

    def _discover_devices_via_arp(self):
        if ARP is None or Ether is None or srp is None:
            return []

        subnet = self._get_local_subnet()
        if not subnet:
            return []

        try:
            packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
            answered, _ = srp(packet, timeout=2, retry=1, verbose=False)
        except Exception:
            return []

        devices = []
        seen_base_urls = set()
        for _, received in answered:
            device = self._device_from_direct_target(received.psrc)
            if not device:
                continue
            if device["base_url"] in seen_base_urls:
                continue
            seen_base_urls.add(device["base_url"])
            devices.append(device)
        return devices

    def _get_local_subnet(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            network = ipaddress.ip_network(local_ip + "/24", strict=False)
            return str(network)
        except Exception:
            return None

    def _select_device(self, devices, device_name):
        if not device_name:
            return devices[0]

        lowered = str(device_name).strip().lower()
        for device in devices:
            if device["display_name"].strip().lower() == lowered:
                return device
        for device in devices:
            if lowered in device["display_name"].strip().lower():
                return device

        raise RuntimeError(f"AirScan device not found: {device_name}")

    def _merge_direct_device(self, devices, direct_device):
        merged_devices = list(devices)
        direct_identity = (direct_device["display_name"], direct_device["base_url"])
        for device in merged_devices:
            identity = (device["display_name"], device["base_url"])
            if identity == direct_identity:
                return merged_devices
        merged_devices.insert(0, direct_device)
        return merged_devices

    def _device_from_direct_target(self, target):
        if not target:
            return None

        normalized_target = str(target).strip()
        if not normalized_target:
            return None

        candidate_base_urls = []
        parsed_target = urlparse(normalized_target)
        if parsed_target.scheme and parsed_target.netloc:
            candidate_base_urls.append(self._normalize_base_url(normalized_target))
        else:
            host = normalized_target
            if "/" in host:
                host = host.split("/", 1)[0]
            candidate_base_urls.append(f"http://{host}/eSCL/")
            candidate_base_urls.append(f"https://{host}/eSCL/")

        for base_url in candidate_base_urls:
            if self._direct_capabilities_available(base_url):
                parsed_base = urlparse(base_url)
                display_name = normalized_target
                return {
                    "display_name": display_name,
                    "host": parsed_base.hostname or normalized_target,
                    "port": parsed_base.port or (443 if parsed_base.scheme == "https" else 80),
                    "base_url": base_url,
                    "properties": {"source": "direct"},
                }

        return None

    def _normalize_base_url(self, value):
        trimmed_value = str(value).strip().rstrip("/")
        if trimmed_value.lower().endswith("/scannercapabilities"):
            trimmed_value = trimmed_value[: -len("/ScannerCapabilities")]
        if not trimmed_value.lower().endswith("/escl"):
            trimmed_value = trimmed_value + "/eSCL"
        return trimmed_value.rstrip("/") + "/"

    def _direct_capabilities_available(self, base_url):
        try:
            response = requests.get(
                urljoin(base_url, "ScannerCapabilities"),
                timeout=min(self.request_timeout_seconds, 5),
                verify=False,
            )
            if response.status_code != 200:
                return False
            ET.fromstring(response.content)
            return True
        except Exception:
            return False

    def _fetch_capabilities(self, device):
        response = requests.get(
            urljoin(device["base_url"], "ScannerCapabilities"),
            timeout=self.request_timeout_seconds,
            verify=False,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        return {
            "document_formats": self._find_texts(root, "DocumentFormat"),
            "color_modes": self._find_texts(root, "ColorMode"),
            "supports_adf": self._has_local_name(root, "AdfSimplexInputCaps") or self._has_local_name(root, "AdfDuplexInputCaps"),
            "supports_duplex": self._has_local_name(root, "AdfDuplexInputCaps"),
        }

    def _build_scan_settings(self, request, capabilities):
        dpi = int(request.get("dpi", 300))
        source_type = request.get("source_type", "flatbed")
        use_adf = source_type == "adf" and capabilities.get("supports_adf")
        color_mode = self._choose_color_mode(request.get("mode", "color"), capabilities.get("color_modes") or [])
        document_format = self._choose_document_format(capabilities.get("document_formats") or [])
        duplex_requested = bool(request.get("duplex")) and capabilities.get("supports_duplex") and use_adf

        settings_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<scan:ScanSettings xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm" xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03">',
            '  <pwg:Version>2.0</pwg:Version>',
            '  <scan:Intent>Document</scan:Intent>',
            f'  <pwg:InputSource>{"Feeder" if use_adf else "Platen"}</pwg:InputSource>',
            f'  <scan:ColorMode>{color_mode}</scan:ColorMode>',
            f'  <scan:XResolution>{dpi}</scan:XResolution>',
            f'  <scan:YResolution>{dpi}</scan:YResolution>',
            f'  <scan:DocumentFormat>{document_format}</scan:DocumentFormat>',
        ]
        if duplex_requested:
            settings_lines.append('  <scan:Duplex>true</scan:Duplex>')
        settings_lines.append('</scan:ScanSettings>')
        return "\n".join(settings_lines)

    def _submit_scan_job(self, device, scan_settings):
        response = requests.post(
            urljoin(device["base_url"], "ScanJobs"),
            data=scan_settings.encode("utf-8"),
            headers={"Content-Type": "text/xml"},
            timeout=self.request_timeout_seconds,
            verify=False,
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("image/") and response.content:
            return response.content, content_type

        location = response.headers.get("Location")
        if not location:
            raise RuntimeError("AirScan device did not return a scan job location")

        job_url = urljoin(response.url, location)
        document_urls = [
            job_url.rstrip("/") + "/NextDocument",
            job_url.rstrip("/") + "/Documents/1",
            job_url,
        ]

        deadline = time.time() + self.request_timeout_seconds
        while time.time() < deadline:
            for document_url in document_urls:
                document_response = requests.get(
                    document_url,
                    timeout=self.request_timeout_seconds,
                    verify=False,
                )
                if document_response.status_code == 200 and document_response.content:
                    doc_content_type = document_response.headers.get("Content-Type", "")
                    if doc_content_type.startswith("image/") or doc_content_type == "application/octet-stream":
                        return document_response.content, doc_content_type
                elif document_response.status_code not in {404, 425, 503}:
                    document_response.raise_for_status()
            time.sleep(1.0)

        raise RuntimeError("AirScan scan job did not yield a downloadable document")

    def _save_scan_bytes(self, content, content_type, destination_folder, request):
        try:
            image = Image.open(io.BytesIO(content))
        except Exception as exc:
            raise RuntimeError(f"AirScan returned an unreadable image payload: {exc}") from exc

        requested_mode = request.get("mode", "color")
        if requested_mode == "grayscale":
            image = image.convert("L")
        elif requested_mode == "mono":
            image = image.convert("1")
        else:
            image = image.convert("RGB")

        scan_number = 1
        while True:
            filename = f"scan_{scan_number:06d}.tif"
            path = os.path.join(destination_folder, filename)
            if not os.path.exists(path):
                break
            scan_number += 1

        image.save(path, format="TIFF")
        return path

    def _choose_document_format(self, formats):
        preferred_formats = ("image/tiff", "image/png", "image/jpeg")
        normalized_formats = [str(fmt).strip() for fmt in formats if fmt]
        lowered_to_original = {fmt.lower(): fmt for fmt in normalized_formats}
        for candidate in preferred_formats:
            if candidate in lowered_to_original:
                return lowered_to_original[candidate]
        return normalized_formats[0] if normalized_formats else "image/jpeg"

    def _choose_color_mode(self, requested_mode, supported_modes):
        normalized_modes = [str(mode).strip() for mode in supported_modes if mode]
        lowered_to_original = {mode.lower(): mode for mode in normalized_modes}
        preferred_by_request = {
            "color": ("rgb24", "rgb8", "color"),
            "grayscale": ("grayscale8", "grayscale16", "grayscale"),
            "mono": ("blackandwhite1", "blackandwhite", "lineart"),
        }
        for candidate in preferred_by_request.get(requested_mode, preferred_by_request["color"]):
            if candidate in lowered_to_original:
                return lowered_to_original[candidate]

        fallback_candidates = preferred_by_request["color"] + preferred_by_request["grayscale"] + preferred_by_request["mono"]
        for candidate in fallback_candidates:
            if candidate in lowered_to_original:
                return lowered_to_original[candidate]

        return normalized_modes[0] if normalized_modes else "RGB24"

    def _find_texts(self, root, local_name):
        values = []
        for element in root.iter():
            if self._local_name(element.tag) == local_name and element.text:
                values.append(element.text.strip())
        return values

    def _has_local_name(self, root, local_name):
        for element in root.iter():
            if self._local_name(element.tag) == local_name:
                return True
        return False

    @staticmethod
    def _local_name(tag_name):
        return tag_name.rsplit("}", 1)[-1] if "}" in tag_name else tag_name