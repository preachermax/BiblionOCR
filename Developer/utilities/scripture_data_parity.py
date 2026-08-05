#!/usr/bin/env python3
"""Scripture data parity utility.

Maintains CSV->JSON mirror files for scripture normalization/reference assets and
reports required SQLite reference DB presence.

By policy, JSON files are code-updated while CSV/DB files are manually curated.
This script supports that workflow.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable, List

CSV_TO_JSON_MAP = {
    "BooksAbbrName.csv": "BooksAbbrName.json",
    "BooksAbbrNameNumIndex.csv": "BooksAbbrNameNumIndex.json",
    "BooksFolderList.csv": "BooksFolderList.json",
    "BookChapter": "BookChapter.json",
    "LineBookChapterVerse.csv": "LineBookChapterVerse.json",
    "EnglishProperNames.csv": "EnglishProperNames.json",
    "ProperNames.csv": "ProperNames.json",
    "FromvsDiacritics.csv": "FromvsDiacritics.json",
    "FROMVS3_0_PUA_Norm.csv": "FROMVS3_0_PUA_Norm.json",
    "UnicodeRanges.csv": "UnicodeRanges.json",
    "ProjectUnicodeRanges.csv": "ProjectUnicodeRanges.json",
    "rmac.csv": "RMAC.json",
}

REQUIRED_SCRIPTURE_SQLITE = (
    "FROMVS.db",
    "TRBible.db",
    "TRBibleWords.db",
    "TRiBible.db",
    "TRiBibleWords.db",
    "RMAC.db",
)


def _read_csv_rows(csv_path: Path) -> List[object]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)

        if not sample.strip():
            return []

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(handle, dialect=dialect)
        rows = [row for row in reader if any(str(cell).strip() for cell in row)]

    if not rows:
        return []

    header = [str(cell).strip() for cell in rows[0]]
    has_named_header = all(header) and len(set(header)) == len(header)

    if has_named_header:
        payload = []
        for row in rows[1:]:
            record = {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
            payload.append(record)
        return payload

    return rows


def _write_json(json_path: Path, payload: Iterable[object]) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(list(payload), handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain scripture data parity between CSV/JSON and check SQLite assets.")
    parser.add_argument("--root", default=".", help="Repository root path (default: current directory).")
    parser.add_argument("--write-json", action="store_true", help="Generate/refresh JSON mirrors from CSV sources.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSON files when writing mirrors.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    csv_dir = root / "Model" / "Project" / "Data" / "csv"
    json_dir = root / "Model" / "Project" / "Data" / "json"
    sqlite_dir = root / "Model" / "Project" / "Data" / "SQLite"

    print("[parity] root:", root)
    print("[parity] csv dir:", csv_dir)
    print("[parity] json dir:", json_dir)
    print("[parity] sqlite dir:", sqlite_dir)

    missing_csv = []
    missing_json = []

    for csv_name, json_name in CSV_TO_JSON_MAP.items():
        csv_path = csv_dir / csv_name
        json_path = json_dir / json_name

        if not csv_path.exists():
            missing_csv.append(csv_name)
            print(f"[missing-csv] {csv_name}")
            continue

        if not json_path.exists():
            missing_json.append(json_name)
            print(f"[missing-json] {json_name}")

        if args.write_json and (args.force or not json_path.exists()):
            payload = _read_csv_rows(csv_path)
            _write_json(json_path, payload)
            print(f"[wrote-json] {json_name} from {csv_name} ({len(payload)} rows)")

    for db_name in REQUIRED_SCRIPTURE_SQLITE:
        db_path = sqlite_dir / db_name
        if db_path.exists():
            print(f"[has-db] {db_name}")
        else:
            print(f"[missing-db] {db_name}")

    if missing_csv:
        print(f"[summary] missing CSV files: {len(missing_csv)}")
    if missing_json:
        print(f"[summary] missing JSON files before write: {len(missing_json)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
