"""Registry-backed launcher integration for MyLauncher.

This module keeps launch routing logic separate from Qt widgets so it can be
integration-tested without booting a GUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from Developer.Publisher.application_ui_model import (
    ApplicationModule,
    ApplicationUIModel,
    InterfaceReference,
    InterfaceType,
    LaunchMode,
    NavigationRelationship,
)


@dataclass
class LauncherRegistry:
    """Registry mapping launcher modules to executable scripts."""

    application_model: ApplicationUIModel
    launcher_interface_id: str = "MyLauncher"
    module_scripts: Dict[str, str] = field(default_factory=dict)
    module_metadata: Dict[str, Dict[str, object]] = field(default_factory=dict)

    def resolve_script(self, module_id: str) -> Optional[str]:
        """Return the script filename if module is a registered launch target."""

        launch_targets = set(self.application_model.launches(self.launcher_interface_id))
        if module_id not in launch_targets:
            return None
        return self.module_scripts.get(module_id)

    def help_panel_text(self, module_id: str) -> str:
        """Return contextual launcher text for the right help panel."""

        interface = self.application_model.get_interface(module_id)
        script_name = self.module_scripts.get(module_id, "(unmapped)")
        display_name = interface.display_name if interface else module_id
        description = interface.description if interface else "No description available."

        return (
            f"Launcher target: {display_name}\n"
            f"Route: {self.launcher_interface_id} -> {module_id}\n"
            f"Script: {script_name}\n\n"
            f"{description}"
        )


class LauncherIntegrationController:
    """Coordinates launch dispatch and help-panel swap for MyLauncher."""

    def __init__(
        self,
        registry: LauncherRegistry,
        launch_callback: Callable[[str], None],
        help_panel_callback: Callable[[str], None],
    ) -> None:
        self.registry = registry
        self.launch_callback = launch_callback
        self.help_panel_callback = help_panel_callback

    def launch_module(self, module_id: str) -> bool:
        """Update help panel then dispatch launch for a registered module."""

        script_name = self.registry.resolve_script(module_id)
        if not script_name:
            return False

        self.help_panel_callback(self.registry.help_panel_text(module_id))
        self.launch_callback(script_name)
        return True


def build_default_launcher_registry() -> LauncherRegistry:
    """Build minimal ApplicationUIModel wiring for launcher integration."""

    app_model = ApplicationUIModel.create_empty(name="BiblionOCR")

    launcher_interface = InterfaceReference(
        interface_id="MyLauncher",
        display_name="MyLauncher",
        ui_filename="MyLauncherUI.ui",
        interface_type=InterfaceType.LAUNCHER,
        description="Primary module launcher dashboard.",
        launch_mode=LaunchMode.NON_MODAL,
    )
    server_interface = InterfaceReference(
        interface_id="MyServer",
        display_name="MyServer",
        ui_filename="MyServerUI.ui",
        interface_type=InterfaceType.MODULE,
        description="OCR processing server and workflow coordinator.",
        launch_mode=LaunchMode.CHILD_PROCESS,
    )
    scanner_interface = InterfaceReference(
        interface_id="MyScanner",
        display_name="MyScanner",
        ui_filename="MyScannerUI.ui",
        interface_type=InterfaceType.MODULE,
        description="Document scanner and acquisition workflow module.",
        launch_mode=LaunchMode.CHILD_PROCESS,
    )
    pixler_interface = InterfaceReference(
        interface_id="MyPixler",
        display_name="MyPixler",
        ui_filename="MyPixlerUI.ui",
        interface_type=InterfaceType.MODULE,
        description="Image cleanup and pixel-level editing module.",
        launch_mode=LaunchMode.CHILD_PROCESS,
    )
    explorer_interface = InterfaceReference(
        interface_id="MyExplorer",
        display_name="MyExplorer",
        ui_filename="MyExplorerUI.ui",
        interface_type=InterfaceType.MODULE,
        description="Project browsing and file exploration module.",
        launch_mode=LaunchMode.CHILD_PROCESS,
    )

    app_model.add_interface(launcher_interface)
    app_model.add_interface(server_interface)
    app_model.add_interface(scanner_interface)
    app_model.add_interface(pixler_interface)
    app_model.add_interface(explorer_interface)

    app_model.add_module(
        ApplicationModule(
            module_id="MyServer",
            display_name="MyServer",
            description="OCR processing server and workflow coordinator.",
            interface=server_interface,
        )
    )
    app_model.add_module(
        ApplicationModule(
            module_id="MyScanner",
            display_name="MyScanner",
            description="Document scanner and acquisition workflow module.",
            interface=scanner_interface,
        )
    )
    app_model.add_module(
        ApplicationModule(
            module_id="MyPixler",
            display_name="MyPixler",
            description="Image cleanup and pixel-level editing module.",
            interface=pixler_interface,
        )
    )
    app_model.add_module(
        ApplicationModule(
            module_id="MyExplorer",
            display_name="MyExplorer",
            description="Project browsing and file exploration module.",
            interface=explorer_interface,
        )
    )

    app_model.add_navigation(
        source="MyLauncher",
        destination="MyServer",
        relationship=NavigationRelationship.LAUNCHES,
        description="MyLauncher opens MyServer as the primary workflow entry.",
    )
    app_model.add_navigation(
        source="MyLauncher",
        destination="MyScanner",
        relationship=NavigationRelationship.LAUNCHES,
        description="MyLauncher opens MyScanner for document acquisition.",
    )
    app_model.add_navigation(
        source="MyLauncher",
        destination="MyPixler",
        relationship=NavigationRelationship.LAUNCHES,
        description="MyLauncher opens MyPixler for image cleanup/editing.",
    )
    app_model.add_navigation(
        source="MyLauncher",
        destination="MyExplorer",
        relationship=NavigationRelationship.LAUNCHES,
        description="MyLauncher opens MyExplorer for project browsing.",
    )

    return LauncherRegistry(
        application_model=app_model,
        launcher_interface_id="MyLauncher",
        module_scripts={
            "MyServer": "MyServer.py",
            "MyScanner": "MyScanner.py",
            "MyPixler": "MyPixler.py",
            "MyExplorer": "MyExplorer.py",
        },
        module_metadata={
            "MyLauncher": {
                "order": 0,
                "help": "HelpSystem:MyLauncher",
                "animation": "idle",
            },
            "MyServer": {
                "order": 1,
                "help": "HelpSystem:MyServer",
                "animation": "pulse",
            },
            "MyScanner": {
                "order": 2,
                "help": "HelpSystem:MyScanner",
                "animation": "pulse",
            },
            "MyPixler": {
                "order": 3,
                "help": "HelpSystem:MyPixler",
                "animation": "pulse",
            },
            "MyExplorer": {
                "order": 4,
                "help": "HelpSystem:MyExplorer",
                "animation": "pulse",
            },
        },
    )
