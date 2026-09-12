"""Curated, executable acceptance fixtures for Biblion Scheduler."""

from __future__ import annotations

from datetime import date

from .biblionocr import BiblionOCRAdapter, BiblionOCRProjectReference
from .models import Constraint, ConstraintType, Dependency, DependencyType, ProjectSnapshot, Task, WBSElement


def biblionocr_development_plan() -> ProjectSnapshot:
    """Return a representative planning model, not BiblionOCR execution logic.

    Estimates are illustrative and intentionally live here as schedule inputs so
    the fixture remains a useful acceptance network as the engine evolves.
    """
    project = ProjectSnapshot(
        id="biblionocr-development",
        name="BiblionOCR Development and Release",
        project_start=date(2026, 9, 14),
        wbs_elements=(
            WBSElement("development", "1", "BiblionOCR Development"),
            WBSElement("architecture", "1.1", "Architecture", "development"),
            WBSElement("core", "1.2", "Core Platform", "development"),
            WBSElement("workflows", "1.3", "Module Workflows", "development"),
            WBSElement("scanner", "1.3.1", "MyScanner Standalone", "workflows"),
            WBSElement("release", "1.4", "Verification and Release", "development"),
        ),
        tasks=(
            Task("architecture", "Compute engine architecture", 5, "architecture"),
            Task("architecture-frozen", "Compute engine architecture frozen", 0, "architecture"),
            Task("core-infrastructure", "Core infrastructure", 10, "core"),
            Task("ocr-workflow", "OCR workflow design", 6, "workflows"),
            Task("module-standardization", "Module standardization", 8, "workflows"),
            Task("scanner-licensing", "Scanner licensing review", 5, "scanner"),
            Task("repository-separation", "Scanner repository separation", 5, "scanner"),
            Task("qt-migration", "Qt/PySide6 migration", 12, "scanner"),
            Task("scanner-acquisition", "Scanner acquisition", 15, "scanner"),
            Task("platform-backends", "Scanner platform backends", 10, "scanner"),
            Task("airsan-escl", "AirScan/eSCL support", 8, "scanner"),
            Task("integration-testing", "Integration and acceptance testing", 10, "release"),
            Task("documentation", "User and maintainer documentation", 7, "release"),
            Task("packaging", "Packaging", 5, "release"),
            Task("release-candidate", "MyScanner release candidate", 0, "release"),
        ),
        dependencies=(
            Dependency("architecture", "architecture-frozen"),
            Dependency("architecture-frozen", "core-infrastructure"),
            Dependency("architecture-frozen", "ocr-workflow"),
            Dependency("core-infrastructure", "module-standardization"),
            Dependency("ocr-workflow", "module-standardization", DependencyType.FINISH_TO_START, lag_days=-2),
            Dependency("architecture-frozen", "scanner-licensing"),
            Dependency("scanner-licensing", "repository-separation"),
            Dependency("repository-separation", "qt-migration"),
            Dependency("scanner-acquisition", "platform-backends"),
            Dependency("qt-migration", "platform-backends"),
            Dependency("platform-backends", "airsan-escl"),
            Dependency("module-standardization", "integration-testing"),
            Dependency("airsan-escl", "integration-testing"),
            Dependency("integration-testing", "documentation", DependencyType.START_TO_START, lag_days=2),
            Dependency("integration-testing", "packaging"),
            Dependency("documentation", "release-candidate"),
            Dependency("packaging", "release-candidate"),
        ),
        constraints=(
            Constraint("scanner-acquisition", ConstraintType.START_NO_EARLIER_THAN, date(2026, 9, 28)),
        ),
    )
    return BiblionOCRAdapter.attach_reference(
        project,
        BiblionOCRProjectReference("biblionocr-development", "fixture-r1"),
    )
