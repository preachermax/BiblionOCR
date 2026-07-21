"""
Cytoscape graph exporter.

Converts BiblionOCR launch graph + UI metadata
into Cytoscape.js element JSON.

Publisher owns the visualization export.
UI Model remains the source of presentation metadata.
"""

import json


class CytoscapeExporter:

    def __init__(self, launch_graph, ui_model=None):
        self.launch_graph = launch_graph
        self.ui_model = ui_model


    def export_elements(self):

        elements = []

        # Nodes
        for node in self.launch_graph.get_nodes():

            node_id = self._node_id(node)
            node_label = self._node_label(node)
            node_script = self._node_script(node)

            metadata = self._get_ui_metadata(node_id)

            elements.append(
                {
                    "data":
                    {
                        "id": node_id,
                        "label": node_label,

                        # UI Model supplied values
                        "order": metadata.get(
                            "order",
                            999
                        ),

                        "help": metadata.get(
                            "help",
                            ""
                        ),

                        "animation": metadata.get(
                            "animation",
                            "idle"
                        ),

                        "script": node_script
                    }
                }
            )


        # Edges
        for edge in self.launch_graph.get_edges():

            elements.append(
                {
                    "data":
                    {
                        "source": edge["source"],
                        "target": edge["target"]
                    }
                }
            )


        return elements

    def export_payload(self):
        """Return a versioned payload for downstream consumers."""

        nodes = []
        edges = []

        for element in self.export_elements():
            data = element.get("data", {})
            if "id" in data:
                nodes.append(data)
            elif "source" in data and "target" in data:
                edges.append(data)

        return {
            "schema_version": 1,
            "generated_from": "launch_graph.py",
            "nodes": nodes,
            "edges": edges,
        }


    def export_json(self, filename):

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.export_payload(),
                file,
                indent=4
            )


    def _get_ui_metadata(self, module_name):

        """
        UI Model remains authoritative.

        This intentionally does not pull
        presentation information from the graph.
        """

        if self.ui_model is None:
            return {}

        if not hasattr(self.ui_model, "get_module_metadata"):
            return {}


        return self.ui_model.get_module_metadata(
            module_name
        )

    def _node_id(self, node):
        if hasattr(node, "interface_id"):
            return node.interface_id
        return node.name

    def _node_label(self, node):
        if hasattr(node, "display_name"):
            return node.display_name
        return node.name

    def _node_script(self, node):
        if hasattr(node, "script"):
            return node.script
        module_scripts = getattr(self.launch_graph, "module_scripts", {})
        return module_scripts.get(self._node_id(node), "")