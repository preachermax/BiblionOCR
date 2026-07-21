from __future__ import annotations

import json
import os
import tempfile
import unittest

from Developer.Publisher.Cytoscape.cytoscape_exporter import CytoscapeExporter
from Developer.Publisher.launch_graph import LaunchGraph
from Developer.Publisher.launcher_registry import build_default_launcher_registry


class CytoscapeExporterTests(unittest.TestCase):
    def _build_exporter(self) -> CytoscapeExporter:
        registry = build_default_launcher_registry()
        launch_graph = LaunchGraph(
            application_model=registry.application_model,
            launcher_interface_id=registry.launcher_interface_id,
            module_scripts=registry.module_scripts,
        )
        return CytoscapeExporter(launch_graph)

    def test_export_elements_contains_expected_nodes_and_edges(self) -> None:
        exporter = self._build_exporter()

        elements = exporter.export_elements()

        node_elements = [e for e in elements if "id" in e["data"]]
        edge_elements = [e for e in elements if "source" in e["data"]]

        node_ids = {e["data"]["id"] for e in node_elements}
        edge_pairs = {(e["data"]["source"], e["data"]["target"]) for e in edge_elements}

        self.assertEqual({"MyServer", "MyScanner", "MyPixler", "MyExplorer"}, node_ids)
        self.assertEqual(
            {
                ("MyLauncher", "MyServer"),
                ("MyLauncher", "MyScanner"),
                ("MyLauncher", "MyPixler"),
                ("MyLauncher", "MyExplorer"),
            },
            edge_pairs,
        )

        script_by_node = {
            e["data"]["id"]: e["data"].get("script")
            for e in node_elements
        }
        self.assertEqual("MyServer.py", script_by_node["MyServer"])
        self.assertEqual("MyScanner.py", script_by_node["MyScanner"])
        self.assertEqual("MyPixler.py", script_by_node["MyPixler"])
        self.assertEqual("MyExplorer.py", script_by_node["MyExplorer"])

    def test_export_json_writes_cytoscape_payload(self) -> None:
        exporter = self._build_exporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "launch_graph.json")
            exporter.export_json(output_file)

            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r", encoding="utf-8") as handle:
                payload = json.load(handle)

            self.assertIsInstance(payload, dict)
            self.assertEqual(1, payload.get("schema_version"))
            self.assertEqual("launch_graph.py", payload.get("generated_from"))
            self.assertIsInstance(payload.get("nodes"), list)
            self.assertIsInstance(payload.get("edges"), list)
            self.assertEqual(4, len(payload["nodes"]))
            self.assertEqual(4, len(payload["edges"]))
            self.assertTrue(any("id" in item for item in payload["nodes"]))
            self.assertTrue(any("source" in item for item in payload["edges"]))


if __name__ == "__main__":
    unittest.main()
