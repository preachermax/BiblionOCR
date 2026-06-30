import win32com.client
import tempfile
import os

def scan_once():
    wia = win32com.client.Dispatch("WIA.CommonDialog")

    device_manager = win32com.client.Dispatch("WIA.DeviceManager")
    device = device_manager.DeviceInfos[0].Connect()

    print("Selected device:", device.Properties("Name").Value)

    # WIA constants (important)
    WIA_FORMAT_PNG = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
    WIA_INTENT_COLOR = 1

    # POSitional call (THIS is the key fix)
    image = wia.ShowAcquireImage(
        1,          # DeviceType: 1 = scanner
        WIA_INTENT_COLOR,
        0,          # Bias
        WIA_FORMAT_PNG,
        False,      # AlwaysSelectDevice
        True,       # UseCommonUI
        False       # CancelError
    )

    path = os.path.join(tempfile.gettempdir(), "scan.png")
    image.SaveFile(path)

    print("Saved:", path)


if __name__ == "__main__":
    scan_once()