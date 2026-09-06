from __future__ import annotations

import os
import shutil
import stat


PDF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "source_images",
    "pdf_acq_src_image",
)


def project_pdf_source_path(project_root: str, filename: str) -> str:
    return os.path.join(os.path.abspath(project_root), PDF_SOURCE_RELATIVE_DIR, os.path.basename(filename))


def find_project_pdf_source(project_root: str) -> str:
    source_dir = os.path.join(os.path.abspath(project_root), PDF_SOURCE_RELATIVE_DIR)
    if not os.path.isdir(source_dir):
        return ""

    pdf_files = sorted(
        os.path.join(source_dir, filename)
        for filename in os.listdir(source_dir)
        if filename.lower().endswith(".pdf") and os.path.isfile(os.path.join(source_dir, filename))
    )
    return pdf_files[0] if pdf_files else ""


def copy_pdf_source_readonly(source_path: str, project_root: str) -> str:
    normalized_source = os.path.abspath(str(source_path or "").strip())
    if not os.path.isfile(normalized_source):
        raise ValueError("Selected source image document does not exist")
    if os.path.splitext(normalized_source)[1].lower() != ".pdf":
        raise ValueError("Selected source image document must be a PDF file")

    destination_path = project_pdf_source_path(project_root, os.path.basename(normalized_source))
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    if os.path.normcase(normalized_source) != os.path.normcase(os.path.abspath(destination_path)):
        if os.path.exists(destination_path):
            os.chmod(destination_path, os.stat(destination_path).st_mode | stat.S_IWUSR)
        shutil.copy2(normalized_source, destination_path)
    os.chmod(destination_path, os.stat(destination_path).st_mode & ~(
        stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    ))
    return destination_path