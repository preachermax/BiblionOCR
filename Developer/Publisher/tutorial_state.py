from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TutorialState:
    """
    Current tutorial execution state.

    This class owns no metadata.
    It simply tracks where the tutorial currently is.
    """

    module_name: str = ""
    order: int = 0
    running: bool = False

    def reset(self) -> None:
        self.module_name = ""
        self.order = 0
        self.running = False