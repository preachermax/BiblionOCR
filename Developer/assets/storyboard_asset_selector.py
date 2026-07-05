"""Interactive selector for assigning PNG asset previews to storyboard categories.

This tool treats ``PNG previews`` as the working review surface and persists
assignments into ``asset_tags.csv``. It can also sync the categorized EPS copy
folders from the saved manifest so the preview-based review workflow stays in
step with the non-destructive source asset sort.
"""

from __future__ import annotations

import csv
import shutil
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageTk


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "Licensed images"
PREVIEW_DIR = ROOT / "PNG previews"
MANIFEST_PATH = ROOT / "asset_tags.csv"
CATEGORY_CONFIG_PATH = ROOT / "storyboard_categories.csv"

DEFAULT_CATEGORIES = [
    {
        "category_code": "A",
        "display_name": "Darkness / abstraction / emergence",
        "category_folder": "A - Darkness abstraction emergence",
        "description": (
            "Canonical A storyboard map for shadowed archive and discovery "
            "imagery: caves lanterns manuscripts emergence and first-contact "
            "visuals."
        ),
    },
    {
        "category_code": "B",
        "display_name": "Knowledge / thought / conceptual structures",
        "category_folder": "B - Knowledge thought conceptual structures",
        "description": (
            "Canonical B storyboard map for scholars books seminars and "
            "interpretive scenes centered on learning dialogue and textual "
            "understanding."
        ),
    },
    {
        "category_code": "C",
        "display_name": "Technical systems / UI / data / machines",
        "category_folder": "C - Technical systems UI data machines",
        "description": (
            "Canonical C storyboard map for interfaces dashboards holograms and "
            "technical workstations used in analytical and computational "
            "sequences."
        ),
    },
    {
        "category_code": "D",
        "display_name": "Architecture / diagrams / flow / networks",
        "category_folder": "D - Architecture diagrams flow networks",
        "description": (
            "Canonical D storyboard map for architectural civic and circulation "
            "scenes that widen story world and public context."
        ),
    },
    {
        "category_code": "E",
        "display_name": "Neutral / branding / background textures",
        "category_folder": "E - Neutral branding background textures",
        "description": (
            "Canonical E storyboard map for title plates transitions background "
            "textures and other low-semantic supporting frames."
        ),
    },
]


@dataclass
class AssetRecord:
    eps_file: str
    png_preview_file: str
    category_code: str = ""
    category_folder: str = ""
    tags: str = ""
    notes: str = ""


@dataclass(frozen=True)
class CategoryDefinition:
    code: str
    display_name: str
    folder: str
    description: str = ""


def load_category_config() -> list[CategoryDefinition]:
    categories: list[CategoryDefinition] = []

    if CATEGORY_CONFIG_PATH.exists():
        with CATEGORY_CONFIG_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                code = (row.get("category_code") or "").strip()
                display_name = (row.get("display_name") or "").strip()
                folder = (row.get("category_folder") or "").strip()
                description = (row.get("description") or "").strip()
                if code and display_name and folder:
                    categories.append(
                        CategoryDefinition(
                            code=code,
                            display_name=display_name,
                            folder=folder,
                            description=description,
                        )
                    )

    if categories:
        return categories

    return [
        CategoryDefinition(
            code=item["category_code"],
            display_name=item["display_name"],
            folder=item["category_folder"],
            description=item.get("description", ""),
        )
        for item in DEFAULT_CATEGORIES
    ]


