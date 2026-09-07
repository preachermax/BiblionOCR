from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile

from PIL import Image
from pypdf import PdfReader, PdfWriter

from Core.project_database import load_project_database_record, project_metadata_database_path


PDF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "source_images",
    "pdf_acq_src_image",
)
TIFF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "source_images",
    "tif_acq_src_image",
)
SCANNED_TIFF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyScanner",
    "scanned_images",
    "tif_scan_src_image",
)
SCANNED_PDF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyScanner",
    "scanned_images",
    "pdf_scan_src_image",
)
COMBINED_PDF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "source_images",
    "pdf_combined_src_images",
)
PROVENANCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "source_images",
    "provenance",
)
SUPPORTED_SOURCE_EXTENSIONS = {".pdf", ".tif", ".tiff"}
LEGACY_PDF_SOURCE_RELATIVE_DIRS = (
    os.path.join("Model", "Project", "Images", "MyServer", "Source", "pdf"),
)


def project_pdf_source_path(project_root: str, filename: str) -> str:
    return project_source_document_path(project_root, filename)


def project_source_document_path(project_root: str, filename: str) -> str:
    extension = os.path.splitext(str(filename))[1].lower()
    if extension not in SUPPORTED_SOURCE_EXTENSIONS:
        raise ValueError("Source document must be a PDF or TIFF file")
    relative_dir = PDF_SOURCE_RELATIVE_DIR if extension == ".pdf" else TIFF_SOURCE_RELATIVE_DIR
    return os.path.join(os.path.abspath(project_root), relative_dir, os.path.basename(filename))


def find_project_pdf_source(project_root: str) -> str:
    return find_project_source_document(project_root)


def find_project_source_document(project_root: str) -> str:
    absolute_project_root = os.path.abspath(project_root)
    metadata = load_project_database_record(project_metadata_database_path(absolute_project_root))
    registered_path = str(metadata.get("SourceDocumentPath", "") or "").strip()
    if registered_path and not os.path.isabs(registered_path):
        registered_path = os.path.join(absolute_project_root, registered_path)
    if (
        registered_path
        and os.path.splitext(registered_path)[1].lower() in SUPPORTED_SOURCE_EXTENSIONS
        and os.path.isfile(registered_path)
    ):
        return os.path.abspath(registered_path)

    source_directories = (
        os.path.join(absolute_project_root, PDF_SOURCE_RELATIVE_DIR),
        os.path.join(absolute_project_root, TIFF_SOURCE_RELATIVE_DIR),
        *(
            os.path.join(absolute_project_root, relative_dir)
            for relative_dir in LEGACY_PDF_SOURCE_RELATIVE_DIRS
        ),
    )
    for source_dir in source_directories:
        if not os.path.isdir(source_dir):
            continue
        source_files = sorted(
            os.path.join(source_dir, filename)
            for filename in os.listdir(source_dir)
            if os.path.splitext(filename)[1].lower() in SUPPORTED_SOURCE_EXTENSIONS
            and os.path.isfile(os.path.join(source_dir, filename))
        )
        if source_files:
            return source_files[0]
    return ""


def copy_pdf_source_readonly(source_path: str, project_root: str) -> str:
    return copy_source_document_readonly(source_path, project_root)


def copy_source_document_readonly(source_path: str, project_root: str) -> str:
    normalized_source = os.path.abspath(str(source_path or "").strip())
    if not os.path.isfile(normalized_source):
        raise ValueError("Selected source image document does not exist")
    if os.path.splitext(normalized_source)[1].lower() not in SUPPORTED_SOURCE_EXTENSIONS:
        raise ValueError("Selected source image document must be a PDF or TIFF file")

    destination_path = project_source_document_path(project_root, os.path.basename(normalized_source))
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    if os.path.normcase(normalized_source) != os.path.normcase(os.path.abspath(destination_path)):
        if os.path.exists(destination_path):
            os.chmod(destination_path, os.stat(destination_path).st_mode | stat.S_IWUSR)
        shutil.copy2(normalized_source, destination_path)
    os.chmod(destination_path, os.stat(destination_path).st_mode & ~(
        stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    ))
    return destination_path


