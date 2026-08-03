import os
import sys
from types import SimpleNamespace


def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    module_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(module_dir, "..", ".."))

    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    import MyServer
    from ImagePreviewDialog import ImagePreviewDialog
    from PyQt5 import QtCore, QtGui, QtWidgets

    sample_image = os.environ.get(
        "BIBLION_SMOKE_IMAGE",
        os.path.join(
            repo_root,
            "ViewController",
            "1-PreProcess",
            "ImageEditor",
            "Image-Editor-main",
            "ppl.jpg",
        ),
    )

    if not os.path.isfile(sample_image):
        raise FileNotFoundError(sample_image)

    captured = {}
    original_popen = MyServer.subprocess.Popen

    def fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = list(cmd)

        class DummyProc:
            pid = 12345

        return DummyProc()

    MyServer.subprocess.Popen = fake_popen

    class DummyServer:
        def __init__(self, imgpath):
            self.imgpath = imgpath

        def run_child_module(self, *args):
            return MyServer.MainWindow.run_child_module(self, *args)

        def _start_pixler_return_monitor(self):
            return None

    try:
        dummy = DummyServer(sample_image)
        MyServer.MainWindow.OpenWithMyPixler(dummy)
    finally:
        MyServer.subprocess.Popen = original_popen

    assert captured.get("cmd"), "No launch command captured"
    assert captured["cmd"][1].endswith("MyPixler.py"), captured["cmd"]
    assert os.path.normpath(captured["cmd"][2]) == os.path.normpath(sample_image), captured["cmd"]

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    qimage = QtGui.QImage(sample_image)
    assert not qimage.isNull(), "Failed to load sample image into QImage"

    class CropProbe:
        def __call__(self, qimage, params):
            x = params.get("x", 0)
            y = params.get("y", 0)
            w = params.get("w", qimage.width())
            h = params.get("h", qimage.height())
            return qimage.copy(x, y, w, h)

    dialog = ImagePreviewDialog(qimage, CropProbe(), None)
    dialog.zoom_slider.setValue(100)
    QtWidgets.QApplication.processEvents()

    assert dialog._set_crop_from_display_rect(QtCore.QRect(10, 10, 50, 60)), "Crop rect was not accepted"
    result = dialog.get_result()
    assert result is not None and not result.isNull(), "Crop result is null"
    assert result.width() == 50 and result.height() == 60, (result.width(), result.height())

    print("TEST_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())