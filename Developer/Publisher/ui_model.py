"""
ui_model.py

Core UI abstraction model for BiblionOCR.

This module defines a framework-independent representation of user interfaces.

The model is intentionally separated from Qt so that it can support:

    - Qt Designer .ui parsing
    - Tutorial generation
    - Cytoscape visualization
    - Documentation generation
    - Web portal representations
    - Runtime UI inspection

Architecture:

    Qt .ui files
          |
          v
      ui_parser.py
          |
          v
       UIModel
          |
          +----------------+
          |                |
          v                v
    Qt Runtime       Documentation
                         |
                         v
                  Tutorial/Cytoscape

Part 1:
    - Imports
    - Enumerations
    - Primitive dataclasses
    - Widget metadata structures

"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)


# ============================================================
# Type Aliases
# ============================================================

WidgetID = str
ModuleID = str
PropertyName = str


# ============================================================
# Enumerations
# ============================================================


class UIElementType(Enum):
    """
    Generic UI element categories.

    These are deliberately broader than Qt widgets.
    """

    APPLICATION = auto()
    WINDOW = auto()
    PANEL = auto()
    CONTAINER = auto()

    BUTTON = auto()
    LABEL = auto()
    IMAGE = auto()
    SLIDER = auto()
    INPUT = auto()
    CHECKBOX = auto()
    RADIO = auto()

    MENU = auto()
    TOOLBAR = auto()

    DIALOG = auto()

    TABLE = auto()
    TREE = auto()
    LIST = auto()

    CUSTOM = auto()



class ModuleState(Enum):
    """
    Runtime state of a BiblionOCR module.
    """

    UNKNOWN = auto()
    CREATED = auto()
    INITIALIZED = auto()
    READY = auto()
    RUNNING = auto()
    BUSY = auto()
    ERROR = auto()
    STOPPED = auto()



class VisibilityState(Enum):
    """
    Visibility state independent of GUI framework.
    """

    UNKNOWN = auto()
    VISIBLE = auto()
    HIDDEN = auto()
    COLLAPSED = auto()



class ConnectionType(Enum):
    """
    Represents logical UI connections.

    These map naturally to Qt signals/slots,
    but also work for web events or documentation graphs.
    """

    CLICK = auto()
    CHANGE = auto()
    UPDATE = auto()
    TRIGGER = auto()
    ENABLE = auto()
    DISABLE = auto()
    CUSTOM = auto()



# ============================================================
# Primitive Geometry Models
# ============================================================


@dataclass
class Position:
    """
    Two-dimensional UI position.
    """

    x: int = 0
    y: int = 0


@dataclass
class Size:
    """
    UI dimensions.
    """

    width: int = 0
    height: int = 0



# ============================================================
# Property Models
# ============================================================


@dataclass
class PropertyModel:
    """
    Generic widget property.

    Example:

        name="text"
        value="Open Project"

    or

        name="minimum"
        value=0
    """

    name: PropertyName

    value: Any

    description: str = ""



# ============================================================
# Signal / Slot Models
# ============================================================


@dataclass
class SignalModel:
    """
    Represents an emitted UI event.

    Example:

        QPushButton.clicked

    becomes:

        SignalModel(
            name="clicked",
            event_type=ConnectionType.CLICK
        )
    """

    name: str

    event_type: ConnectionType = ConnectionType.CUSTOM

    description: str = ""



@dataclass
class SlotModel:
    """
    Represents a callable destination.

    Example:

        MyServer.load_image()

    """

    name: str

    target: str = ""

    description: str = ""



@dataclass
class ConnectionModel:
    """
    Represents a logical connection between UI elements.
    """

    source_id: WidgetID

    signal: SignalModel

    destination_id: WidgetID

    slot: SlotModel

    connection_type: ConnectionType = ConnectionType.CUSTOM



# ============================================================
# Widget Metadata
# ============================================================


@dataclass
class WidgetMetadata:
    """
    Metadata describing a UI component.

    This is intentionally descriptive rather than
    tied to a particular implementation.
    """

    widget_id: WidgetID

    name: str

    element_type: UIElementType

    description: str = ""

    tooltip: str = ""

    module: Optional[ModuleID] = None

    position: Position = field(
        default_factory=Position
    )

    size: Size = field(
        default_factory=Size
    )

    visibility: VisibilityState = (
        VisibilityState.UNKNOWN
    )

    properties: Dict[str, Any] = field(
        default_factory=dict
    )

    tags: List[str] = field(
        default_factory=list
    )



# ============================================================
# Serialization Helpers
# ============================================================


def enum_to_value(value: Any) -> Any:
    """
    Convert enums recursively for serialization.
    """

    if isinstance(value, Enum):
        return value.name

    if isinstance(value, dict):
        return {
            key: enum_to_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            enum_to_value(item)
            for item in value
        ]

    return value



def dataclass_to_dict(instance: Any) -> Dict[str, Any]:
    """
    Convert a dataclass object into a JSON-safe dictionary.
    """

    return enum_to_value(
        asdict(instance)
    )
# ============================================================
# Widget Model Hierarchy
# ============================================================


@dataclass
class WidgetModel:
    """
    Base representation of any UI component.

    All widgets share:

        - identity
        - hierarchy
        - metadata
        - child relationships
        - signals
        - slots

    This becomes the universal representation used by:

        - ui_parser.py
        - tutorial_generator.py
        - cytoscape_generator.py
    """

    metadata: WidgetMetadata

    parent_id: Optional[WidgetID] = None

    children: List["WidgetModel"] = field(
        default_factory=list
    )

    signals: List[SignalModel] = field(
        default_factory=list
    )

    slots: List[SlotModel] = field(
        default_factory=list
    )


    def add_child(
        self,
        child: "WidgetModel"
    ) -> None:
        """
        Add a child widget.
        """

        child.parent_id = self.metadata.widget_id

        self.children.append(child)



    def add_signal(
        self,
        signal: SignalModel
    ) -> None:
        """
        Register a UI event.
        """

        self.signals.append(signal)



    def add_slot(
        self,
        slot: SlotModel
    ) -> None:
        """
        Register a callable action.
        """

        self.slots.append(slot)



    @property
    def id(self) -> WidgetID:
        return self.metadata.widget_id



    @property
    def name(self) -> str:
        return self.metadata.name



# ============================================================
# Specialized Widget Models
# ============================================================


@dataclass
class ButtonModel(WidgetModel):
    """
    Push button representation.

    Example:

        MyLauncher:
            New Project
            Open Project
            Exit
    """

    action_name: Optional[str] = None



@dataclass
class LabelModel(WidgetModel):
    """
    Text label representation.
    """

    text: str = ""



@dataclass
class ImageDisplayModel(WidgetModel):
    """
    Image display component.

    Used heavily by:

        MyServer
        MyPixler
        OCR preprocessing tools
    """

    image_source: Optional[str] = None

    supports_zoom: bool = False

    supports_pan: bool = False



@dataclass
class SliderModel(WidgetModel):
    """
    Slider control representation.
    """

    minimum: float = 0

    maximum: float = 100

    value: float = 0



@dataclass
class PanelModel(WidgetModel):
    """
    Container panel.

    Examples:

        MyLauncher left module panel

        MyServer image controls panel
    """

    orientation: str = "vertical"



@dataclass
class MenuModel(WidgetModel):
    """
    Application menu representation.
    """

    actions: List[str] = field(
        default_factory=list
    )



@dataclass
class ToolbarModel(WidgetModel):
    """
    Toolbar representation.
    """

    tools: List[str] = field(
        default_factory=list
    )



@dataclass
class DialogModel(WidgetModel):
    """
    Dialog representation.

    Used for:

        - New Project dialogs
        - Provenance dialogs
        - Settings dialogs
    """

    modal: bool = True



# ============================================================
# Module Representation
# ============================================================


@dataclass
class ModuleAction:
    """
    Represents an executable module action.

    Example:

        Module:
            MyScanner

        Action:
            Acquire Image
    """

    name: str

    description: str = ""

    command: Optional[str] = None



@dataclass
class ModuleModel:
    """
    Represents a BiblionOCR application module.

    Example:

        MyServer
            |
            +-- Load Image
            +-- Preview
            +-- Run OCR


    Modules are intentionally independent from
    Python import mechanics.
    """

    module_id: ModuleID

    name: str

    description: str = ""

    state: ModuleState = ModuleState.UNKNOWN


    root_widget: Optional[WidgetModel] = None


    actions: List[ModuleAction] = field(
        default_factory=list
    )


    tags: List[str] = field(
        default_factory=list
    )



    def add_action(
        self,
        action: ModuleAction
    ) -> None:
        """
        Register a module capability.
        """

        self.actions.append(action)



# ============================================================
# Tutorial and Animation Models
# ============================================================


@dataclass
class TutorialStepModel:
    """
    A single instructional step.

    Example:

        "Click MyScanner"

        Highlight:
            scanner_button
    """

    title: str

    description: str

    target_widget: Optional[WidgetID] = None

    duration_seconds: float = 3.0



@dataclass
class AnimationFrame:
    """
    Represents one animation state.

    Useful for:

        - MyLauncher button cycling
        - module demonstrations
        - tutorials
    """

    target_widget: WidgetID

    action: str

    duration_seconds: float = 1.0



@dataclass
class AnimationSequenceModel:
    """
    Ordered UI animation sequence.

    Example:

        MyLauncher:

            MyServer
              |
            MyPixler
              |
            MyScanner


    Each button can animate while the
    help panel changes content.
    """

    name: str

    frames: List[AnimationFrame] = field(
        default_factory=list
    )



    def add_frame(
        self,
        frame: AnimationFrame
    ) -> None:

        self.frames.append(frame)
        
   # ============================================================
# UIModel - Master UI Representation
# ============================================================


@dataclass
class UIModel:
    """
    Master representation of an application UI.

    This is the central object passed between:

        ui_parser.py
              |
              v
           UIModel
              |
       +------+------+ 
       |             |
       v             v
 tutorial_generator  cytoscape_generator


    The model contains no Qt dependencies.
    """

    name: str

    version: str = "1.0"


    description: str = ""


    root_widget: Optional[WidgetModel] = None


    widgets: Dict[WidgetID, WidgetModel] = field(
        default_factory=dict
    )


    modules: Dict[ModuleID, ModuleModel] = field(
        default_factory=dict
    )


    connections: List[ConnectionModel] = field(
        default_factory=list
    )



    # --------------------------------------------------------
    # Widget Management
    # --------------------------------------------------------


    def add_widget(
        self,
        widget: WidgetModel
    ) -> None:
        """
        Register a widget.
        """

        self.widgets[
            widget.id
        ] = widget



    def remove_widget(
        self,
        widget_id: WidgetID
    ) -> None:
        """
        Remove widget from registry.
        """

        if widget_id in self.widgets:

            del self.widgets[widget_id]



    def find_widget(
        self,
        widget_id: WidgetID
    ) -> Optional[WidgetModel]:
        """
        Retrieve widget by ID.
        """

        return self.widgets.get(widget_id)



    # --------------------------------------------------------
    # Module Management
    # --------------------------------------------------------


    def add_module(
        self,
        module: ModuleModel
    ) -> None:
        """
        Register application module.
        """

        self.modules[
            module.module_id
        ] = module



    def find_module(
        self,
        module_id: ModuleID
    ) -> Optional[ModuleModel]:

        return self.modules.get(module_id)



    # --------------------------------------------------------
    # Connection Management
    # --------------------------------------------------------


    def add_connection(
        self,
        connection: ConnectionModel
    ) -> None:
        """
        Register widget signal connection.
        """

        self.connections.append(
            connection
        )



    # --------------------------------------------------------
    # Tree Generation
    # --------------------------------------------------------


    def generate_tree(
        self,
        widget: Optional[WidgetModel] = None,
        depth: int = 0
    ) -> List[str]:
        """
        Produce a human-readable widget tree.

        Example:

            MyLauncher
              |
              +-- ModulePanel
                    |
                    +-- MyServerButton

        """

        if widget is None:

            widget = self.root_widget


        if widget is None:

            return []



        output = []

        prefix = "    " * depth


        output.append(
            f"{prefix}{widget.name}"
        )


        for child in widget.children:

            output.extend(
                self.generate_tree(
                    child,
                    depth + 1
                )
            )


        return output



    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------


    def validate(self) -> List[str]:
        """
        Validate model integrity.

        Returns:

            []

        when valid.

        """

        errors = []


        # Duplicate IDs are impossible in dictionary,
        # but empty IDs indicate parser problems.

        for widget_id, widget in self.widgets.items():

            if not widget_id:

                errors.append(
                    "Widget contains empty ID"
                )


            if widget.metadata.name == "":

                errors.append(
                    f"Widget {widget_id} has no name"
                )



        # Check parent references

        for widget in self.widgets.values():

            if widget.parent_id:

                if widget.parent_id not in self.widgets:

                    errors.append(
                        f"{widget.id} references missing parent "
                        f"{widget.parent_id}"
                    )



        # Check connections

        for connection in self.connections:

            if connection.source_id not in self.widgets:

                errors.append(
                    f"Missing connection source: "
                    f"{connection.source_id}"
                )


            if connection.destination_id not in self.widgets:

                errors.append(
                    f"Missing connection destination: "
                    f"{connection.destination_id}"
                )



        return errors



    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------


    def to_dict(self) -> Dict[str, Any]:
        """
        Convert UIModel into JSON-safe structure.
        """

        return enum_to_value(
            asdict(self)
        )



    def save_json(
        self,
        filename: str
    ) -> None:
        """
        Save UI model.

        Intended for:

            - documentation cache
            - parser output
            - tutorial generation
        """

        import json


        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.to_dict(),
                file,
                indent=4
            )



    # --------------------------------------------------------
    # Graph Export
    # --------------------------------------------------------


    def export_graph(self) -> Dict[str, List[Dict]]:
        """
        Export graph-compatible representation.

        Designed for:

            - Cytoscape
            - Network visualization
            - Dependency maps

        """

        nodes = []

        edges = []



        for widget in self.widgets.values():

            nodes.append(
                {
                    "id": widget.id,
                    "label": widget.name,
                    "type":
                        widget.metadata.element_type.name
                }
            )



        for connection in self.connections:

            edges.append(
                {
                    "source":
                        connection.source_id,

                    "target":
                        connection.destination_id,

                    "type":
                        connection.connection_type.name
                }
            )



        return {
            "nodes": nodes,
            "edges": edges
        }



# ============================================================
# Convenience Constructors
# ============================================================


def create_widget_metadata(
    widget_id: str,
    name: str,
    element_type: UIElementType,
    **kwargs
) -> WidgetMetadata:
    """
    Convenience factory.

    Example:

        create_widget_metadata(
            "btn_server",
            "MyServer",
            UIElementType.BUTTON
        )
    """

    return WidgetMetadata(
        widget_id=widget_id,
        name=name,
        element_type=element_type,
        **kwargs
    )        