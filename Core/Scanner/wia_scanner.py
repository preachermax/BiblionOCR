import win32com.client
import tempfile
import os
import uuid
from PyQt5.QtGui import QImage
print("[WIA SCANNER LOADED]")
class WIAScanner:

    def __init__(self):
        self.wia = win32com.client.Dispatch("WIA.CommonDialog")
        self.device_manager = win32com.client.Dispatch("WIA.DeviceManager")

    # -------------------------
    # Device discovery
    # -------------------------
    def list_devices(self):
        devices = []
        for i, dev in enumerate(self.device_manager.DeviceInfos):
            devices.append(dev.Properties("Name").Value)
        return devices

    # -------------------------
    # Scan acquisition
    # -------------------------

    def acquire(self, destination_folder):

        device_manager = win32com.client.Dispatch("WIA.DeviceManager")
        device = device_manager.DeviceInfos[0].Connect()

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

        # -------------------------
        # SAVE UNIQUE FILE
        # -------------------------
        # Save the WIA image temporarily
        temp_png = os.path.join(destination_folder, "__scan_temp.png")
        image.SaveFile(temp_png)

        # Load into Qt
        qimg = QImage(temp_png)

        # Convert to grayscale
        qimg = qimg.convertToFormat(QImage.Format_Grayscale8)

        # Find the next available scan number
        scan_number = 1
        while True:
            filename = f"scan_{scan_number:06d}.tif"
            path = os.path.join(destination_folder, filename)
            if not os.path.exists(path):
                break
            scan_number += 1

        # Save as TIFF
        qimg.save(path, "TIFF")

        # Remove temporary PNG
        try:
            os.remove(temp_png)
        except OSError:
            pass

        return {
            "path": path,
            "dir": destination_folder
        }
        
        
        
        # filename = f"scan_{uuid.uuid4().hex}.png"
        # path = os.path.join(destination_folder, filename)

        # image.SaveFile(path)

        # # -------------------------
        # # CREATE QIMAGE (LOCAL ONLY)
        # # -------------------------
        # qimg = QImage(path)

        # # -------------------------
        # # RETURN STRUCTURE
        # # -------------------------
        # return {
        #     "image": qimg,
        #     "path": path,
        #     "dir": os.path.dirname(path)
        # } 
    
    
#     def acquire(self):
#         device = self.device_manager.DeviceInfos[0].Connect()

#         WIA_FORMAT_PNG = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
#         WIA_INTENT_COLOR = 1

#         image = self.wia.ShowAcquireImage(
#             1,
#             WIA_INTENT_COLOR,
#             0,
#             WIA_FORMAT_PNG,
#             False,
#             True,
#             False
#         )

#         import uuid
#         import tempfile
#         import os

#         filename = f"scan_{uuid.uuid4().hex}.png"
#         path = os.path.join(tempfile.gettempdir(), filename)

#         image.SaveFile(path)

#         #return path
#         return {
#             "image": self.qimage,
#             "path": path,
#             "dir": os.path.dirname(path)
# }
#     # -------------------------
    # Convert to Qt image
    # -------------------------
    
    def acquire_qimage(self, destination_folder):
        result = self.acquire(destination_folder)
        return result["image"]