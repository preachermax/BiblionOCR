"""
application_ui_model.py

Application-level UI orchestration model for BiblionOCR.

Unlike ui_model.py, which represents a single user interface,
this module represents the relationships between every UI in the
application.

Architecture
------------

                ui_model.py
                     │
                     ▼
               Individual UIModel
                     │
     +---------------+---------------+
     |               |               |
     ▼               ▼               ▼
 MyLauncher      MyServer      MyScanner
                     │
                     ▼
          ApplicationUIModel
                     │
     +---------------+---------------+
     |               |               |
     ▼               ▼               ▼
 Tutorial      Documentation    Cytoscape
 Generator        Generator      Generator

The ApplicationUIModel intentionally contains no Qt dependencies.
It describes the logical application rather than any runtime GUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set

from ui_model import (
    UIModel,
    ModuleModel,
    ModuleState,
    WidgetID,
    ModuleID,
    enum_to_value,
)

# ============================================================
# Enumerations
# ============================================================


class InterfaceType(Enum):
    """
    High-level interface categories.
    """

    APPLICATION = auto()
    LAUNCHER = auto()
    MODULE = auto()
    DIALOG = auto()
    TOOL = auto()
    DOCUMENT = auto()
    SETTINGS = auto()
    WIZARD = auto()
    OTHER = auto()


class LaunchMode(Enum):
    """
    How one interface activates another.
    """

    UNKNOWN = auto()
    EMBEDDED = auto()
    MODAL = auto()
    NON_MODAL = auto()
    CHILD_PROCESS = auto()
    EXTERNAL = auto()


class NavigationRelationship(Enum):
    """
    Logical navigation relationships.
    """

    NONE = auto()

    LAUNCHES = auto()

    RETURNS_TO = auto()

    DEPENDS_ON = auto()

    MONITORS = auto()

    CONFIGURES = auto()

    DOCUMENTS = auto()

    TUTORIAL = auto()


# ============================================================
# Interface Models
# ============================================================


@dataclass
class InterfaceReference:
    """
    Reference to one UIModel.

    Example:

        MyServer.ui

            ↓

        InterfaceReference
    """

    interface_id: str

    display_name: str

    ui_filename: str

    interface_type: InterfaceType = InterfaceType.MODULE

    description: str = ""

    launch_mode: LaunchMode = LaunchMode.CHILD_PROCESS

    icon: Optional[str] = None

    enabled: bool = True


@dataclass
class NavigationLink:
    """
    Relationship between two interfaces.

    Example:

        MyLauncher
              |
              +------ launches ------+
                                     |
                                     v
                                MyServer
    """

    source: str

    destination: str

    relationship: NavigationRelationship

    description: str = ""


# ============================================================
# Tutorial Models
# ============================================================


@dataclass
class TutorialReference:
    """
    Associates tutorial content with an interface.
    """

    tutorial_id: str

    title: str

    interface_id: str

    markdown_file: Optional[str] = None

    html_file: Optional[str] = None

    narration_file: Optional[str] = None

    duration_seconds: float = 0.0

    tags: List[str] = field(default_factory=list)


# ============================================================
# Documentation Models
# ============================================================


@dataclass
class DocumentationReference:
    """
    Associates documentation with an interface.
    """

    document_id: str

    title: str

    interface_id: str

    filename: str

    description: str = ""

    tags: List[str] = field(default_factory=list)


# ============================================================
# Animation Registry
# ============================================================


@dataclass
class AnimationReference:
    """
    High-level animation description.

    Animation implementations remain in ui_model.py.

    This registry merely associates them with interfaces.
    """

    animation_id: str

    interface_id: str

    sequence_name: str

    description: str = ""


# ============================================================
# Application Module
# ============================================================


@dataclass
class ApplicationModule:
    """
    Represents one BiblionOCR module.

    Example:

        MyScanner

            UI
            Tutorial
            Documentation
            Animations
    """

    module_id: ModuleID

    display_name: str

    description: str = ""

    state: ModuleState = ModuleState.UNKNOWN

    interface: Optional[InterfaceReference] = None

    ui_model: Optional[UIModel] = None

    module_model: Optional[ModuleModel] = None

    tutorials: List[TutorialReference] = field(
        default_factory=list
    )

    documentation: List[DocumentationReference] = field(
        default_factory=list
    )

    animations: List[AnimationReference] = field(
        default_factory=list
    )

    tags: List[str] = field(default_factory=list)

    def add_tutorial(
        self,
        tutorial: TutorialReference
    ) -> None:

        self.tutorials.append(tutorial)

    def add_documentation(
        self,
        document: DocumentationReference
    ) -> None:

        self.documentation.append(document)

    def add_animation(
        self,
        animation: AnimationReference
    ) -> None:

        self.animations.append(animation)


# ============================================================
# ApplicationUIModel
# ============================================================


@dataclass
class ApplicationUIModel:
    """
    Master representation of the entire application's UI.

    Unlike UIModel, which represents one interface,
    ApplicationUIModel understands how every interface
    relates to every other interface.

    It becomes the foundation for:

        • launcher navigation

        • documentation generation

        • tutorial generation

        • Cytoscape graphs

        • dependency analysis

        • future web portal generation
    """

    name: str = "BiblionOCR"

    version: str = "1.0"

    description: str = ""

    interfaces: Dict[str, InterfaceReference] = field(
        default_factory=dict
    )

    ui_models: Dict[str, UIModel] = field(
        default_factory=dict
    )

    modules: Dict[ModuleID, ApplicationModule] = field(
        default_factory=dict
    )

    navigation: List[NavigationLink] = field(
        default_factory=list
    )

    tutorials: Dict[str, TutorialReference] = field(
        default_factory=dict
    )

    documentation: Dict[str, DocumentationReference] = field(
        default_factory=dict
    )

    animations: Dict[str, AnimationReference] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    
        # ========================================================
    # Interface Registration
    # ========================================================

    def add_interface(
        self,
        interface: InterfaceReference,
        ui_model: Optional[UIModel] = None,
    ) -> None:
        """
        Register an application interface.

        Parameters
        ----------
        interface:
            Interface metadata.

        ui_model:
            Parsed UIModel corresponding to the interface.
        """

        self.interfaces[interface.interface_id] = interface

        if ui_model is not None:
            self.ui_models[interface.interface_id] = ui_model

    def remove_interface(
        self,
        interface_id: str,
    ) -> None:
        """
        Remove an interface from the application model.
        """

        self.interfaces.pop(interface_id, None)
        self.ui_models.pop(interface_id, None)

        self.navigation = [
            link
            for link in self.navigation
            if link.source != interface_id
            and link.destination != interface_id
        ]

    def get_interface(
        self,
        interface_id: str,
    ) -> Optional[InterfaceReference]:
        """
        Return an interface by identifier.
        """

        return self.interfaces.get(interface_id)

    def get_ui_model(
        self,
        interface_id: str,
    ) -> Optional[UIModel]:
        """
        Return the parsed UIModel for an interface.
        """

        return self.ui_models.get(interface_id)

    # ========================================================
    # Module Registration
    # ========================================================

    def add_module(
        self,
        module: ApplicationModule,
    ) -> None:
        """
        Register an application module.
        """

        self.modules[module.module_id] = module

    def remove_module(
        self,
        module_id: ModuleID,
    ) -> None:
        """
        Remove a module.
        """

        self.modules.pop(module_id, None)

    def get_module(
        self,
        module_id: ModuleID,
    ) -> Optional[ApplicationModule]:
        """
        Lookup a module.
        """

        return self.modules.get(module_id)

    def find_module_by_name(
        self,
        display_name: str,
    ) -> Optional[ApplicationModule]:

        for module in self.modules.values():

            if module.display_name == display_name:
                return module

        return None

    # ========================================================
    # Navigation Graph
    # ========================================================

    def add_navigation(
        self,
        source: str,
        destination: str,
        relationship: NavigationRelationship,
        description: str = "",
    ) -> NavigationLink:
        """
        Create a navigation relationship.
        """

        link = NavigationLink(
            source=source,
            destination=destination,
            relationship=relationship,
            description=description,
        )

        self.navigation.append(link)

        return link

    def remove_navigation(
        self,
        source: str,
        destination: str,
    ) -> None:

        self.navigation = [
            link
            for link in self.navigation
            if not (
                link.source == source
                and link.destination == destination
            )
        ]

    def outgoing_navigation(
        self,
        interface_id: str,
    ) -> List[NavigationLink]:

        return [
            link
            for link in self.navigation
            if link.source == interface_id
        ]

    def incoming_navigation(
        self,
        interface_id: str,
    ) -> List[NavigationLink]:

        return [
            link
            for link in self.navigation
            if link.destination == interface_id
        ]

    def launches(
        self,
        interface_id: str,
    ) -> List[str]:
        """
        Return every interface launched from
        the specified interface.
        """

        launched = []

        for link in self.navigation:

            if (
                link.source == interface_id
                and link.relationship
                == NavigationRelationship.LAUNCHES
            ):
                launched.append(link.destination)

        return launched

    # ========================================================
    # Tutorial Registry
    # ========================================================

    def register_tutorial(
        self,
        tutorial: TutorialReference,
    ) -> None:

        self.tutorials[tutorial.tutorial_id] = tutorial

        interface = self.interfaces.get(
            tutorial.interface_id
        )

        if interface is None:
            return

        for module in self.modules.values():

            if (
                module.interface
                and module.interface.interface_id
                == tutorial.interface_id
            ):
                module.add_tutorial(tutorial)
                break

    def tutorial(
        self,
        tutorial_id: str,
    ) -> Optional[TutorialReference]:

        return self.tutorials.get(tutorial_id)

    def tutorials_for_interface(
        self,
        interface_id: str,
    ) -> List[TutorialReference]:

        return [
            tutorial
            for tutorial in self.tutorials.values()
            if tutorial.interface_id == interface_id
        ]

    # ========================================================
    # Documentation Registry
    # ========================================================

    def register_documentation(
        self,
        document: DocumentationReference,
    ) -> None:

        self.documentation[
            document.document_id
        ] = document

        for module in self.modules.values():

            if (
                module.interface
                and module.interface.interface_id
                == document.interface_id
            ):
                module.add_documentation(document)
                break

    def documentation_for_interface(
        self,
        interface_id: str,
    ) -> List[DocumentationReference]:

        return [
            doc
            for doc in self.documentation.values()
            if doc.interface_id == interface_id
        ]

    # ========================================================
    # Animation Registry
    # ========================================================

    def register_animation(
        self,
        animation: AnimationReference,
    ) -> None:

        self.animations[
            animation.animation_id
        ] = animation

        for module in self.modules.values():

            if (
                module.interface
                and module.interface.interface_id
                == animation.interface_id
            ):
                module.add_animation(animation)
                break

    def animations_for_interface(
        self,
        interface_id: str,
    ) -> List[AnimationReference]:

        return [
            animation
            for animation in self.animations.values()
            if animation.interface_id == interface_id
        ]

    # ========================================================
    # Lookup Helpers
    # ========================================================

    def has_interface(
        self,
        interface_id: str,
    ) -> bool:

        return interface_id in self.interfaces

    def has_module(
        self,
        module_id: ModuleID,
    ) -> bool:

        return module_id in self.modules

    def interface_ids(self) -> List[str]:

        return sorted(self.interfaces.keys())

    def module_ids(self) -> List[ModuleID]:

        return sorted(self.modules.keys())

    def module_names(self) -> List[str]:

        return sorted(
            module.display_name
            for module in self.modules.values()
        )

    def interface_count(self) -> int:

        return len(self.interfaces)

    def module_count(self) -> int:

        return len(self.modules)
    
        # ========================================================
    # Graph Construction
    # ========================================================

    def dependency_graph(self) -> Dict[str, List[str]]:
        """
        Return the application dependency graph.

        Returns
        -------
        dict
            {
                interface_id: [dependent_interface_ids]
            }
        """

        graph: Dict[str, List[str]] = {}

        for interface_id in self.interfaces:
            graph[interface_id] = []

        for link in self.navigation:

            if (
                link.relationship
                == NavigationRelationship.DEPENDS_ON
            ):
                graph.setdefault(link.source, []).append(
                    link.destination
                )

        return graph

    def launch_graph(self) -> Dict[str, List[str]]:
        """
        Return the launcher graph.
        """

        graph: Dict[str, List[str]] = {}

        for interface_id in self.interfaces:
            graph[interface_id] = []

        for link in self.navigation:

            if (
                link.relationship
                == NavigationRelationship.LAUNCHES
            ):
                graph.setdefault(link.source, []).append(
                    link.destination
                )

        return graph

    # ========================================================
    # Validation
    # ========================================================

    def validate(self) -> List[str]:
        """
        Validate the application model.

        Returns
        -------
        list[str]
            Collection of validation errors.
        """

        errors: List[str] = []

        #
        # Interfaces referenced by navigation.
        #

        for link in self.navigation:

            if link.source not in self.interfaces:
                errors.append(
                    f"Unknown source interface: "
                    f"{link.source}"
                )

            if link.destination not in self.interfaces:
                errors.append(
                    f"Unknown destination interface: "
                    f"{link.destination}"
                )

        #
        # Modules reference registered interfaces.
        #

        for module in self.modules.values():

            if module.interface is None:
                continue

            if (
                module.interface.interface_id
                not in self.interfaces
            ):
                errors.append(
                    f"Module "
                    f"{module.display_name} "
                    f"references unknown interface "
                    f"{module.interface.interface_id}"
                )

        return errors

    # ========================================================
    # Serialization
    # ========================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the application model.
        """

        return {

            "name": self.name,

            "version": self.version,

            "description": self.description,

            "interfaces": {
                key: asdict(value)
                for key, value in self.interfaces.items()
            },

            "modules": {
                str(key): asdict(value)
                for key, value in self.modules.items()
            },

            "navigation": [
                asdict(link)
                for link in self.navigation
            ],

            "tutorials": {
                key: asdict(value)
                for key, value in self.tutorials.items()
            },

            "documentation": {
                key: asdict(value)
                for key, value
                in self.documentation.items()
            },

            "animations": {
                key: asdict(value)
                for key, value
                in self.animations.items()
            },

            "metadata": self.metadata,
        }

    def to_json_dict(self) -> Dict[str, Any]:
        """
        Convert to a JSON-safe representation.
        """

        return enum_to_value(self.to_dict())

    # ========================================================
    # Convenience Constructors
    # ========================================================

    @classmethod
    def create_empty(
        cls,
        name: str = "BiblionOCR",
    ) -> "ApplicationUIModel":
        """
        Create an empty application model.
        """

        return cls(
            name=name,
        )

    @classmethod
    def from_ui_models(
        cls,
        ui_models: List[UIModel],
    ) -> "ApplicationUIModel":
        """
        Construct an application model from a
        collection of UIModel instances.
        """

        app = cls()

        for ui in ui_models:

            interface = InterfaceReference(

                interface_id=ui.name,

                display_name=ui.name,

                ui_filename=ui.filename,

                interface_type=InterfaceType.MODULE,
            )

            app.add_interface(
                interface,
                ui,
            )

        return app

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(self) -> Dict[str, int]:
        """
        Return application statistics.
        """

        return {

            "interfaces": len(self.interfaces),

            "modules": len(self.modules),

            "navigation_links": len(self.navigation),

            "tutorials": len(self.tutorials),

            "documentation": len(self.documentation),

            "animations": len(self.animations),
        }

    # ========================================================
    # Representation
    # ========================================================

    def __len__(self) -> int:
        return len(self.interfaces)

    def __contains__(
        self,
        interface_id: str,
    ) -> bool:
        return interface_id in self.interfaces

    def __iter__(self):
        return iter(self.interfaces.values())

    def __repr__(self) -> str:

        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"interfaces={len(self.interfaces)}, "
            f"modules={len(self.modules)})"
        )