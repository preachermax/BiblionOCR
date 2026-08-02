from __future__ import annotations

import os
import sys
import unittest


VIEWCONTROLLER_MAINUI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "ViewController",
    "0-MainUI",
)
if VIEWCONTROLLER_MAINUI_DIR not in sys.path:
    sys.path.insert(0, VIEWCONTROLLER_MAINUI_DIR)

from Developer.Publisher.launcher_registry import (  # noqa: E402
    LauncherIntegrationController,
    build_default_launcher_registry,
)


class LauncherRegistryIntegrationTests(unittest.TestCase):
    def test_myserver_registered_in_application_launch_graph(self) -> None:
        registry = build_default_launcher_registry()

        self.assertIn("MyServer", registry.application_model.launches("MyLauncher"))
        self.assertEqual("MyServer.py", registry.resolve_script("MyServer"))

    def test_myscanner_registered_in_application_launch_graph(self) -> None:
        registry = build_default_launcher_registry()

        self.assertIn("MyScanner", registry.application_model.launches("MyLauncher"))
        self.assertEqual("MyScanner.py", registry.resolve_script("MyScanner"))

    def test_mypixler_registered_in_application_launch_graph(self) -> None:
        registry = build_default_launcher_registry()

        self.assertIn("MyPixler", registry.application_model.launches("MyLauncher"))
        self.assertEqual("MyPixler.py", registry.resolve_script("MyPixler"))

    def test_myexplorer_registered_in_application_launch_graph(self) -> None:
        registry = build_default_launcher_registry()

        self.assertIn("MyExplorer", registry.application_model.launches("MyLauncher"))
        self.assertEqual("MyExplorer.py", registry.resolve_script("MyExplorer"))

    def test_myserver_launch_updates_help_panel_before_dispatch(self) -> None:
        registry = build_default_launcher_registry()
        events = []

        def launch_callback(script_name: str) -> None:
            events.append(("launch", script_name))

        def help_callback(help_text: str) -> None:
            events.append(("help", help_text))

        controller = LauncherIntegrationController(
            registry=registry,
            launch_callback=launch_callback,
            help_panel_callback=help_callback,
        )

        launched = controller.launch_module("MyServer")

        self.assertTrue(launched)
        self.assertEqual(2, len(events))
        self.assertEqual("help", events[0][0])
        self.assertIn("MyLauncher -> MyServer", events[0][1])
        self.assertEqual(("launch", "MyServer.py"), events[1])

    def test_unknown_module_does_not_launch(self) -> None:
        registry = build_default_launcher_registry()
        events = []

        controller = LauncherIntegrationController(
            registry=registry,
            launch_callback=lambda script: events.append(("launch", script)),
            help_panel_callback=lambda text: events.append(("help", text)),
        )

        launched = controller.launch_module("MissingModule")

        self.assertFalse(launched)
        self.assertEqual([], events)

    def test_myscanner_launch_updates_help_panel_before_dispatch(self) -> None:
        registry = build_default_launcher_registry()
        events = []

        def launch_callback(script_name: str) -> None:
            events.append(("launch", script_name))

        def help_callback(help_text: str) -> None:
            events.append(("help", help_text))

        controller = LauncherIntegrationController(
            registry=registry,
            launch_callback=launch_callback,
            help_panel_callback=help_callback,
        )

        launched = controller.launch_module("MyScanner")

        self.assertTrue(launched)
        self.assertEqual(2, len(events))
        self.assertEqual("help", events[0][0])
        self.assertIn("MyLauncher -> MyScanner", events[0][1])
        self.assertEqual(("launch", "MyScanner.py"), events[1])

    def test_mypixler_launch_updates_help_panel_before_dispatch(self) -> None:
        registry = build_default_launcher_registry()
        events = []

        def launch_callback(script_name: str) -> None:
            events.append(("launch", script_name))

        def help_callback(help_text: str) -> None:
            events.append(("help", help_text))

        controller = LauncherIntegrationController(
            registry=registry,
            launch_callback=launch_callback,
            help_panel_callback=help_callback,
        )

        launched = controller.launch_module("MyPixler")

        self.assertTrue(launched)
        self.assertEqual(2, len(events))
        self.assertEqual("help", events[0][0])
        self.assertIn("MyLauncher -> MyPixler", events[0][1])
        self.assertEqual(("launch", "MyPixler.py"), events[1])

    def test_myexplorer_launch_updates_help_panel_before_dispatch(self) -> None:
        registry = build_default_launcher_registry()
        events = []

        def launch_callback(script_name: str) -> None:
            events.append(("launch", script_name))

        def help_callback(help_text: str) -> None:
            events.append(("help", help_text))

        controller = LauncherIntegrationController(
            registry=registry,
            launch_callback=launch_callback,
            help_panel_callback=help_callback,
        )

        launched = controller.launch_module("MyExplorer")

        self.assertTrue(launched)
        self.assertEqual(2, len(events))
        self.assertEqual("help", events[0][0])
        self.assertIn("MyLauncher -> MyExplorer", events[0][1])
        self.assertEqual(("launch", "MyExplorer.py"), events[1])


if __name__ == "__main__":
    unittest.main()
