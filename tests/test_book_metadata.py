from pathlib import Path

from Core.book_metadata import (
    book_session_values,
    find_book_reference,
    normalize_book_folder,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_book_reference_resolves_abbreviation_markdown_and_folder_names() -> None:
    expected = ("Luk", "_book_42_Luke")

    for value in ("Luk", "_book_42_Luke", "book_42_Luke", "book 42 Luke"):
        reference = find_book_reference(str(ROOT_DIR), value)
        assert reference is not None
        assert (reference["BookAbbr"], reference["BookMarkdown"]) == expected


def test_book_session_values_preserve_canonical_markdown() -> None:
    reference = find_book_reference(str(ROOT_DIR), "Mat")
    assert reference is not None

    values = book_session_values(reference)

    assert normalize_book_folder(values["self.bookmarkdown"]) == "book_40_Matthew"
    assert values["self.bookabbr"] == "Mat"
    assert values["self.sourcebookmarkdown"] == "source_book_40_Matthew"
    assert values["self.greekbookmarkdown"] == "greek_book_40_Matthew"
    assert values["self.latinbookmarkdown"] == "latin_book_40_Matthew"