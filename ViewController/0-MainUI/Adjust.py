# -------------------------
# Adjust.py
# Image processing functions (PURE LOGIC ONLY)
# -------------------------

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg


# -------------------------
# CROP
# -------------------------
def crop_processor(qimage: qtg.QImage, params: dict) -> qtg.QImage:
    """
    params:
        x, y, w, h
    """
    if qimage is None or qimage.isNull():
        return qtg.QImage()

    x = int(params.get("x", 0))
    y = int(params.get("y", 0))
    w = int(params.get("w", qimage.width()))
    h = int(params.get("h", qimage.height()))

    rect = qtc.QRect(x, y, w, h)
    rect = rect.intersected(qimage.rect())  # safety clamp

    return qimage.copy(rect)


# -------------------------
# ROTATE (example future tool)
# -------------------------
def rotate_processor(qimage: qtg.QImage, params: dict) -> qtg.QImage:
    angle = float(params.get("angle", 0))

    if qimage is None or qimage.isNull():
        return qtg.QImage()

    transform = qtg.QTransform().rotate(angle)
    return qimage.transformed(transform, mode=qtc.Qt.SmoothTransformation)


# -------------------------
# THRESHOLD (placeholder for later)
# -------------------------
def threshold_processor(qimage: qtg.QImage, params: dict) -> qtg.QImage:
    """
    Placeholder — returns original for now
    """
    return qimage


# -------------------------
# PROCESSOR REGISTRY (VERY IMPORTANT)
# -------------------------
PROCESSORS = {
    "crop": crop_processor,
    "rotate": rotate_processor,
    "threshold": threshold_processor,
}


def get_processor(name: str):
    return PROCESSORS.get(name)