"""Read-only catalog of authoritative BiblionOCR workflow exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .models import WorkflowScope


@dataclass(frozen=True)
class WorkflowStep:
    """One source row retained as planning evidence, not a scheduled task."""

    scope: WorkflowScope
    source_row: int
    sequence: str
    description: str
    milestone_name: str
    method: str
    module: str = ""
    section: str = ""
    source_module: str = ""
    destination_module: str = ""

    @property
    def identity(self) -> tuple[str, ...]:
        if self.scope is WorkflowScope.PAGE:
            return (self.section, self.sequence, self.milestone_name, self.method)
        return (self.sequence, self.milestone_name, self.method)

    def references_module(self, module: str) -> bool:
        return module.casefold() in {
            self.module.casefold(),
            self.source_module.casefold(),
            self.destination_module.casefold(),
        }


@dataclass(frozen=True)
class WorkflowCatalog:
    source_path: Path
    scope: WorkflowScope
    steps: tuple[WorkflowStep, ...]

    @classmethod
    def from_csv(cls, path: str | Path, scope: WorkflowScope) -> "WorkflowCatalog":
        source_path = Path(path)
        with source_path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            required = {"Sequence", "MilestoneName", "Method"}
            if scope is WorkflowScope.PAGE:
                required.add("PageSections")
            missing = required.difference(reader.fieldnames or ())
            if missing:
                raise ValueError(f"Workflow CSV is missing columns: {', '.join(sorted(missing))}.")

            steps = tuple(
                cls._step_from_row(scope, source_row, row)
                for source_row, row in enumerate(reader, start=2)
                if cls._has_identity(scope, row)
            )
        return cls(source_path, scope, steps)

    @classmethod
    def from_ods(cls, path: str | Path, scope: WorkflowScope) -> "WorkflowCatalog":
        """Read a named workflow sheet directly from the governing ODS workbook."""
        try:
            from odf import teletype
            from odf.namespaces import TABLENS
            from odf.opendocument import load
            from odf.table import Table, TableRow
        except ImportError as error:
            raise RuntimeError("Reading ProjectWorkflow.ods requires odfpy.") from error

        source_path = Path(path)
        document = load(str(source_path))
        sheet_name = f"{scope.value}_workflow"
        sheet = next(
            (
                table for table in document.spreadsheet.getElementsByType(Table)
                if table.getAttribute("name") == sheet_name
            ),
            None,
        )
        if sheet is None:
            raise ValueError(f"Workflow workbook is missing sheet: {sheet_name}.")

        source_rows: list[tuple[int, list[str]]] = []
        source_row = 1
        for row in sheet.getElementsByType(TableRow):
            values: list[str] = []
            for cell in row.childNodes:
                if getattr(cell, "qname", None) not in {
                    (TABLENS, "table-cell"),
                    (TABLENS, "covered-table-cell"),
                }:
                    continue
                repeated_columns = int(cell.getAttribute("numbercolumnsrepeated") or 1)
                values.extend([teletype.extractText(cell).strip()] * repeated_columns)
            repeated_rows = int(row.getAttribute("numberrowsrepeated") or 1)
            for _ in range(repeated_rows):
                source_rows.append((source_row, values))
                source_row += 1

        if not source_rows:
            raise ValueError(f"Workflow workbook sheet is empty: {sheet_name}.")
        headers = source_rows[0][1]
        required = {"Sequence", "MilestoneName", "Method"}
        if scope is WorkflowScope.PAGE:
            required.add("PageSections")
        missing = required.difference(headers)
        if missing:
            raise ValueError(f"Workflow ODS is missing columns: {', '.join(sorted(missing))}.")
        steps = tuple(
            cls._step_from_row(scope, row_number, dict(zip(headers, values)))
            for row_number, values in source_rows[1:]
            if cls._has_identity(scope, dict(zip(headers, values)))
        )
        return cls(source_path, scope, steps)

    @staticmethod
    def _has_identity(scope: WorkflowScope, row: dict[str, str | None]) -> bool:
        fields = ["Sequence", "MilestoneName", "Method"]
        if scope is WorkflowScope.PAGE:
            fields.append("PageSections")
        return any((row.get(field) or "").strip() for field in fields)

    @staticmethod
    def _step_from_row(
        scope: WorkflowScope,
        source_row: int,
        row: dict[str, str | None],
    ) -> WorkflowStep:
        def value(field: str) -> str:
            return (row.get(field) or "").strip()

        return WorkflowStep(
            scope=scope,
            source_row=source_row,
            sequence=value("Sequence"),
            description=value("Description"),
            milestone_name=value("MilestoneName"),
            method=value("Method"),
            module=value("Module"),
            section=value("PageSections"),
            source_module=value("SourceModule"),
            destination_module=value("DestinationModule"),
        )

    def steps_for_module(self, module: str) -> tuple[WorkflowStep, ...]:
        return tuple(step for step in self.steps if step.references_module(module))

    def duplicate_identities(self) -> dict[tuple[str, ...], tuple[WorkflowStep, ...]]:
        grouped: dict[tuple[str, ...], list[WorkflowStep]] = {}
        for step in self.steps:
            grouped.setdefault(step.identity, []).append(step)
        return {
            identity: tuple(matches)
            for identity, matches in grouped.items()
            if len(matches) > 1
        }
