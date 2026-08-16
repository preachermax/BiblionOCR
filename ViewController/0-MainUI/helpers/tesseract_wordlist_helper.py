import os
import re
import unicodedata
from collections import Counter
from typing import Optional

from PyQt5 import QtWidgets


def _normalize_word(word: str) -> str:
    return unicodedata.normalize("NFC", str(word or "").strip()).lower()


def extract_wordlist_words(text: str) -> set[str]:
    return {
        _normalize_word(token)
        for token in re.findall(r"[^\W_]+(?:['’][^\W_]+)*", text or "", flags=re.UNICODE)
        if _normalize_word(token)
    }


def _read_existing_words(path: Optional[str]) -> set:
    if not path or not os.path.exists(path):
        return set()

    with open(path, "r", encoding="utf-8") as handle:
        return {
            _normalize_word(line)
            for line in handle
            if _normalize_word(line)
        }


def _get_full_text(text_source) -> str:
    if callable(text_source):
        value = text_source()
    else:
        value = text_source

    if hasattr(value, "toPlainText"):
        return value.toPlainText()
    if value is None:
        return ""
    return str(value)


def _get_selected_text(text_source) -> str:
    if callable(text_source):
        value = text_source()
    else:
        value = text_source

    if hasattr(value, "textCursor"):
        try:
            return value.textCursor().selectedText()
        except Exception:
            pass
    return _get_full_text(value)


def show_word_count_dialog(parent, text_source) -> QtWidgets.QDialog:
    dialog = QtWidgets.QDialog(parent)
    layout = QtWidgets.QGridLayout(dialog)

    current_label = QtWidgets.QLabel("Current selection", dialog)
    current_label.setStyleSheet("font-weight:bold; font-size: 15px;")
    current_words_label = QtWidgets.QLabel("Words: ", dialog)
    current_symbols_label = QtWidgets.QLabel("Symbols: ", dialog)
    current_words = QtWidgets.QLabel(dialog)
    current_symbols = QtWidgets.QLabel(dialog)

    total_label = QtWidgets.QLabel("Total", dialog)
    total_label.setStyleSheet("font-weight:bold; font-size: 15px;")
    total_words_label = QtWidgets.QLabel("Words: ", dialog)
    total_symbols_label = QtWidgets.QLabel("Symbols: ", dialog)
    total_words = QtWidgets.QLabel(dialog)
    total_symbols = QtWidgets.QLabel(dialog)

    layout.addWidget(current_label, 0, 0)
    layout.addWidget(current_words_label, 1, 0)
    layout.addWidget(current_words, 1, 1)
    layout.addWidget(current_symbols_label, 2, 0)
    layout.addWidget(current_symbols, 2, 1)
    layout.addWidget(total_label, 4, 0)
    layout.addWidget(total_words_label, 5, 0)
    layout.addWidget(total_words, 5, 1)
    layout.addWidget(total_symbols_label, 6, 0)
    layout.addWidget(total_symbols, 6, 1)

    dialog.setWindowTitle("Word count")
    dialog.setGeometry(300, 300, 200, 200)
    dialog.setLayout(layout)

    selected_text = _get_selected_text(text_source)
    full_text = _get_full_text(text_source)
    current_words.setText(str(len(selected_text.split())))
    current_symbols.setText(str(len(selected_text)))
    total_words.setText(str(len(full_text.split())))
    total_symbols.setText(str(len(full_text)))

    dialog.show()
    return dialog


def update_tesseract_wordlist_for_variant(
    base_word: str,
    variant_word: str,
    project_root: Optional[str] = None,
    output_path: Optional[str] = None,
    include_existing: bool = True,
) -> str:
    words_to_add = [word for word in (base_word, variant_word) if word]
    if not words_to_add:
        return output_path or os.path.join(project_root or os.getcwd(), "tesseract_wordlist.txt")

    combined_text = " ".join(words_to_add)
    return update_tesseract_wordlist_from_text(
        combined_text,
        project_root=project_root,
        output_path=output_path,
        include_existing=include_existing,
    )


def update_tesseract_wordlist_from_text(
    text: str,
    project_root: Optional[str] = None,
    output_path: Optional[str] = None,
    include_existing: bool = True,
) -> str:
    if not output_path:
        if project_root:
            output_path = os.path.join(project_root, "tesseract_wordlist.txt")
        else:
            output_path = os.path.join(os.getcwd(), "tesseract_wordlist.txt")

    existing_words = _read_existing_words(output_path) if include_existing else set()
    discovered_words = Counter(extract_wordlist_words(text))

    combined = sorted(existing_words | set(discovered_words.keys()))
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as handle:
        for word in combined:
            handle.write(f"{word}\n")

    return output_path
