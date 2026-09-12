"""Explicit, read-only BiblionOCR reference integration boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .models import ProjectSnapshot


@dataclass(frozen=True)
class BiblionOCRProjectReference:
    """Stable identity metadata received from BiblionOCR.

    This deliberately contains no executable workflow state. Mapping workflows
    or BiblionOCR events into scheduling tasks requires a separate, approved
    command so that execution relationships never become schedule logic by
    accident.
    """

    project_id: str
    revision: str

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.revision.strip():
            raise ValueError("BiblionOCR project id and revision are required.")

    @property
    def external_reference(self) -> str:
        return f"biblionocr:{self.project_id}@{self.revision}"


class BiblionOCRAdapter:
    """Attach a source reference without reading or writing BiblionOCR data."""

    @staticmethod
    def attach_reference(project: ProjectSnapshot, source: BiblionOCRProjectReference) -> ProjectSnapshot:
        return replace(project, external_reference=source.external_reference)
