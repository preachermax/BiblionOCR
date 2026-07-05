import { useEffect, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";

const overviewSequence = [
  "biblion",
  "vision",
  "architecture",
  "development",
  "publications"
];

const overviewSequenceEdges = ["e1", "e2", "e3", "e4"];

const overviewNodes = [
  {
    data: {
      id: "biblion",
      label: "Biblion",
      category: "Platform",
      summary: "Digital Humanities platform centered on preservation, scholarship, and responsible AI."
    }
  },
  {
    data: {
      id: "vision",
      label: "Vision",
      category: "Document",
      summary: "Defines the long-term purpose and intellectual direction of the project."
    }
  },
  {
    data: {
      id: "architecture",
      label: "Architecture",
      category: "Document",
      summary: "Describes the system structure, module boundaries, and implementation shape."
    }
  },
  {
    data: {
      id: "development",
      label: "Development",
      category: "Workflow",
      summary: "Tracks active engineering notes, procedures, and ongoing implementation work."
    }
  },
  {
    data: {
      id: "publications",
      label: "Publications",
      category: "Outcome",
      summary: "Represents the scholarly outputs the platform is intended to support."
    }
  }
];

const overviewEdges = [
  { data: { id: "e1", source: "biblion", target: "vision" } },
  { data: { id: "e2", source: "vision", target: "architecture" } },
  { data: { id: "e3", source: "architecture", target: "development" } },
  { data: { id: "e4", source: "development", target: "publications" } }
];

const principlesNodes = [
  { data: { id: "principles", label: "Guiding Principles" } },
  {
    data: {
      id: "preservation",
      label: "Preservation Before Convenience"
    }
  },
  {
    data: {
      id: "scholarship",
      label: "Scholarship Before Automation"
    }
  },
  {
    data: {
      id: "documentation",
      label: "Guiding Principles",
      category: "Vision",
      summary: "Core commitments that govern how Biblion applies technology to historical materials."
    }
  },
  {
    data: {
      id: "community",
      label: "Preservation Before Convenience",
      category: "Principle",
      summary: "Source material should remain recoverable, traceable, and documented whenever possible."
    }
  },
  {
    data: {
      id: "stewardship",
      label: "Scholarship Before Automation",
      category: "Principle",
      summary: "Automation supports scholarship; human understanding remains central."
    }
  }
];

const principlesEdges = [
      label: "Documentation Before Assumption",
      category: "Principle",
      summary: "Knowledge should not exist only in source code; decisions and context must be recorded."
    data: {
      id: "p1",
      source: "principles",
      target: "preservation"
    }
      label: "Community Before Individual",
      category: "Principle",
      summary: "Meaningful preservation depends on contributions from many disciplines."
  {
    data: {
      id: "p2",
      source: "principles",
      target: "scholarship"
      label: "Stewardship Before Ownership",
      category: "Principle",
      summary: "Historical texts are treated as shared human inheritance, not possessions."
  },
  {
    data: {
      id: "p3",
      source: "principles",
      target: "documentation"
    }
  },
  {
    data: {
      id: "p4",
      source: "principles",
      target: "community"
    }
  },
  {
    data: {
      id: "p5",
      source: "principles",
      target: "stewardship"
    }
  }
];

const principlesElements = [...principlesNodes, ...principlesEdges];

const stylesheet = [
  {
    selector: "node",
    style: {
      "background-color": "#143642",
      shape: "round-rectangle",
      label: "data(label)",
      color: "#f7f3e9",
      "text-valign": "center",
      "text-halign": "center",
      "text-wrap": "wrap",
      "text-max-width": 138,
      "font-size": "10px",
      width: 156,
      height: 84,
      "border-width": 2,
      "border-color": "#cda15c"
    }
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": "#9cafb7",
      "target-arrow-color": "#9cafb7",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier"
    }
  },
  {
    selector: ".sequence-active",
    style: {
      "background-color": "#cda15c",
      color: "#143642",
      "border-color": "#7d5a22",
      "border-width": 4
    }
  },
  {
    selector: ".sequence-edge",
    style: {
      width: 4,
      "line-color": "#cda15c",
      "target-arrow-color": "#cda15c"
    }
  }
];

const layout = {
  name: "breadthfirst",
  directed: true,
  padding: 24,
  spacingFactor: 1.2
};

const circleLayout = {
  name: "concentric",
  minNodeSpacing: 24,
  padding: 28,
  spacingFactor: 1.1,
  concentric(node) {
    return node.id() === "principles" ? 3 : 1;
  },
  levelWidth() {
    return 1;
  }
};

function GraphCard({ title, description, elements, layoutConfig, onNodeSelect }) {
  const [cy, setCy] = useState(null);

  useEffect(() => {
    if (!cy || !onNodeSelect) {
      return undefined;
    }

    const handleNodeTap = (event) => {
      onNodeSelect({
        graphTitle: title,
        ...event.target.data()
      });
    };

    cy.on("tap", "node", handleNodeTap);

    return () => {
      cy.off("tap", "node", handleNodeTap);
    };
  }, [cy, onNodeSelect, title]);

  return (
    <article className="graph-card">
      <header className="graph-card-header">
        <p className="eyebrow">Static Graph View</p>
        <h2>{title}</h2>
        <p>{description}</p>
      </header>

      <div className="graph-canvas" aria-label={title}>
        <CytoscapeComponent
          cy={setCy}
          elements={elements}
          stylesheet={stylesheet}
          layout={layoutConfig}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </article>
  );
}

export default function App() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [sequenceStep, setSequenceStep] = useState(0);

  const highlightedNodeIds = new Set(overviewSequence.slice(0, sequenceStep + 1));
  const highlightedEdgeIds = new Set(overviewSequenceEdges.slice(0, sequenceStep));

  const overviewElements = [
      ...overviewNodes.map((node) => ({
        ...node,
        classes: highlightedNodeIds.has(node.data.id) ? "sequence-active" : ""
      })),
      ...overviewEdges.map((edge) => ({
        ...edge,
        classes: highlightedEdgeIds.has(edge.data.id) ? "sequence-edge" : ""
      }))
    ];

    const handleAdvanceSequence = () => {
      setSequenceStep((currentStep) => (currentStep + 1) % overviewSequence.length);
    };

    const handleResetSequence = () => {
      setSequenceStep(0);
    };

    const handleToggleAutoplay = () => {
      setIsAutoplaying((currentValue) => !currentValue);
    };

    return (
      <main className="page-shell">
        <section className="intro-panel">
          <p className="eyebrow">Biblion Website Prototype</p>
          <h1>Minimal Cytoscape Graph</h1>
          <p>
            Static React example using predefined node and edge arrays. Node
            clicks promote the selected node data into parent state.
          </p>

          <div className="sequence-controls">
            <button className="sequence-button" type="button" onClick={handleAdvanceSequence}>
              Advance Overview Sequence
            </button>
            <button
              className="sequence-button sequence-button-secondary"
              type="button"
              onClick={handleResetSequence}
            >
              Reset Sequence
            </button>
            <button
              className={`sequence-button ${isAutoplaying ? "sequence-button-active" : ""}`}
              type="button"
              onClick={handleToggleAutoplay}
            >
              {isAutoplaying ? "Stop Autoplay" : "Start Autoplay"}
            </button>
          </div>

          <p className="sequence-status">
            Autoplay is {isAutoplaying ? "running" : "stopped"} at {autoplayIntervalMs} ms per step.
          </p>

          <section className="selected-node-panel" aria-label="Selected node details">
            <p className="eyebrow">Selected Node</p>
            {selectedNode ? (
              <>
                <h2>{selectedNode.label}</h2>
                <p className="selected-node-meta">
                  {selectedNode.graphTitle} · {selectedNode.category}
                </p>
                <p>{selectedNode.summary}</p>
              </>
            ) : (
              <p>Click a node to inspect its data in parent state.</p>
            )}
          </section>
        </section>

        <section className="graph-panel" aria-label="Biblion graph previews">
          <GraphCard
            title="Biblion Overview"
            description={`A minimal relationship map for the current documentation-facing website prototype. Sequence step ${sequenceStep + 1} of ${overviewSequence.length}.`}
            elements={overviewElements}
            layoutConfig={layout}
            onNodeSelect={setSelectedNode}
          />

          <GraphCard
            title="Guiding Principles"
            description="A static graph derived from the principles outlined in THE_BIBLION_PROJECT.md."
            elements={principlesElements}
            layoutConfig={circleLayout}
            onNodeSelect={setSelectedNode}
          />
        </section>
      </main>
    );
  }
      ...node,
      classes: highlightedNodeIds.has(node.data.id) ? "sequence-active" : ""
    })),
    ...overviewEdges.map((edge) => ({
      ...edge,
      classes: highlightedEdgeIds.has(edge.data.id) ? "sequence-edge" : ""
    }))
  ];

  const handleAdvanceSequence = () => {
    setSequenceStep((currentStep) => (currentStep + 1) % overviewSequence.length);
  };

  const handleResetSequence = () => {
    setSequenceStep(0);
  };

  return (
    <main className="page-shell">
      <section className="intro-panel">
        <p className="eyebrow">Biblion Website Prototype</p>
        <h1>Minimal Cytoscape Graph</h1>
        <p>
          Static React example using predefined node and edge arrays. Node
          clicks now promote the selected node data into parent state.
        </p>

        <div className="sequence-controls">
          <button className="sequence-button" type="button" onClick={handleAdvanceSequence}>
            Advance Overview Sequence
          </button>
          <button
            className="sequence-button sequence-button-secondary"
            type="button"
            onClick={handleResetSequence}
          >
            Reset Sequence
          </button>
        </div>

        <section className="selected-node-panel" aria-label="Selected node details">
          <p className="eyebrow">Selected Node</p>
          {selectedNode ? (
            <>
              <h2>{selectedNode.label}</h2>
              <p className="selected-node-meta">{selectedNode.graphTitle} · {selectedNode.category}</p>
              <p>{selectedNode.summary}</p>
            </>
          ) : (
            <p>Click a node to inspect its data in parent state.</p>
          )}
        </section>
      </section>

      <section className="graph-panel" aria-label="Biblion graph previews">
        <GraphCard
          title="Biblion Overview"
          description={`A minimal relationship map for the current documentation-facing website prototype. Sequence step ${sequenceStep + 1} of ${overviewSequence.length}.`}
          elements={overviewElements}
          layoutConfig={layout}
          onNodeSelect={setSelectedNode}
        />

        <GraphCard
          title="Guiding Principles"
          description="A static graph derived from the principles outlined in THE_BIBLION_PROJECT.md."
          elements={principlesElements}
          layoutConfig={circleLayout}
          onNodeSelect={setSelectedNode}
        />
      </section>
    </main>
  );
}