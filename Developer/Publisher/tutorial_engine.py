"""Compatibility shim for migrated tutorial naming.

Prefer importing TutorialGenerator from tutorial_generator.py.
"""

from __future__ import annotations

from .tutorial_generator import TutorialGenerator, TutorialEngine

__all__ = ["TutorialGenerator", "TutorialEngine"]