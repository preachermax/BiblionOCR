"""Relationship view over ApplicationUIModel launch metadata.

This module intentionally avoids duplicating launcher/module metadata and
derives launch nodes and edges from the canonical ApplicationUIModel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from .application_ui_model import (
        ApplicationUIModel,
        NavigationRelationship,
    )
except ImportError:
    from application_ui_model import (  # type: ignore
        ApplicationUIModel,
        NavigationRelationship,
    )


@dataclass(frozen=True)
class LaunchNode:
    """Derived launch-target node for graph rendering."""

    interface_id: str
    display_name: str
    ui_filename: str
    description: str
    launch_mode: str


class LaunchGraph:
    """Launch relationship graph derived from ApplicationUIModel."""

    def __init__(
        self,
        application_model: ApplicationUIModel,
        launcher_interface_id: str = "MyLauncher",
        module_scripts: Optional[Dict[str, str]] = None,
    ) -> None:
        self.application_model = application_model
        self.launcher_interface_id = launcher_interface_id
        self.module_scripts = dict(module_scripts or {})

    def get_nodes(self) -> List[LaunchNode]:
        """Return launch-target nodes derived from interface metadata."""

        nodes: List[LaunchNode] = []

        for interface_id in self.application_model.launches(self.launcher_interface_id):
            interface = self.application_model.get_interface(interface_id)
            if interface is None:
                nodes.append(
                    LaunchNode(
                        interface_id=interface_id,
                        display_name=interface_id,
                        ui_filename="",
                        description="",
                        launch_mode="UNKNOWN",
                    )
                )
                continue

            nodes.append(
                LaunchNode(
                    interface_id=interface.interface_id,
                    display_name=interface.display_name,
                    ui_filename=interface.ui_filename,
                    description=interface.description,
                    launch_mode=interface.launch_mode.name,
                )
            )

        return nodes

    def get_edges(self) -> List[Dict[str, str]]:
        """Return launch edges derived from navigation links."""

        edges: List[Dict[str, str]] = []

        for link in self.application_model.outgoing_navigation(self.launcher_interface_id):
            if link.relationship != NavigationRelationship.LAUNCHES:
                continue

            edge = {
                "source": link.source,
                "target": link.destination,
                "description": link.description,
            }

            script_name = self.module_scripts.get(link.destination)
            if script_name:
                edge["script"] = script_name

            edges.append(edge)

        return edges