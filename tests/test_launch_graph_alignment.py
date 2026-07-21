from __future__ import annotations

import os
import sys
import unittest

from Developer.Publisher.launch_graph import LaunchGraph


VIEWCONTROLLER_MAINUI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "ViewController",
    "0-MainUI",
)
if VIEWCONTROLLER_MAINUI_DIR not in sys.path:
    sys.path.insert(0, VIEWCONTROLLER_MAINUI_DIR)

from Developer.Publisher.launcher_registry import build_default_launcher_registry  # noqa: E402


class LaunchGraphAlignmentTests(unittest.TestCase):
    def test_nodes_are_derived_from_application_ui_metadata(self) -> None:
        registry = build_default_launcher_registry()
        graph = LaunchGraph(
            application_model=registry.application_model,
            module_scripts=registry.module_scripts,
        )

        node_ids = {node.interface_id for node in graph.get_nodes()}
        launch_targets = set(registry.application_model.launches("MyLauncher"))
        expected_nodes = launch_targets.union({"MyLauncher"})

        self.assertEqual(expected_nodes, node_ids)

        explorer_node = next(node for node in graph.get_nodes() if node.interface_id == "MyExplorer")
        self.assertEqual("MyExplorerUI.ui", explorer_node.ui_filename)
        self.assertIn("Project browsing", explorer_node.description)

        launcher_node = next(node for node in graph.get_nodes() if node.interface_id == "MyLauncher")
        self.assertEqual("MyLauncherUI.ui", launcher_node.ui_filename)
        self.assertEqual("NON_MODAL", launcher_node.launch_mode)

    def test_edges_are_derived_from_launch_navigation_links(self) -> None:
        registry = build_default_launcher_registry()
        graph = LaunchGraph(
            application_model=registry.application_model,
            module_scripts=registry.module_scripts,
        )

        edges = graph.get_edges()

        self.assertEqual(4, len(edges))
        for edge in edges:
            self.assertEqual("MyLauncher", edge["source"])
            self.assertIn(edge["target"], registry.application_model.launches("MyLauncher"))
            self.assertEqual(registry.module_scripts[edge["target"]], edge["script"])


if __name__ == "__main__":
    unittest.main()
