from __future__ import annotations

import argparse
import json
import os
import sys

from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg
from PyQt6 import QtPdf


def ensure_application() -> qtg.QGuiApplication:
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return qtg.QGuiApplication.instance() or qtg.QGuiApplication([])


def load_pdf(pdf_path: str) -> QtPdf.QPdfDocument:
    ensure_application()
    document = QtPdf.QPdfDocument(None)
    error = document.load(os.path.abspath(pdf_path))
    if error != QtPdf.QPdfDocument.Error.None_:
        raise ValueError(f"QtPdf could not load the document (error {error.name}).")
    return document


def pdf_metadata(pdf_path: str) -> dict[str, object]:
    document = load_pdf(pdf_path)
    pages = []
    for page_index in range(document.pageCount()):
        page_size = document.pagePointSize(page_index)
        pages.append({"width": page_size.width(), "height": page_size.height()})
    return {"page_count": document.pageCount(), "pages": pages}


def render_pdf_page(pdf_path: str, page_index: int, width: int, output_path: str) -> None:
    document = load_pdf(pdf_path)
    if page_index < 0 or page_index >= document.pageCount():
        raise IndexError(f"PDF page index {page_index} is out of range.")

    page_size = document.pagePointSize(page_index)
    render_width = max(1, int(width))
    render_height = max(1, round(render_width * page_size.height() / page_size.width()))
    image = document.render(page_index, qtc.QSize(render_width, render_height))
    if image.isNull() or not image.save(output_path, "PNG"):
        raise OSError(f"QtPdf could not render page {page_index + 1}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render PDF pages with QtPdf.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata_parser = subparsers.add_parser("metadata")
    metadata_parser.add_argument("pdf_path")

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("pdf_path")
    render_parser.add_argument("page_index", type=int)
    render_parser.add_argument("width", type=int)
    render_parser.add_argument("output_path")

    args = parser.parse_args()
    try:
        if args.command == "metadata":
            print(json.dumps(pdf_metadata(args.pdf_path)))
        else:
            render_pdf_page(args.pdf_path, args.page_index, args.width, args.output_path)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())