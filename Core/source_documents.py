from __future__ import annotations

import os
import shutil
import stat

from Core.project_database import load_project_database_record, project_metadata_database_path


PDF_SOURCE_RELATIVE_DIR = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "source_images",
    "pdf_acq_src_image",
)
LEGACY_PDF_SOURCE_RELATIVE_DIRS = (
    os.path.join("Model", "Project", "Images", "MyServer", "Source", "pdf"),
)


def project_pdf_source_path(project_root: str, filename: str) -> str:
    return os.path.join(os.path.abspath(project_root), PDF_SOURCE_RELATIVE_DIR, os.path.basename(filename))


def find_project_pdf_source(project_root: str) -> str:
    absolute_project_root = os.path.abspath(project_root)
    metadata = load_project_database_record(project_metadata_database_path(absolute_project_root))
    registered_path = str(metadata.get("SourceDocumentPath", "") or "").strip()
    if registered_path and not os.path.isabs(registered_path):
        registered_path = os.path.join(absolute_project_root, registered_path)
    if registered_path and registered_path.lower().endswith(".pdf") and os.path.isfile(registered_path):
        return os.path.abspath(registered_path)

    source_directories = (
        os.path.join(absolute_project_root, PDF_SOURCE_RELATIVE_DIR),
        *(
            os.path.join(absolute_project_root, relative_dir)
            for relative_dir in LEGACY_PDF_SOURCE_RELATIVE_DIRS
        ),
    )
    for source_dir in source_directories:
        if not os.path.isdir(source_dir):
            continue
        pdf_files = sorted(
            os.path.join(source_dir, filename)
            for filename in os.listdir(source_dir)
            if filename.lower().endswith(".pdf") and os.path.isfile(os.path.join(source_dir, filename))
        )
        if pdf_files:
            return pdf_files[0]
    return ""


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