try:
    import pythoncom
    import win32com.client
except ImportError:
    pythoncom = None
    win32com = None

import os
from PyQt5.QtGui import QImage
from .device import ScannerDevice


class WIAScanner(ScannerDevice):
    backend_name = "WIA"

    @classmethod
    def is_supported_platform(cls, platform_name):
        return platform_name == "windows"

    @classmethod
    def is_available(cls):
        return win32com is not None and pythoncom is not None

    def __init__(self):
        if win32com is None or pythoncom is None:
            raise RuntimeError(
                "WIA scanning requires pywin32 and is only supported on Windows"
            )

    # -------------------------
    # Device discovery
    # -------------------------
    def list_devices(self):
        pythoncom.CoInitialize()
        try:
            device_manager = win32com.client.Dispatch("WIA.DeviceManager")
            devices = []
            for dev in device_manager.DeviceInfos:
                devices.append(dev.Properties("Name").Value)
            return devices
        finally:
            pythoncom.CoUninitialize()

    # -------------------------
    # Scan acquisition
    # -------------------------

    def acquire(self, destination_folder, request=None):
        pythoncom.CoInitialize()
        try:
            device_manager = win32com.client.Dispatch("WIA.DeviceManager")
            devices = list(device_manager.DeviceInfos)
            if not devices:
                raise RuntimeError("WIA did not report any scanner devices")

            wia = win32com.client.Dispatch("WIA.CommonDialog")
            WIA_FORMAT_PNG = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
            WIA_INTENT_COLOR = 1

            image = wia.ShowAcquireImage(
                1,
                WIA_INTENT_COLOR,
                0,
                WIA_FORMAT_PNG,
                False,
                True,
                False
            )

            if image is None:
                raise RuntimeError("WIA scan did not return an image")

            temp_png = os.path.join(destination_folder, "__scan_temp.png")
            image.SaveFile(temp_png)

            qimg = QImage(temp_png)
            if qimg.isNull():
                raise RuntimeError("WIA returned an unreadable temporary image")

            qimg = qimg.convertToFormat(QImage.Format_Grayscale8)

            scan_number = 1
            while True:
                filename = f"scan_{scan_number:06d}.tif"
                path = os.path.join(destination_folder, filename)
                if not os.path.exists(path):
                    break
                scan_number += 1

            if not qimg.save(path, "TIFF"):
                raise RuntimeError(f"Failed to save scanned TIFF to {path}")

            try:
                os.remove(temp_png)
            except OSError:
                pass

            return {
                "path": path,
                "dir": destination_folder
            }
        finally:
            pythoncom.CoUninitialize()

    # Convert to Qt image
    # -------------------------
    def acquire_qimage(self, destination_folder):
        return super().acquire_qimage(destination_folder)