def copy_provenance_file(source_path: str, project_root: str) -> str:
    normalized_source = os.path.abspath(str(source_path or "").strip())
    if not os.path.isfile(normalized_source):
        raise ValueError("Selected provenance file does not exist")

    destination_path = os.path.join(
        os.path.abspath(project_root),
        PROVENANCE_RELATIVE_DIR,
        os.path.basename(normalized_source),
    )
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    if os.path.normcase(normalized_source) != os.path.normcase(os.path.abspath(destination_path)):
        shutil.copy2(normalized_source, destination_path)
    return destination_path


def project_scan_image_directory(project_root: str) -> str:
    return os.path.join(os.path.abspath(project_root), SCANNED_TIFF_SOURCE_RELATIVE_DIR)


def convert_scan_to_project_pdf(scan_path: str, project_root: str) -> str:
    normalized_scan_path = os.path.abspath(str(scan_path or "").strip())
    if not os.path.isfile(normalized_scan_path):
        raise ValueError("Scanned image does not exist")

    destination_dir = os.path.join(
        os.path.abspath(project_root),
        SCANNED_PDF_SOURCE_RELATIVE_DIR,
    )
    os.makedirs(destination_dir, exist_ok=True)
    destination_path = os.path.join(
        destination_dir,
        f"{os.path.splitext(os.path.basename(normalized_scan_path))[0]}.pdf",
    )

    pages = []
    with Image.open(normalized_scan_path) as source_image:
        frame_count = int(getattr(source_image, "n_frames", 1) or 1)
        for frame_index in range(frame_count):
            source_image.seek(frame_index)
            pages.append(source_image.convert("RGB").copy())

    if not pages:
        raise ValueError("Scanned image contains no pages")
    try:
        pages[0].save(
            destination_path,
            format="PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=300.0,
        )
    finally:
        for page in pages:
            page.close()
    return destination_path


def combine_project_source_pdfs(project_root: str, filename: str = "combined_source.pdf") -> str:
    normalized_project_root = os.path.abspath(project_root)
    source_directories = (
        os.path.join(normalized_project_root, PDF_SOURCE_RELATIVE_DIR),
        os.path.join(normalized_project_root, SCANNED_PDF_SOURCE_RELATIVE_DIR),
    )
    source_paths = []
    for source_directory in source_directories:
        if not os.path.isdir(source_directory):
            continue
        source_paths.extend(
            os.path.join(source_directory, entry)
            for entry in sorted(os.listdir(source_directory))
            if entry.lower().endswith(".pdf")
            and os.path.isfile(os.path.join(source_directory, entry))
        )
    if not source_paths:
        raise ValueError("No acquired or scanned PDF source pages are available to combine")

    destination_dir = os.path.join(normalized_project_root, COMBINED_PDF_SOURCE_RELATIVE_DIR)
    os.makedirs(destination_dir, exist_ok=True)
    destination_path = os.path.join(destination_dir, os.path.basename(filename))
    writer = PdfWriter()
    for source_path in source_paths:
        reader = PdfReader(source_path)
        for page in reader.pages:
            writer.add_page(page)
    with open(destination_path, "wb") as destination_file:
        writer.write(destination_file)
    return destination_path


