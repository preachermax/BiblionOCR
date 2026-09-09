from __future__ import annotations

import json
import os
from typing import Any


BOOK_LOOKUP_RELATIVE_PATH = os.path.join(
    "Model", "Project", "Data", "json", "BooksMarkDown.json"
)


def normalize_book_folder(value: Any) -> str:
    text = str(value or "").strip()
    for prefix in ("source_", "greek_", "latin_"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
            break
    return text.lstrip("_").replace(" ", "_")


def load_book_references(root: str) -> list[dict[str, Any]]:
    lookup_path = os.path.join(os.path.abspath(root), BOOK_LOOKUP_RELATIVE_PATH)
    if not os.path.isfile(lookup_path):
        return []
    try:
        with open(lookup_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError, TypeError):
        return []
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def find_book_reference(root: str, value: Any) -> dict[str, Any] | None:
    normalized = normalize_book_folder(value).lower()
    abbreviation = str(value or "").strip().lower()
    for item in load_book_references(root):
        if str(item.get("BookAbbr", "")).strip().lower() == abbreviation:
            return item
        if normalize_book_folder(item.get("BookMarkdown")).lower() == normalized:
            return item
    return None


def book_session_values(reference: dict[str, Any]) -> dict[str, Any]:
    abbreviation = str(reference.get("BookAbbr", "")).strip()
    markdown = str(reference.get("BookMarkdown", "")).strip()
    folder = normalize_book_folder(markdown)
    return {
        "self.bookabbr": abbreviation,
        "self.bookmarkdown": markdown,
        "self.current_book_folder": folder,
        "self.current_book_number": reference.get("BookNumber"),
        "self.sourcebookmarkdown": f"source{markdown}",
        "self.greekbookmarkdown": f"greek{markdown}",
        "self.latinbookmarkdown": f"latin{markdown}",
    }