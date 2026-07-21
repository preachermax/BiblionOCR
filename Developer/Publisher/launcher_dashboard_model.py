"""
launcher_dashboard_model.py

Semantic layout model for the MyLauncher Dashboard Canvas.

Unlike ui_model.py, which represents an individual Qt Designer
interface, and application_ui_model.py, which represents the
relationships between application interfaces, this module models
the unique spatial composition of the MyLauncher dashboard.

The Dashboard Canvas consists of three conceptual layers:

    1. Content Regions
    2. Navigation Spine
    3. Reserved Navigation Space

This module intentionally contains no Qt dependencies.

-----------------------------------------------------------------

                Dashboard Canvas

    +-------------------------------------------+

        Named Content Regions

            top_left_container

            top_right_container

            left_center_container

            right_center_container

            bottom_container

    +-------------------------------------------+

            Navigation Spine

                    North

               MyLauncher
                 MyWriter

        West                 East

      MyTrainer         MyVersifier
      MyGrounder        MyResolver
      MyReader          MyLexer

                    South

              MyGlypher
              MyBoxer
              MyPixler
              MyScanner
              MyExplorer
              MyServer

    +-------------------------------------------+

        Reserved Navigation Space

The Navigation Spine occupies the negative space between
the content regions.

These spaces are intentional and must remain available
for navigation, animation and tutorial highlighting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


# ============================================================
# Enumerations
# ============================================================


class DashboardRegion(Enum):
    """
    Permanent content regions.
    """

    TOP_LEFT = auto()

    TOP_RIGHT = auto()

    LEFT_CENTER = auto()

    RIGHT_CENTER = auto()

    BOTTOM = auto()


class SpineArm(Enum):
    """
    Navigation Spine arms.
    """

    NORTH = auto()

    SOUTH = auto()

    EAST = auto()

    WEST = auto()


class RegionRole(Enum):
    """
    Intended use of each region.
    """

    HEADER = auto()

    FOOTER = auto()

    INFORMATION = auto()

    VISUALIZATION = auto()

    PRESENTATION = auto()

    GENERAL = auto()


class ContentProvider(Enum):
    """
    Types of content that may occupy
    Dashboard regions.
    """

    NONE = auto()

    CYTOSCAPE = auto()

    TUTORIAL = auto()

    DOCUMENTATION = auto()

    STATUS = auto()

    AVATAR = auto()

    VIDEO = auto()

    IMAGE = auto()

    HTML = auto()

    CUSTOM = auto()


# ============================================================
# Dashboard Regions
# ============================================================


@dataclass
class ContentRegion:
    """
    One named dashboard region.
    """

    region: DashboardRegion

    object_name: str

    role: RegionRole

    preferred_provider: ContentProvider = ContentProvider.NONE

    visible: bool = True

    description: str = ""
    
    # ============================================================
# Navigation Spine
# ============================================================


@dataclass
class NavigationNode:
    """
    Represents one module button positioned on the
    Navigation Spine.
    """

    module_name: str

    arm: SpineArm

    order: int

    button_name: str = ""

    interface_name: Optional[str] = None

    description: str = ""

    enabled: bool = True

    visible: bool = True

    highlighted: bool = False

    animated: bool = False


@dataclass
class NavigationSpine:
    """
    Semantic representation of the Dashboard
    Navigation Spine.

    The spine exists independently of Qt layouts.
    It describes logical placement rather than
    pixel coordinates.
    """

    north: List[NavigationNode] = field(default_factory=list)

    west: List[NavigationNode] = field(default_factory=list)

    east: List[NavigationNode] = field(default_factory=list)

    south: List[NavigationNode] = field(default_factory=list)

    def add_node(self, node: NavigationNode) -> None:

        if node.arm == SpineArm.NORTH:
            self.north.append(node)

        elif node.arm == SpineArm.WEST:
            self.west.append(node)

        elif node.arm == SpineArm.EAST:
            self.east.append(node)

        elif node.arm == SpineArm.SOUTH:
            self.south.append(node)

    def nodes(self) -> List[NavigationNode]:
        """
        Return every node in display order.
        """

        return (
            sorted(self.north, key=lambda n: n.order)
            + sorted(self.west, key=lambda n: n.order)
            + sorted(self.east, key=lambda n: n.order)
            + sorted(self.south, key=lambda n: n.order)
        )

    def find(self, module_name: str) -> Optional[NavigationNode]:

        for node in self.nodes():

            if node.module_name == module_name:
                return node

        return None

    def highlight(
        self,
        module_name: str,
        animated: bool = True,
    ) -> bool:

        node = self.find(module_name)

        if node is None:
            return False

        node.highlighted = True
        node.animated = animated

        return True

    def clear_highlights(self) -> None:

        for node in self.nodes():

            node.highlighted = False
            node.animated = False


# ============================================================
# Dashboard Canvas
# ============================================================


@dataclass
class DashboardCanvas:
    """
    Semantic description of the MyLauncher Dashboard.

    This class intentionally knows nothing about Qt
    widgets or layouts. It describes *what* exists
    rather than *how* it is rendered.
    """

    name: str = "MyLauncher Dashboard"

    description: str = (
        "Dashboard Canvas for the BiblionOCR launcher."
    )

    regions: Dict[DashboardRegion, ContentRegion] = field(
        default_factory=dict
    )

    spine: NavigationSpine = field(
        default_factory=NavigationSpine
    )

    metadata: Dict[str, str] = field(
        default_factory=dict
    )

    def add_region(
        self,
        region: ContentRegion,
    ) -> None:

        self.regions[region.region] = region

    def region(
        self,
        region: DashboardRegion,
    ) -> Optional[ContentRegion]:

        return self.regions.get(region)

    def add_node(
        self,
        node: NavigationNode,
    ) -> None:

        self.spine.add_node(node)

    def all_nodes(self) -> List[NavigationNode]:

        return self.spine.nodes()

    def module_names(self) -> List[str]:

        return [
            node.module_name
            for node in self.all_nodes()
        ]
        
      # ============================================================
# Default Dashboard Construction
# ============================================================


def create_default_dashboard() -> DashboardCanvas:
    """
    Construct the canonical MyLauncher Dashboard Canvas.

    This establishes the semantic layout used by the
    desktop launcher, the Render tutorial site, and the
    future Django portal.

    Returns
    -------
    DashboardCanvas
    """

    canvas = DashboardCanvas()

    # --------------------------------------------------------
    # Named Content Regions
    # --------------------------------------------------------

    canvas.add_region(
        ContentRegion(
            region=DashboardRegion.TOP_LEFT,
            object_name="top_left_container",
            role=RegionRole.INFORMATION,
            preferred_provider=ContentProvider.STATUS,
            description=(
                "Application branding, project summary, "
                "user identity and quick information."
            ),
        )
    )

    canvas.add_region(
        ContentRegion(
            region=DashboardRegion.TOP_RIGHT,
            object_name="top_right_container",
            role=RegionRole.HEADER,
            preferred_provider=ContentProvider.DOCUMENTATION,
            description=(
                "Tutorial title, current module, "
                "status banner and header information."
            ),
        )
    )

    canvas.add_region(
        ContentRegion(
            region=DashboardRegion.LEFT_CENTER,
            object_name="left_center_container",
            role=RegionRole.VISUALIZATION,
            preferred_provider=ContentProvider.CYTOSCAPE,
            description=(
                "Persistent Cytoscape visualization "
                "and workflow explorer."
            ),
        )
    )

    canvas.add_region(
        ContentRegion(
            region=DashboardRegion.RIGHT_CENTER,
            object_name="right_center_container",
            role=RegionRole.PRESENTATION,
            preferred_provider=ContentProvider.AVATAR,
            description=(
                "Animated demonstrations, avatar, "
                "interactive previews and media."
            ),
        )
    )

    canvas.add_region(
        ContentRegion(
            region=DashboardRegion.BOTTOM,
            object_name="bottom_container",
            role=RegionRole.FOOTER,
            preferred_provider=ContentProvider.STATUS,
            description=(
                "Tutorial controls, narration controls, "
                "progress indicators and footer."
            ),
        )
    )

    # --------------------------------------------------------
    # Navigation Spine
    # --------------------------------------------------------

    #
    # North Arm
    #

    canvas.add_node(
        NavigationNode(
            module_name="MyLauncher",
            button_name="btnMyLauncher",
            arm=SpineArm.NORTH,
            order=0,
        )
    )

    canvas.add_node(
        NavigationNode(
            module_name="MyWriter",
            button_name="btnMyWriter",
            arm=SpineArm.NORTH,
            order=1,
        )
    )

    #
    # West Arm
    #

    canvas.add_node(
        NavigationNode(
            module_name="MyTrainer",
            button_name="btnMyTrainer",
            arm=SpineArm.WEST,
            order=0,
        )
    )

    canvas.add_node(
        NavigationNode(
            module_name="MyGrounder",
            button_name="btnMyGrounder",
            arm=SpineArm.WEST,
            order=1,
        )
    )

    canvas.add_node(
        NavigationNode(
            module_name="MyReader",
            button_name="btnMyReader",
            arm=SpineArm.WEST,
            order=2,
        )
    )

    #
    # East Arm
    #

    canvas.add_node(
        NavigationNode(
            module_name="MyVersifier",
            button_name="btnMyVersifier",
            arm=SpineArm.EAST,
            order=0,
        )
    )

    canvas.add_node(
        NavigationNode(
            module_name="MyResolver",
            button_name="btnMyResolver",
            arm=SpineArm.EAST,
            order=1,
        )
    )

    canvas.add_node(
        NavigationNode(
            module_name="MyLexer",
            button_name="btnMyLexer",
            arm=SpineArm.EAST,
            order=2,
        )
    )

    #
    # South Arm
    #

    south_modules = [
        "MyGlypher",
        "MyBoxer",
        "MyPixler",
        "MyScanner",
        "MyExplorer",
        "MyServer",
    ]

    for order, module in enumerate(south_modules):

        canvas.add_node(
            NavigationNode(
                module_name=module,
                button_name=f"btn{module}",
                arm=SpineArm.SOUTH,
                order=order,
            )
        )

    return canvas


# ============================================================
# Dashboard Utilities
# ============================================================


def region_names(canvas: DashboardCanvas) -> List[str]:
    """
    Return all Dashboard region object names.
    """

    return sorted(
        region.object_name
        for region in canvas.regions.values()
    )


def validate_dashboard(
    canvas: DashboardCanvas,
) -> List[str]:
    """
    Validate the Dashboard Canvas.

    Returns
    -------
    List[str]
        Validation errors. An empty list indicates that
        the dashboard is structurally valid.
    """

    errors: List[str] = []

    #
    # Required content regions
    #

    required_regions = {
        DashboardRegion.TOP_LEFT,
        DashboardRegion.TOP_RIGHT,
        DashboardRegion.LEFT_CENTER,
        DashboardRegion.RIGHT_CENTER,
        DashboardRegion.BOTTOM,
    }

    missing = required_regions.difference(
        canvas.regions.keys()
    )

    if missing:

        for region in sorted(
            missing,
            key=lambda r: r.name,
        ):
            errors.append(
                f"Missing dashboard region: {region.name}"
            )

    #
    # Duplicate module names
    #

    seen = set()

    for node in canvas.all_nodes():

        if node.module_name in seen:

            errors.append(
                f"Duplicate NavigationSpine node: "
                f"{node.module_name}"
            )

        seen.add(node.module_name)

    return errors


# ============================================================
# Public API
# ============================================================

__all__ = [

    #
    # Enumerations
    #

    "DashboardRegion",
    "SpineArm",
    "RegionRole",
    "ContentProvider",

    #
    # Models
    #

    "ContentRegion",
    "NavigationNode",
    "NavigationSpine",
    "DashboardCanvas",

    #
    # Factory
    #

    "create_default_dashboard",

    #
    # Utilities
    #

    "region_names",
    "validate_dashboard",
]  