def extract_pdf_page_range(
    source_path: str,
    destination_dir: str,
    first_page: int,
    last_page: int,
) -> str:
    normalized_source_path = os.path.abspath(str(source_path or "").strip())
    if not os.path.isfile(normalized_source_path):
        raise ValueError("Source PDF does not exist")
    if os.path.splitext(normalized_source_path)[1].lower() != ".pdf":
        raise ValueError("Source document must be a PDF file")

    try:
        first_page_number = int(first_page)
        last_page_number = int(last_page)
    except (TypeError, ValueError) as exc:
        raise ValueError("First and last page must be whole numbers") from exc

    reader = PdfReader(normalized_source_path)
    page_count = len(reader.pages)
    if first_page_number < 1 or last_page_number < first_page_number:
        raise ValueError("Page range must be ordered and use page numbers starting at 1")
    if last_page_number > page_count:
        raise ValueError(f"Last page {last_page_number} exceeds the PDF page count of {page_count}")

    normalized_destination_dir = os.path.abspath(str(destination_dir or "").strip())
    if not normalized_destination_dir:
        raise ValueError("A destination folder is required")
    os.makedirs(normalized_destination_dir, exist_ok=True)
    source_name = os.path.splitext(os.path.basename(normalized_source_path))[0]
    destination_path = os.path.join(
        normalized_destination_dir,
        f"{source_name}_Page_{first_page_number}-{last_page_number}.pdf",
    )

    writer = PdfWriter()
    for page_index in range(first_page_number - 1, last_page_number):
        writer.add_page(reader.pages[page_index])
    with open(destination_path, "wb") as destination_file:
        writer.write(destination_file)
    return destination_path


def extract_pdf_pages(
    source_path: str,
    destination_dir: str,
    first_page: int = 1,
    last_page: int | None = None,
) -> list[str]:
    normalized_source_path = os.path.abspath(str(source_path or "").strip())
    if not os.path.isfile(normalized_source_path):
        raise ValueError("Source PDF does not exist")
    reader = PdfReader(normalized_source_path)
    page_count = len(reader.pages)
    final_page = page_count if last_page is None else int(last_page)
    first_page_number = int(first_page)
    if first_page_number < 1 or final_page < first_page_number or final_page > page_count:
        raise ValueError(f"Page range must be between 1 and {page_count}")

    normalized_destination_dir = os.path.abspath(str(destination_dir or "").strip())
    os.makedirs(normalized_destination_dir, exist_ok=True)
    source_name = os.path.splitext(os.path.basename(normalized_source_path))[0]
    output_paths = []
    for page_number in range(first_page_number, final_page + 1):
        destination_path = os.path.join(
            normalized_destination_dir,
            f"{source_name}_Page_{page_number:03d}.pdf",
        )
        writer = PdfWriter()
        writer.add_page(reader.pages[page_number - 1])
        with open(destination_path, "wb") as destination_file:
            writer.write(destination_file)
        output_paths.append(destination_path)
    return output_paths


def convert_pdf_pages_to_tiff(
    source_dir: str,
    destination_dir: str,
    start_page_number: int = 1,
) -> list[str]:
    normalized_source_dir = os.path.abspath(str(source_dir or "").strip())
    if not os.path.isdir(normalized_source_dir):
        raise ValueError("PDF page source folder does not exist")
    source_paths = sorted(
        os.path.join(normalized_source_dir, filename)
        for filename in os.listdir(normalized_source_dir)
        if filename.lower().endswith(".pdf")
        and os.path.isfile(os.path.join(normalized_source_dir, filename))
    )
    if not source_paths:
        raise ValueError("PDF page source folder contains no PDF files")

    normalized_destination_dir = os.path.abspath(str(destination_dir or "").strip())
    os.makedirs(normalized_destination_dir, exist_ok=True)
    renderer_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            "ViewController",
            "0-MainUI",
            "helpers",
            "qt_pdf_renderer.py",
        )
    )
    output_paths = []
    page_number = int(start_page_number)
    for source_path in source_paths:
        output_path = os.path.join(
            normalized_destination_dir,
            f"{os.path.splitext(os.path.basename(source_path))[0]}_{page_number:03d}.tif",
        )
        temporary_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temporary_path = temporary_file.name
        temporary_file.close()
        try:
            subprocess.run(
                [sys.executable, renderer_path, "render", source_path, "0", "2400", temporary_path],
                check=True,
                capture_output=True,
                text=True,
            )
            with Image.open(temporary_path) as rendered_page:
                rendered_page.convert("RGB").save(output_path, format="TIFF", compression="tiff_lzw")
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            raise RuntimeError(f"Could not convert {os.path.basename(source_path)} to TIFF: {detail.strip()}") from exc
        finally:
            try:
                os.remove(temporary_path)
            except OSError:
                pass
        output_paths.append(output_path)
        page_number += 1
    return output_paths