def load_preview_records() -> list[AssetRecord]:
    records_by_png: dict[str, AssetRecord] = {}

    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                png_name = (row.get("png_preview_file") or "").strip()
                if not png_name:
                    continue
                records_by_png[png_name] = AssetRecord(
                    eps_file=(row.get("eps_file") or "").strip(),
                    png_preview_file=png_name,
                    category_code=(row.get("category_code") or "").strip(),
                    category_folder=(row.get("category_folder") or "").strip(),
                    tags=(row.get("tags") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                )

    ordered_records: list[AssetRecord] = []
    for preview_path in sorted(PREVIEW_DIR.glob("shutterstock_*.png")):
        png_name = preview_path.name
        record = records_by_png.get(png_name)
        if record is None:
            record = AssetRecord(
                eps_file=f"{preview_path.stem}.eps",
                png_preview_file=png_name,
            )
        elif not record.eps_file:
            record.eps_file = f"{preview_path.stem}.eps"
        ordered_records.append(record)

    return ordered_records


def load_category_definitions(records: list[AssetRecord]) -> list[CategoryDefinition]:
    seen_codes: set[str] = set()
    categories: list[CategoryDefinition] = []

    for category in load_category_config():
        if category.code not in seen_codes:
            categories.append(category)
            seen_codes.add(category.code)

    for record in records:
        if record.category_code and record.category_folder and record.category_code not in seen_codes:
            categories.append(
                CategoryDefinition(
                    code=record.category_code,
                    display_name=record.category_folder,
                    folder=record.category_folder,
                    description="",
                )
            )
            seen_codes.add(record.category_code)

    return categories


def write_manifest(records: list[AssetRecord]) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "eps_file",
                "png_preview_file",
                "category_code",
                "category_folder",
                "tags",
                "notes",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "eps_file": record.eps_file,
                    "png_preview_file": record.png_preview_file,
                    "category_code": record.category_code,
                    "category_folder": record.category_folder,
                    "tags": record.tags,
                    "notes": record.notes,
                }
            )


def sync_category_folders(records: list[AssetRecord], categories: list[CategoryDefinition]) -> None:
    category_lookup = {category.code: category.folder for category in categories}
    managed_filenames = {record.eps_file for record in records if record.eps_file}

    for category in categories:
        (ROOT / category.folder).mkdir(exist_ok=True)

    for category in categories:
        target_dir = ROOT / category.folder
        for eps_path in target_dir.glob("shutterstock_*.eps"):
            matching_record = next((record for record in records if record.eps_file == eps_path.name), None)
            if matching_record is None:
                continue
            expected_folder = category_lookup.get(matching_record.category_code, "")
            if matching_record.eps_file in managed_filenames and category.folder != expected_folder:
                eps_path.unlink()

    for record in records:
        if not record.category_code or not record.category_folder or not record.eps_file:
            continue

        source_path = SOURCE_DIR / record.eps_file
        if not source_path.exists():
            continue

        target_dir = ROOT / record.category_folder
        target_dir.mkdir(exist_ok=True)
        shutil.copy2(source_path, target_dir / record.eps_file)


class StoryboardSelectorApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Storyboard Asset Selector")
        self.master.geometry("1500x920")

        self.records = load_preview_records()
        self.categories = load_category_definitions(self.records)
        self.category_map = {category.code: category.folder for category in self.categories}
        self.category_details = {category.code: category for category in self.categories}

        self.current_record: AssetRecord | None = None
        self.current_photo: ImageTk.PhotoImage | None = None
        self.filtered_indices: list[int] = []

        self.filter_var = tk.StringVar(value="All")
        self.file_label_var = tk.StringVar(value="")
        self.category_var = tk.StringVar(value="")
        self.category_help_var = tk.StringVar(value="Select an A-E storyboard category to see its guidance.")
        self.tags_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")
        self.auto_advance_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._bind_shortcuts()
        self._refresh_asset_list()
        if self.filtered_indices:
            self.asset_listbox.selection_set(0)
            self._select_filtered_position(0)

    def _build_ui(self) -> None:
        container = ttk.Panedwindow(self.master, orient=tk.HORIZONTAL)
        container.pack(fill=tk.BOTH, expand=True)

        preview_panel = ttk.Frame(container, padding=10)
        control_panel = ttk.Frame(container, padding=10)
        container.add(preview_panel, weight=4)
        container.add(control_panel, weight=3)

        self.preview_label = ttk.Label(preview_panel, anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        preview_panel.bind("<Configure>", self._on_preview_resize)

        header = ttk.Frame(control_panel)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Storyboard filter").pack(anchor=tk.W)

        filter_values = ["All", "Unassigned"] + [f"{category.code} - {category.display_name}" for category in self.categories]
        filter_box = ttk.Combobox(
            header,
            textvariable=self.filter_var,
            values=filter_values,
            state="readonly",
        )
        filter_box.pack(fill=tk.X, pady=(4, 8))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_asset_list())

        list_frame = ttk.Frame(control_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.asset_listbox = tk.Listbox(list_frame, exportselection=False, height=16)
        self.asset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.asset_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.asset_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.asset_listbox.configure(yscrollcommand=scrollbar.set)

        ttk.Label(control_panel, textvariable=self.file_label_var, wraplength=420).pack(fill=tk.X, pady=(10, 8))

        category_frame = ttk.LabelFrame(control_panel, text="Storyboard category")
        category_frame.pack(fill=tk.X, pady=(0, 10))
        for index, category in enumerate(self.categories, start=1):
            label = f"{index}. {category.code}"
            button = ttk.Radiobutton(
                category_frame,
                text=f"{label}  {category.display_name}",
                value=category.code,
                variable=self.category_var,
                command=self._assign_from_radio,
            )
            button.pack(anchor=tk.W, padx=8, pady=3)

        ttk.Label(
            control_panel,
            textvariable=self.category_help_var,
            wraplength=420,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(0, 10))

        tag_frame = ttk.Frame(control_panel)
        tag_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(tag_frame, text="Tags (; separated)").pack(anchor=tk.W)
        ttk.Entry(tag_frame, textvariable=self.tags_var).pack(fill=tk.X, pady=(4, 0))

        notes_frame = ttk.Frame(control_panel)
        notes_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(notes_frame, text="Notes").pack(anchor=tk.W)
        self.notes_text = tk.Text(notes_frame, height=8, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        action_frame = ttk.Frame(control_panel)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Checkbutton(
            action_frame,
            text="Auto-advance after assignment",
            variable=self.auto_advance_var,
        ).pack(anchor=tk.W, pady=(0, 8))

        nav_frame = ttk.Frame(action_frame)
        nav_frame.pack(fill=tk.X)
        ttk.Button(nav_frame, text="Previous", command=self.previous_asset).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="Next", command=self.next_asset).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(nav_frame, text="Save manifest", command=self.save_manifest).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(nav_frame, text="Sync category folders", command=self.sync_folders).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(control_panel, textvariable=self.status_var, wraplength=420).pack(fill=tk.X, pady=(12, 0))

    def _bind_shortcuts(self) -> None:
        self.master.bind("<Left>", lambda _event: self.previous_asset())
        self.master.bind("<Right>", lambda _event: self.next_asset())
        self.master.bind("<Control-s>", lambda _event: self.save_manifest())

        for index, category in enumerate(self.categories, start=1):
            if index <= 9:
                self.master.bind(str(index), lambda _event, value=category.code: self.assign_category(value))
            self.master.bind(category.code.lower(), lambda _event, value=category.code: self.assign_category(value))
            self.master.bind(category.code.upper(), lambda _event, value=category.code: self.assign_category(value))

    def _filtered_record_indices(self) -> list[int]:
        filter_value = self.filter_var.get()
        indices: list[int] = []

        for index, record in enumerate(self.records):
            if filter_value == "All":
                indices.append(index)
            elif filter_value == "Unassigned":
                if not record.category_code:
                    indices.append(index)
            else:
                code = filter_value.split(" - ", 1)[0]
                if record.category_code == code:
                    indices.append(index)

        return indices

    def _refresh_asset_list(self) -> None:
        current_png = self.current_record.png_preview_file if self.current_record else None
        self.filtered_indices = self._filtered_record_indices()
        self.asset_listbox.delete(0, tk.END)

        for record_index in self.filtered_indices:
            record = self.records[record_index]
            display_code = record.category_code or "-"
            self.asset_listbox.insert(tk.END, f"[{display_code}] {record.png_preview_file}")

        if not self.filtered_indices:
            self.current_record = None
            self.file_label_var.set("No assets match the current filter.")
            self.preview_label.configure(image="")
            self.current_photo = None
            return

        if current_png:
            for position, record_index in enumerate(self.filtered_indices):
                if self.records[record_index].png_preview_file == current_png:
                    self.asset_listbox.selection_set(position)
                    self._select_filtered_position(position)
                    return

        self.asset_listbox.selection_set(0)
        self._select_filtered_position(0)

    def _select_filtered_position(self, position: int) -> None:
        if not self.filtered_indices:
            return

        position = max(0, min(position, len(self.filtered_indices) - 1))
        self.asset_listbox.selection_clear(0, tk.END)
        self.asset_listbox.selection_set(position)
        self.asset_listbox.see(position)

        record_index = self.filtered_indices[position]
        self._load_record(self.records[record_index], position)

    def _load_record(self, record: AssetRecord, position: int) -> None:
        self.current_record = record
        self.file_label_var.set(
            f"{position + 1} / {len(self.filtered_indices)}\n"
            f"PNG: {record.png_preview_file}\n"
            f"EPS: {record.eps_file or 'Not set'}"
        )
        self.category_var.set(record.category_code)
        self._update_category_help(record.category_code)
        self.tags_var.set(record.tags)
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", record.notes)
        self._render_preview()

    def _update_category_help(self, category_code: str) -> None:
        category = self.category_details.get(category_code)
        if category is None:
            self.category_help_var.set("Select an A-E storyboard category to see its guidance.")
            return

        guidance = category.description or "No description configured for this storyboard category."
        self.category_help_var.set(f"{category.display_name}\n{guidance}")

    def _render_preview(self) -> None:
        if self.current_record is None:
            return

        preview_path = PREVIEW_DIR / self.current_record.png_preview_file
        if not preview_path.exists():
            self.preview_label.configure(text=f"Missing preview: {preview_path.name}", image="")
            self.current_photo = None
            return

        frame_width = max(self.preview_label.winfo_width(), 600)
        frame_height = max(self.preview_label.winfo_height(), 700)
        image = Image.open(preview_path).convert("RGBA")
        image.thumbnail((frame_width - 20, frame_height - 20))
        self.current_photo = ImageTk.PhotoImage(image)
        self.preview_label.configure(image=self.current_photo, text="")

    def _on_preview_resize(self, _event: tk.Event) -> None:
        if self.current_record is not None:
            self._render_preview()

    def _on_listbox_select(self, _event: tk.Event) -> None:
        selection = self.asset_listbox.curselection()
        if not selection:
            return
        self._cache_current_fields()
        self._select_filtered_position(selection[0])

    def _cache_current_fields(self) -> None:
        if self.current_record is None:
            return

        self.current_record.category_code = self.category_var.get().strip()
        self.current_record.category_folder = self.category_map.get(self.current_record.category_code, "")
        self.current_record.tags = self.tags_var.get().strip()
        self.current_record.notes = self.notes_text.get("1.0", tk.END).strip()

    def _assign_from_radio(self) -> None:
        if self.category_var.get():
            self._update_category_help(self.category_var.get())
            self.assign_category(self.category_var.get())

    def assign_category(self, category_code: str) -> None:
        if self.current_record is None:
            return

        self._cache_current_fields()
        self.current_record.category_code = category_code
        self.current_record.category_folder = self.category_map.get(category_code, "")
        self.category_var.set(category_code)
        self._update_category_help(category_code)
        write_manifest(self.records)
        category_name = self.category_details.get(category_code).display_name if category_code in self.category_details else category_code
        self.status_var.set(f"Saved {self.current_record.png_preview_file} -> {category_name}")
        self._refresh_asset_list()

        if self.auto_advance_var.get():
            self.next_asset()

    def save_manifest(self) -> None:
        self._cache_current_fields()
        write_manifest(self.records)
        self.status_var.set("Manifest saved.")
        self._refresh_asset_list()

    def sync_folders(self) -> None:
        self._cache_current_fields()
        write_manifest(self.records)
        sync_category_folders(self.records, self.categories)
        self.status_var.set("Category folders synced from manifest.")
        messagebox.showinfo("Storyboard Asset Selector", "Category folders synced from the current manifest.")

    def _current_filtered_position(self) -> int:
        if self.current_record is None:
            return -1
        for position, record_index in enumerate(self.filtered_indices):
            if self.records[record_index] is self.current_record:
                return position
        return -1

    def previous_asset(self) -> None:
        if not self.filtered_indices:
            return
        self._cache_current_fields()
        write_manifest(self.records)
        position = self._current_filtered_position()
        if position <= 0:
            position = 0
        else:
            position -= 1
        self._select_filtered_position(position)

    def next_asset(self) -> None:
        if not self.filtered_indices:
            return
        self._cache_current_fields()
        write_manifest(self.records)
        position = self._current_filtered_position()
        if position < 0:
            position = 0
        elif position >= len(self.filtered_indices) - 1:
            position = len(self.filtered_indices) - 1
        else:
            position += 1
        self._select_filtered_position(position)


def main() -> None:
    if not PREVIEW_DIR.exists():
        raise FileNotFoundError(f"Preview folder not found: {PREVIEW_DIR}")

    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    StoryboardSelectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()