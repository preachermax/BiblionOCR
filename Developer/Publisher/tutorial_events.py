from __future__ import annotations

from enum import Enum, auto


class TutorialEvent(Enum):
    START = auto()
    STOP = auto()
    NEXT = auto()
    PREVIOUS = auto()
    MODULE_CHANGED = auto()